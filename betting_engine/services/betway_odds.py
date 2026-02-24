from playwright.sync_api import sync_playwright
from django.conf import settings
from datetime import datetime, timedelta, timezone
import time
import json

from betting_engine.services.scraper_utils import random_sleep, get_user_agent
import os
from concurrent.futures import ThreadPoolExecutor


def _load_leagues():
    """Load leagues from leagues.json. Returns {country: [betway_slugs]} for compatibility."""
    leagues_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "betting_data",
        "leagues.json"
    )
    try:
        with open(leagues_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            country: [item["betway"] for item in leagues]
            for country, leagues in data.items()
        }
    except Exception as e:
        print(f"Error loading leagues: {e}")
        return {}


class BetwayScraper:
    def __init__(self, headless=True):
        self.headless = headless
    
    def convert_to_float(self, value):
        """Convert string to float, return None if invalid"""
        if value is None or value == "" or value == " - ":
            return None
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            return None

    def scrape_game_details(self, page, game_url, game_data):
        """Navigate to individual game page and extract detailed odds"""
        try:
            page.goto(game_url, timeout=60000, wait_until="domcontentloaded")
            random_sleep("nav")
            
            # Wait for markets container
            page.wait_for_selector("div.flex.flex-col.gap-3", timeout=10000)
            random_sleep("medium")
            
            # Initialize all new fields
            game_data['home_win'] = None
            game_data['draw'] = None
            game_data['away_win'] = None
            game_data['home_draw_no_bet'] = None
            game_data['away_draw_no_bet'] = None
            game_data['total_over_1.5'] = None
            game_data['total_under_3.5'] = None
            game_data['BTTS_yes'] = None
            game_data['BTTS_no'] = None
            game_data['home_team_over_0.5'] = None
            game_data['away_team_over_0.5'] = None
            
            # Find all market sections
            market_sections = page.locator("details").all()
            
            for market in market_sections:
                try:
                    # Get market name from summary
                    summary_text = market.locator("summary").inner_text().strip()
                    
                    # 1X2 Market
                    if "1X2" in summary_text:
                        odds_grid = market.locator("div.grid.grid-cols-3").first
                        if odds_grid.count() > 0:
                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                            if len(odds_items) >= 3:
                                # First item is home win - get the last span (odds)
                                home_win_spans = odds_items[0].locator("span").all()
                                if len(home_win_spans) > 0:
                                    game_data['home_win'] = self.convert_to_float(home_win_spans[-1].inner_text().strip())
                                
                                # Second item is draw
                                draw_spans = odds_items[1].locator("span").all()
                                if len(draw_spans) > 0:
                                    game_data['draw'] = self.convert_to_float(draw_spans[-1].inner_text().strip())
                                
                                # Third item is away win
                                away_win_spans = odds_items[2].locator("span").all()
                                if len(away_win_spans) > 0:
                                    game_data['away_win'] = self.convert_to_float(away_win_spans[-1].inner_text().strip())
                    
                    # Draw No Bet Market
                    elif "Draw No Bet" in summary_text:
                        odds_grid = market.locator("div.grid.grid-cols-2").first
                        if odds_grid.count() > 0:
                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                            if len(odds_items) >= 2:
                                # First item is home
                                home_dnb_spans = odds_items[0].locator("span").all()
                                if len(home_dnb_spans) > 0:
                                    game_data['home_draw_no_bet'] = self.convert_to_float(home_dnb_spans[-1].inner_text().strip())
                                
                                # Second item is away
                                away_dnb_spans = odds_items[1].locator("span").all()
                                if len(away_dnb_spans) > 0:
                                    game_data['away_draw_no_bet'] = self.convert_to_float(away_dnb_spans[-1].inner_text().strip())
                    
                    # Total Goals Market
                    elif "Total Goals" in summary_text:
                        odds_grid = market.locator("div.grid.grid-cols-2").first
                        if odds_grid.count() > 0:
                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                            for item in odds_items:
                                # Get the text from the first div (label)
                                label_div = item.locator("div").first
                                if label_div.count() > 0:
                                    item_text = label_div.inner_text().strip()
                                    
                                    # Get odds from the last span
                                    odds_spans = item.locator("span").all()
                                    if len(odds_spans) > 0:
                                        odds_value = self.convert_to_float(odds_spans[-1].inner_text().strip())
                                        
                                        if "Over" in item_text and "(1.5)" in item_text:
                                            game_data['total_over_1.5'] = odds_value
                                        elif "Under" in item_text and "(3.5)" in item_text:
                                            game_data['total_under_3.5'] = odds_value
                    
                    # Both Teams To Score Market
                    elif "Both Teams To Score" in summary_text or "BTTS" in summary_text:
                        odds_grid = market.locator("div.grid.grid-cols-2").first
                        if odds_grid.count() > 0:
                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                            for item in odds_items:
                                # Get the text from the first div (label)
                                label_div = item.locator("div").first
                                if label_div.count() > 0:
                                    item_text = label_div.inner_text().strip()
                                    
                                    # Get odds from the last span
                                    odds_spans = item.locator("span").all()
                                    if len(odds_spans) > 0:
                                        odds_value = self.convert_to_float(odds_spans[-1].inner_text().strip())
                                        
                                        if "Yes" in item_text:
                                            game_data['BTTS_yes'] = odds_value
                                        elif "No" in item_text:
                                            game_data['BTTS_no'] = odds_value
                    
                    # Double Chance Market
                    elif "Double Chance" in summary_text:
                        # Double Chance has 3 options: Home/Draw, Home/Away, Draw/Away
                        odds_grid = market.locator("div.grid.grid-cols-3").first
                        if odds_grid.count() == 0:
                            # Try alternative grid selector
                            odds_grid = market.locator("div.grid.p-1.rounded-b-lg.shadow-sm.bg-light-50.gap-1.dark\\:bg-dark-800.grid-cols-3").first
                        
                        if odds_grid.count() > 0:
                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                            home_team = game_data.get('home_team', '').lower()
                            away_team = game_data.get('away_team', '').lower()
                            
                            for item in odds_items:
                                # Get the text from the first div (label)
                                label_div = item.locator("div").first
                                if label_div.count() > 0:
                                    item_text = label_div.inner_text().strip()
                                    item_text_lower = item_text.lower()
                                    
                                    # Get odds from span
                                    odds_spans = item.locator("span").all()
                                    if len(odds_spans) > 0:
                                        odds_value = self.convert_to_float(odds_spans[-1].inner_text().strip())
                                        
                                        # Identify which double chance option this is based on text
                                        # Format examples:
                                        # "West Bromwich Albion Or Draw" = home_draw (1.39)
                                        # "West Bromwich Albion Or Middlesbrough FC" = home_away (1.31)
                                        # "Draw Or Middlesbrough FC" = away_draw (1.50)
                                        
                                        if home_team and away_team:
                                            has_home = home_team.lower() in item_text_lower
                                            has_away = away_team.lower() in item_text_lower
                                            has_draw = "draw" in item_text_lower
                                            
                                            # home_draw: has home + draw, but NOT away
                                            if has_home and has_draw and not has_away:
                                                game_data['home_draw_odds'] = odds_value
                                            # away_draw: has away + draw, but NOT home
                                            elif has_away and has_draw and not has_home:
                                                game_data['away_draw_odds'] = odds_value
                                            # home_away: has both home and away, but NOT draw
                                            elif has_home and has_away and not has_draw:
                                                game_data['home_away_odds'] = odds_value
                                        else:
                                            # Fallback: use position if team names not available
                                            # This is less reliable but better than nothing
                                            item_index = odds_items.index(item)
                                            if item_index == 0:
                                                game_data['home_draw_odds'] = odds_value
                                            elif item_index == 2:
                                                game_data['away_draw_odds'] = odds_value
                                            elif item_index == 1:
                                                game_data['home_away_odds'] = odds_value
                
                except Exception as e:
                    # Continue to next market if this one fails
                    continue
            
            # Extract team-specific "Over 0.5" odds using search
            # Try to find team-specific markets directly first (without search)
            home_team = game_data.get('home_team')
            away_team = game_data.get('away_team')
            
            # First, try to find team-specific markets directly without search
            try:
                all_markets = page.locator("details").all()
                for market in all_markets:
                    try:
                        summary_text = market.locator("summary").inner_text().strip()
                        
                        # Check for home team Total (0.5) market
                        if home_team and home_team in summary_text and "Total (0.5)" in summary_text and "1st Half" not in summary_text and "2nd Half" not in summary_text:
                            odds_grid = market.locator("div.grid.grid-cols-2").first
                            if odds_grid.count() > 0:
                                odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                                for item in odds_items:
                                    label_div = item.locator("div").first
                                    if label_div.count() > 0:
                                        item_text = label_div.inner_text().strip()
                                        if "Over" in item_text and "(0.5)" in item_text:
                                            odds_spans = item.locator("span").all()
                                            if len(odds_spans) > 0:
                                                game_data['home_team_over_0.5'] = self.convert_to_float(odds_spans[-1].inner_text().strip())
                                                break
                        
                        # Check for away team Total (0.5) market
                        if away_team and away_team in summary_text and "Total (0.5)" in summary_text and "1st Half" not in summary_text and "2nd Half" not in summary_text:
                            odds_grid = market.locator("div.grid.grid-cols-2").first
                            if odds_grid.count() > 0:
                                odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                                for item in odds_items:
                                    label_div = item.locator("div").first
                                    if label_div.count() > 0:
                                        item_text = label_div.inner_text().strip()
                                        if "Over" in item_text and "(0.5)" in item_text:
                                            odds_spans = item.locator("span").all()
                                            if len(odds_spans) > 0:
                                                game_data['away_team_over_0.5'] = self.convert_to_float(odds_spans[-1].inner_text().strip())
                                                break
                    except Exception as e:
                        # Continue to next market if this one fails
                        continue
            except Exception as e:
                print(f"    Error finding team markets directly: {str(e)}")
            
            # If not found directly, try using search (only if still None)
            if home_team and game_data.get('home_team_over_0.5') is None:
                try:
                    # Click search button (the one with search icon in the sticky header)
                    search_button = page.locator("div.flex.gap-2.sticky div.flex.items-center.justify-center.rounded-lg.cursor-pointer.bg-dark-800.w-9.h-9").first
                    if search_button.count() > 0:
                        search_button.click()
                        random_sleep("short")
                        
                        # Find and fill search input (it appears after clicking)
                        search_input = page.locator("input.w-full.px-2.pr-8.text-xs.border.rounded-lg").first
                        if search_input.count() == 0:
                            # Try alternative selector - input that appears in the absolute positioned div
                            search_input = page.locator("div.absolute.top-1\\/2 input").first
                        
                        if search_input.count() > 0:
                            search_input.fill(home_team)
                            random_sleep("medium")
                            
                            # Wait for filtered market to appear
                            try:
                                # Look for market with team name in summary
                                random_sleep("short")
                                
                                # Find all markets and check for team-specific Total market
                                all_markets = page.locator("details").all()
                                for market in all_markets:
                                    summary_text = market.locator("summary").inner_text().strip()
                                    if home_team in summary_text and "Total (0.5)" in summary_text and "1st Half" not in summary_text and "2nd Half" not in summary_text:
                                        # Extract "Over (0.5)" odds
                                        odds_grid = market.locator("div.grid.grid-cols-2").first
                                        if odds_grid.count() > 0:
                                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                                            for item in odds_items:
                                                label_div = item.locator("div").first
                                                if label_div.count() > 0:
                                                    item_text = label_div.inner_text().strip()
                                                    if "Over" in item_text and "(0.5)" in item_text:
                                                        odds_spans = item.locator("span").all()
                                                        if len(odds_spans) > 0:
                                                            game_data['home_team_over_0.5'] = self.convert_to_float(odds_spans[-1].inner_text().strip())
                                                            break
                                        break
                            except Exception as e:
                                print(f"    Error finding home team market via search: {str(e)}")
                            
                            # Always try to clear search and close, even if we found the market or not
                            try:
                                search_input.fill("")
                                random_sleep("short")
                                search_button.click()
                                random_sleep("short")
                            except:
                                pass
                except Exception as e:
                    print(f"    Error extracting home team over 0.5: {str(e)}")
            
            if away_team and game_data.get('away_team_over_0.5') is None:
                try:
                    # Click search button (the one with search icon in the sticky header)
                    search_button = page.locator("div.flex.gap-2.sticky div.flex.items-center.justify-center.rounded-lg.cursor-pointer.bg-dark-800.w-9.h-9").first
                    if search_button.count() > 0:
                        search_button.click()
                        random_sleep("short")
                        
                        # Find and fill search input (it appears after clicking)
                        search_input = page.locator("input.w-full.px-2.pr-8.text-xs.border.rounded-lg").first
                        if search_input.count() == 0:
                            # Try alternative selector - input that appears in the absolute positioned div
                            search_input = page.locator("div.absolute.top-1\\/2 input").first
                        
                        if search_input.count() > 0:
                            search_input.fill(away_team)
                            random_sleep("medium")
                            
                            # Wait for filtered market to appear
                            try:
                                # Look for market with team name in summary
                                random_sleep("short")
                                
                                # Find all markets and check for team-specific Total market
                                all_markets = page.locator("details").all()
                                for market in all_markets:
                                    summary_text = market.locator("summary").inner_text().strip()
                                    if away_team in summary_text and "Total (0.5)" in summary_text and "1st Half" not in summary_text and "2nd Half" not in summary_text:
                                        # Extract "Over (0.5)" odds
                                        odds_grid = market.locator("div.grid.grid-cols-2").first
                                        if odds_grid.count() > 0:
                                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                                            for item in odds_items:
                                                label_div = item.locator("div").first
                                                if label_div.count() > 0:
                                                    item_text = label_div.inner_text().strip()
                                                    if "Over" in item_text and "(0.5)" in item_text:
                                                        odds_spans = item.locator("span").all()
                                                        if len(odds_spans) > 0:
                                                            game_data['away_team_over_0.5'] = self.convert_to_float(odds_spans[-1].inner_text().strip())
                                                            break
                                        break
                            except Exception as e:
                                print(f"    Error finding away team market via search: {str(e)}")
                            
                            # Always try to clear search and close, even if we found the market or not
                            try:
                                search_input.fill("")
                                random_sleep("short")
                                search_button.click()
                                random_sleep("short")
                            except:
                                pass
                except Exception as e:
                    print(f"    Error extracting away team over 0.5: {str(e)}")
            
        except Exception as e:
            print(f"    Error scraping game details from {game_url}: {str(e)}")
            # Ensure we still return game_data even if there was an error
            # The fields are already initialized to None, so they'll be null in JSON
        
        # Ensure team over 0.5 fields are None (null) if not found
        if 'home_team_over_0.5' not in game_data or game_data.get('home_team_over_0.5') is None:
            game_data['home_team_over_0.5'] = None
        if 'away_team_over_0.5' not in game_data or game_data.get('away_team_over_0.5') is None:
            game_data['away_team_over_0.5'] = None
        
        return game_data

    def run(self):
        user_agent = get_user_agent()

        # Unix Timestamp for tomorrow
        # South Africa Standard Time (UTC+2)
        SAST = timezone(timedelta(hours=2))

        # Tomorrow's date
        today_sast = datetime.now(SAST)
        tomorrow_sast = today_sast + timedelta(days=1)

        # Start of tomorrow (00:00:00)
        start_time_sast = tomorrow_sast.replace(hour=0, minute=0, second=0, microsecond=0)

        # End of tomorrow (23:59:59)
        end_time_sast = tomorrow_sast.replace(hour=23, minute=59, second=59, microsecond=0)

        # Convert to Unix timestamps
        start_unix = int(start_time_sast.timestamp())
        end_unix = int(end_time_sast.timestamp())

        print("Start Unix timestamp:", start_unix)
        print("End Unix timestamp:", end_unix)

        # Flatten all leagues from the dictionary
        leagues = _load_leagues()
        all_leagues = []
        for country_leagues in leagues.values():
            all_leagues.extend(country_leagues)

        base_url = "https://betway.co.za"
        all_game_hrefs = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="en-ZA",
            )
            page = context.new_page()

            # Iterate over each league to scrape game data
            all_games_data = []
            
            for league in all_leagues:
                highlights_url = (
                    f"https://betway.co.za/sport/soccer/highlights?"
                    f"sortOrder=League&fromStartEpoch={start_unix}&toStartEpoch={end_unix}&selectedLeagues={league}"
                )
                
                print(f"\nProcessing league: {league}")
                print(f"URL: {highlights_url}")
                
                try:
                    # Navigate to highlights URL (inside try so timeout skips league, doesn't fail whole run)
                    page.goto(highlights_url, timeout=60000, wait_until="domcontentloaded")
                    page.wait_for_selector("#sportsbook-container", timeout=15000)
                    random_sleep("between_leagues")
                    
                    # Extract game hrefs for reference
                    game_links = page.locator("#sportsbook-container a[href*='/event/soccer']").all()
                    game_hrefs = []
                    for link in game_links:
                        href = link.get_attribute("href")
                        if href:
                            if href.startswith("/"):
                                full_url = base_url + href
                            elif href.startswith("http"):
                                full_url = href
                            else:
                                full_url = base_url + "/" + href
                            if full_url not in game_hrefs:
                                game_hrefs.append(full_url)
                    
                    if game_hrefs:
                        print(f"Found {len(game_hrefs)} game links")
                        all_game_hrefs.extend(game_hrefs)
                    
                    # Find all game rows - each game is in a div with id attribute inside details
                    game_rows = page.locator("#sportsbook-container div[id^='6']").all()
                    
                    # Alternative: find by the grid structure
                    if not game_rows:
                        game_rows = page.locator("#sportsbook-container div.grid.grid-cols-12").all()
                    
                    if not game_rows:
                        print(f"No games found for {league}, skipping...")
                        continue
                    
                    print(f"Scraping data from {len(game_rows)} games...")
                    
                    for game_row in game_rows:
                        try:
                            game_data = {
                                'home_team': None,
                                'away_team': None,
                                'home_draw_odds': None,
                                'away_draw_odds': None,
                                'home_away_odds': None,
                                'date': None,
                                'time': None,
                            }
                            
                            # Extract team names - they're in strong tags within flex-col
                            team_container = game_row.locator("div.flex.flex-col.justify-between").first
                            if team_container.count() > 0:
                                team_names = team_container.locator("strong").all()
                                if len(team_names) >= 2:
                                    game_data['home_team'] = team_names[0].inner_text().strip()
                                    game_data['away_team'] = team_names[1].inner_text().strip()
                            
                            # Extract date and time - it's in a span after an SVG icon
                            date_time_container = game_row.locator("div.flex.items-center.gap-1").first
                            if date_time_container.count() > 0:
                                date_time_text = date_time_container.inner_text().strip()
                                # Parse "16 Dec - 20:00" format
                                if " - " in date_time_text:
                                    parts = date_time_text.split(" - ")
                                    if len(parts) >= 2:
                                        game_data['date'] = parts[0].strip()
                                        game_data['time'] = parts[1].strip()
                            
                            # Extract odds - find all odds rows (divs with relative flex w-full gap-1)
                            odds_rows = game_row.locator("div.relative.flex.w-full.gap-1").all()
                            
                            # Second row typically contains Double Chance odds (Home/Draw, Away/Draw) - 2 odds
                            if len(odds_rows) >= 2:
                                double_chance_spans = odds_rows[1].locator("span").all()
                                if len(double_chance_spans) >= 2:
                                    game_data['home_draw_odds'] = self.convert_to_float(double_chance_spans[0].inner_text().strip())
                                    game_data['away_draw_odds'] = self.convert_to_float(double_chance_spans[1].inner_text().strip())
                            
                            # For Home/Away odds, we might need to look at a different market
                            # Let's check if there's a third row or look for specific pattern
                            # Actually, Home/Away might be in the first row (3 odds: Home, Draw, Away)
                            # But user asked for home_away_odds which is likely "Home or Away" (no draw)
                            # This might be in a different market row
                            if len(odds_rows) >= 3:
                                # Third row might have different markets
                                third_row_spans = odds_rows[2].locator("span").all()
                                if len(third_row_spans) >= 2:
                                    # Assuming first two are Home/Away related
                                    game_data['home_away_odds'] = self.convert_to_float(third_row_spans[0].inner_text().strip())
                            
                            # Get game URL for detailed scraping
                            game_link_elem = game_row.locator("a[href*='/event/soccer']").first
                            game_url = None
                            if game_link_elem.count() > 0:
                                href = game_link_elem.get_attribute("href")
                                if href:
                                    if href.startswith("/"):
                                        game_url = base_url + href
                                    elif href.startswith("http"):
                                        game_url = href
                                    else:
                                        game_url = base_url + "/" + href
                            
                            # Only add if we have at least team names
                            if game_data['home_team'] and game_data['away_team']:
                                # Add game URL to data
                                game_data['game_url'] = game_url
                                all_games_data.append(game_data)
                                print(f"  ✓ {game_data['home_team']} vs {game_data['away_team']} - {game_data['date']} {game_data['time']}")
                            else:
                                print(f"  ✗ Skipped game (missing team data)")
                                
                        except Exception as e:
                            print(f"  ✗ Error scraping game row: {str(e)}")
                            continue
                            
                except Exception as e:
                    err_msg = str(e)
                    if "Timeout" in err_msg or "timeout" in err_msg:
                        print(f"  ⚠ Timeout loading {league}, skipping (continuing with other leagues)...")
                    else:
                        print(f"  ✗ Error processing league {league}: {err_msg}")
                    continue
            
            # Now navigate to each game page to get detailed odds
            print(f"\n\n=== SCRAPING DETAILED ODDS ===")
            print(f"Navigating to {len(all_games_data)} game pages...")
            
            for i, game_data in enumerate(all_games_data, 1):
                if game_data.get('game_url'):
                    print(f"\n[{i}/{len(all_games_data)}] Scraping: {game_data['home_team']} vs {game_data['away_team']}")
                    try:
                        self.scrape_game_details(page, game_data['game_url'], game_data)
                        random_sleep("between_games")
                    except Exception as e:
                        print(f"    ⚠ Error scraping details (game will still be saved): {str(e)}")
                        # Game data is already in the list, so it will be saved even if details scraping fails
                else:
                    print(f"\n[{i}/{len(all_games_data)}] Skipping: No game URL available")
            
            # Save to database (run in thread to avoid async context)
            if all_games_data:
                def _save_betway_to_db():
                    from betting_engine.importers import import_betway_odds
                    return import_betway_odds(tomorrow_sast.date(), all_games_data)

                try:
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(_save_betway_to_db)
                        db_result = future.result()
                    print(f"\nDatabase: Created {db_result['created']}, Updated {db_result['updated']}")
                except Exception as e:
                    print(f"\n⚠ Database save failed: {e}")
            
            print(f"\n\n=== SUMMARY ===")
            print(f"Total game links found: {len(all_game_hrefs)}")
            print(f"Total games scraped: {len(all_games_data)}")
            
            print(f"\n=== SAMPLE DATA ===")
            if all_games_data:
                sample = all_games_data[0]
                print(f"\nSample game:")
                print(f"  Home Team: {sample.get('home_team')}")
                print(f"  Away Team: {sample.get('away_team')}")
                print(f"  Date: {sample.get('date')}")
                print(f"  Time: {sample.get('time')}")
                print(f"  Home Win: {sample.get('home_win')}")
                print(f"  Draw: {sample.get('draw')}")
                print(f"  Away Win: {sample.get('away_win')}")
                print(f"  Home Draw No Bet: {sample.get('home_draw_no_bet')}")
                print(f"  Away Draw No Bet: {sample.get('away_draw_no_bet')}")
                print(f"  Total Over 1.5: {sample.get('total_over_1.5')}")
                print(f"  Total Under 3.5: {sample.get('total_under_3.5')}")
                print(f"  BTTS Yes: {sample.get('BTTS_yes')}")
                print(f"  BTTS No: {sample.get('BTTS_no')}")
                print(f"  Home Team Over 0.5: {sample.get('home_team_over_0.5')}")
                print(f"  Away Team Over 0.5: {sample.get('away_team_over_0.5')}")

            context.close()
            browser.close()
            return all_games_data
