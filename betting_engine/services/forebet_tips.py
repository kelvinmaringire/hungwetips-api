from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
import time


class ForebetScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "https://www.forebet.com"
        self.leagues_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "betting_data",
            "forebet_leagues.json"
        )
        
    def load_leagues(self) -> List[Dict[str, str]]:
        """Load league URLs from JSON file with country and league name"""
        try:
            with open(self.leagues_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract all league paths with metadata
            league_data = []
            for country, leagues in data.items():
                for league_path in leagues:
                    # Extract league name from path (e.g., "premier-league" from "football-tips-and-predictions-for-england/premier-league")
                    league_name = league_path.split('/')[-1] if '/' in league_path else league_path
                    # Convert to readable format (e.g., "premier-league" -> "Premier League")
                    league_name_formatted = league_name.replace('-', ' ').title()
                    
                    league_data.append({
                        "country": country,
                        "league_name": league_name_formatted,
                        "league_path": league_path,
                        "url": f"{self.base_url}/en/{league_path}"
                    })
            
            return league_data
        except Exception as e:
            print(f"Error loading leagues: {e}")
            return []
    
    def parse_date_time(self, date_str: str, time_str: str) -> Optional[datetime]:
        """Parse date and time strings to datetime object"""
        try:
            # Date format: "17/01/2026 14:30" or "17/01/2026"
            # Clean up the strings
            date_str = date_str.strip()
            time_str = time_str.strip() if time_str else "00:00"
            
            # If time_str doesn't have :, assume it's just hours
            if ":" not in time_str and time_str.isdigit():
                time_str = f"{time_str}:00"
            
            dt_str = f"{date_str} {time_str}"
            return datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
        except Exception as e:
            print(f"Error parsing date/time '{date_str} {time_str}': {e}")
            return None
    
    def parse_score(self, score_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        """Parse score string like '3 - 2' or '(1 - 0)' into home and away scores"""
        if not score_str:
            return None, None
        
        try:
            # Remove parentheses if present (for half-time scores)
            score_str = score_str.strip().strip('()')
            
            # Split by common delimiters
            parts = score_str.replace(' - ', '-').replace('–', '-').replace('—', '-').split('-')
            
            if len(parts) == 2:
                home_score = int(parts[0].strip())
                away_score = int(parts[1].strip())
                return home_score, away_score
        except (ValueError, AttributeError):
            pass
        
        return None, None
    
    def convert_to_int(self, value: Optional[str]) -> Optional[int]:
        """Convert string to integer, return None if invalid"""
        if value is None or value == "":
            return None
        try:
            return int(value.strip())
        except (ValueError, AttributeError):
            return None
    
    def convert_to_float(self, value: Optional[str]) -> Optional[float]:
        """Convert string to float, return None if invalid"""
        if value is None or value == "":
            return None
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            return None
    
    def extract_match_id(self, row) -> Optional[int]:
        """Extract match ID from various sources in the row"""
        try:
            # Method 1: Try to get from fav_icon div ID (most reliable)
            fav_icon = row.locator(".fav_icon[id]")
            if fav_icon.count() > 0:
                match_id_str = fav_icon.first.get_attribute("id")
                if match_id_str and match_id_str.isdigit():
                    return int(match_id_str)
            
            # Method 2: Try to get from onclick attribute in stcn div
            stcn_div = row.locator(".stcn")
            if stcn_div.count() > 0:
                onclick = stcn_div.first.get_attribute("onclick")
                if onclick:
                    match = re.search(r'getstag\([^,]+,\s*(\d{7,})', onclick)
                    if match:
                        return int(match.group(1))
            
            # Method 3: Try to get from game URL
            link_elem = row.locator("a.tnmscn[itemprop='url']")
            if link_elem.count() > 0:
                href = link_elem.first.get_attribute("href")
                if href:
                    match = re.search(r'-(\d{7,})$', href)
                    if match:
                        return int(match.group(1))
            
            # Method 4: Try to get from any onclick in the row
            onclick_elems = row.locator("[onclick*='getstag']")
            if onclick_elems.count() > 0:
                onclick = onclick_elems.first.get_attribute("onclick")
                if onclick:
                    match = re.search(r'getstag\([^,]+,\s*(\d{7,})', onclick)
                    if match:
                        return int(match.group(1))
            
            return None
        except Exception as e:
            print(f"Error extracting match ID: {e}")
            return None
    
    def extract_preview_html(self, html_content: str) -> Optional[str]:
        """
        Extract preview HTML content from page HTML.
        Looks for content within <td class="contentmiddle"> and extracts <p> tags.

        Args:
            html_content: Raw HTML content from the page

        Returns:
            HTML string containing only the preview paragraphs, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find the content container
        # First, try <td class="contentmiddle">
        content_container = soup.find('td', class_='contentmiddle')
        
        # If not found, try other common containers
        if not content_container:
            content_container = soup.find('div', class_='contentmiddle')
        
        if not content_container:
            # Try to find main content area
            content_container = soup.find('div', {'id': 'content'}) or soup.find('article')
        
        # If still not found, use body as fallback
        if not content_container:
            content_container = soup.find('body')
        
        if not content_container:
            return None
        
        # Extract all <p> tags from the container
        paragraphs = content_container.find_all('p')
        
        if not paragraphs:
            return None
        
        # Build HTML string from paragraphs
        preview_html = ''
        for p in paragraphs:
            # Get the HTML content of the paragraph (preserving inner HTML)
            p_html = str(p)
            preview_html += p_html + '\n'
        
        return preview_html.strip()
    
    def scrape_preview(self, page: Page, preview_url: str) -> Optional[str]:
        """
        Scrape preview content from a preview URL.

        Args:
            page: Playwright page object
            preview_url: URL to the preview page

        Returns:
            HTML string containing preview paragraphs, or None if failed
        """
        try:
            # Navigate to preview page
            page.goto(preview_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(2)  # Wait for content to load
            
            # Get page HTML content
            html_content = page.content()
            
            # Extract preview HTML
            preview_html = self.extract_preview_html(html_content)
            
            return preview_html
            
        except Exception as e:
            print(f"  ✗ Error scraping preview from {preview_url}: {e}")
            return None
    
    def scrape_tomorrow_tips(self, page: Page, league_url: str, country: str = None, league_name: str = None, seen_match_ids: set = None) -> List[Dict]:
        """Scrape tips for tomorrow's games"""
        if seen_match_ids is None:
            seen_match_ids = set()
        
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_date = tomorrow.date()
        
        print(f"\nScraping tomorrow's tips ({tomorrow_date}) from {league_url}")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                page.goto(league_url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_selector(".rcnt", timeout=10000)
                break
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                if "Page crashed" in error_msg or "Target closed" in error_msg:
                    print(f"  ⚠ Page crashed, will be recreated by caller")
                    raise  # Re-raise to let caller handle page recreation
                if retry_count >= max_retries:
                    print(f"Error scraping tomorrow's tips after {max_retries} retries: {e}")
                    return []
                print(f"  ⚠ Retry {retry_count}/{max_retries} for {league_url}")
                try:
                    page.wait_for_timeout(2000)
                except:
                    raise  # If page is dead, re-raise
        
        tips = []
        try:
            game_rows = page.locator(".rcnt").all()
            
            for row in game_rows:
                try:
                    # Extract date and time
                    date_elem = row.locator("time[itemprop='startDate']")
                    if date_elem.count() == 0:
                        continue
                    
                    datetime_attr = date_elem.first.get_attribute("datetime")
                    date_bah = row.locator(".date_bah").first.inner_text() if row.locator(".date_bah").count() > 0 else None
                    
                    if not datetime_attr and not date_bah:
                        continue
                    
                    # Parse date
                    game_date = None
                    if datetime_attr:
                        try:
                            # datetime format: "2026-01-17"
                            game_date = datetime.fromisoformat(datetime_attr)
                        except:
                            try:
                                game_date = datetime.strptime(datetime_attr, "%Y-%m-%d")
                            except:
                                pass
                    
                    if not game_date and date_bah:
                        parts = date_bah.split()
                        if len(parts) >= 2:
                            date_str = parts[0]
                            time_str = parts[1] if len(parts) > 1 else "00:00"
                            game_date = self.parse_date_time(date_str, time_str)
                        elif len(parts) == 1:
                            # Only date, no time
                            game_date = self.parse_date_time(parts[0], "00:00")
                    
                    if not game_date:
                        continue
                    
                    # Skip if not tomorrow
                    if game_date.date() != tomorrow_date:
                        continue
                    
                    # Extract match ID
                    match_id = self.extract_match_id(row)
                    
                    # Skip if already seen
                    if match_id and match_id in seen_match_ids:
                        home_team = row.locator(".homeTeam span[itemprop='name']").first.inner_text() if row.locator(".homeTeam span[itemprop='name']").count() > 0 else "Unknown"
                        away_team = row.locator(".awayTeam span[itemprop='name']").first.inner_text() if row.locator(".awayTeam span[itemprop='name']").count() > 0 else "Unknown"
                        print(f"  ⊗ Skipped duplicate tip: match_id {match_id} ({home_team} vs {away_team})")
                        continue
                    
                    # Extract team names
                    home_team = row.locator(".homeTeam span[itemprop='name']").first.inner_text() if row.locator(".homeTeam span[itemprop='name']").count() > 0 else None
                    away_team = row.locator(".awayTeam span[itemprop='name']").first.inner_text() if row.locator(".awayTeam span[itemprop='name']").count() > 0 else None
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Extract game link
                    game_link_elem = row.locator("a.tnmscn[itemprop='url']")
                    game_link = game_link_elem.first.get_attribute("href") if game_link_elem.count() > 0 else None
                    if game_link and not game_link.startswith("http"):
                        game_link = f"{self.base_url}{game_link}"
                    
                    # Extract preview link - try multiple selectors
                    preview_link = None
                    
                    # Method 1: Try .mprv a (most common - inside lscr_td for upcoming games)
                    preview_link_elem = row.locator(".lscr_td .mprv a")
                    if preview_link_elem.count() > 0:
                        preview_link = preview_link_elem.first.get_attribute("href")
                    
                    # Method 2: Try .mprv a directly in row (fallback)
                    if not preview_link:
                        preview_link_elem = row.locator(".mprv a")
                        if preview_link_elem.count() > 0:
                            preview_link = preview_link_elem.first.get_attribute("href")
                    
                    # Method 3: Try any a tag with href containing "football-match-previews" anywhere in row
                    if not preview_link:
                        preview_link_elem = row.locator("a[href*='football-match-previews']")
                        if preview_link_elem.count() > 0:
                            preview_link = preview_link_elem.first.get_attribute("href")
                    
                    # Method 4: Try finding link by text content "PREVIEW" or "PRE"
                    if not preview_link:
                        # Look for links containing "PREVIEW" text
                        all_links = row.locator("a").all()
                        for link in all_links:
                            try:
                                link_text = link.inner_text().strip().upper()
                                if "PREVIEW" in link_text or (link_text == "PREVIEW") or ("PRE" in link_text and "VIEW" in link_text):
                                    href = link.get_attribute("href")
                                    if href and "football-match-previews" in href:
                                        preview_link = href
                                        break
                            except:
                                continue
                    
                    # Convert relative URL to absolute if found
                    if preview_link:
                        preview_link = preview_link.strip()
                        if not preview_link.startswith("http"):
                            preview_link = f"{self.base_url}{preview_link}"
                    else:
                        preview_link = None
                    
                    # Extract probabilities (1 X 2) and convert to integers
                    prob_spans = row.locator(".fprc span").all()
                    prob_1_str = prob_spans[0].inner_text() if len(prob_spans) > 0 else None
                    prob_x_str = prob_spans[1].inner_text() if len(prob_spans) > 1 else None
                    prob_2_str = prob_spans[2].inner_text() if len(prob_spans) > 2 else None
                    prob_1 = self.convert_to_int(prob_1_str)
                    prob_x = self.convert_to_int(prob_x_str)
                    prob_2 = self.convert_to_int(prob_2_str)
                    
                    # Extract prediction
                    predict_elem = row.locator(".predict .forepr span, .predict_no .forepr span, .predict_y .forepr span")
                    prediction = predict_elem.first.inner_text() if predict_elem.count() > 0 else None
                    
                    # Extract correct score and parse into separate fields
                    correct_score_elem = row.locator(".ex_sc.tabonly")
                    correct_score_str = correct_score_elem.first.inner_text().strip() if correct_score_elem.count() > 0 else None
                    home_pred_score, away_pred_score = self.parse_score(correct_score_str)
                    
                    # Extract average goals and convert to float
                    avg_goals_elem = row.locator(".avg_sc.tabonly")
                    avg_goals_str = avg_goals_elem.first.inner_text().strip() if avg_goals_elem.count() > 0 else None
                    avg_goals = self.convert_to_float(avg_goals_str)
                    
                    # Extract Kelly Criterion and convert to float
                    kelly_elem = row.locator(".la_prmod.tabonly")
                    kelly_str = kelly_elem.first.inner_text().strip() if kelly_elem.count() > 0 else None
                    kelly = self.convert_to_float(kelly_str)
                    
                    # Extract date and time strings
                    date_str = date_bah.split()[0] if date_bah else game_date.strftime("%d/%m/%Y")
                    time_str = date_bah.split()[1] if date_bah and len(date_bah.split()) > 1 else game_date.strftime("%H:%M")
                    
                    # Scrape preview HTML if preview_link exists
                    preview_html = None
                    if preview_link:
                        try:
                            preview_html = self.scrape_preview(page, preview_link)
                            if preview_html:
                                print(f"  ✓ Preview scraped ({len(preview_html)} characters)")
                            else:
                                print(f"  ⚠ Preview link found but content extraction failed")
                        except Exception as e:
                            print(f"  ⚠ Error scraping preview: {e}")
                    
                    tip = {
                        "match_id": match_id,
                        "country": country,
                        "league_name": league_name,
                        "home_team": home_team,
                        "away_team": away_team,
                        "date": date_str,
                        "time": time_str,
                        "game_link": game_link,
                        "preview_link": preview_link if preview_link else None,
                        "preview_html": preview_html,
                        "prob_1": prob_1,
                        "prob_x": prob_x,
                        "prob_2": prob_2,
                        "pred": prediction,
                        "home_pred_score": home_pred_score,
                        "away_pred_score": away_pred_score,
                        "avg_goals": avg_goals,
                        "kelly": kelly
                    }
                    
                    tips.append(tip)
                    if match_id:
                        seen_match_ids.add(match_id)
                    print(f"  ✓ Found: {home_team} vs {away_team} ({date_str} {time_str})")
                    
                    # Small delay after scraping preview to avoid rate limiting
                    if preview_html:
                        time.sleep(1)
                    
                except Exception as e:
                    print(f"  ✗ Error processing game row: {e}")
                    continue
            
            return tips
            
        except Exception as e:
            print(f"Error scraping tomorrow's tips: {e}")
            return []
    
    def scrape_yesterday_results(self, page: Page, league_url: str, country: str = None, league_name: str = None, seen_match_ids: set = None) -> List[Dict]:
        """Scrape results for yesterday's games"""
        if seen_match_ids is None:
            seen_match_ids = set()
        
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_date = yesterday.date()
        
        print(f"\nScraping yesterday's results ({yesterday_date}) from {league_url}")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                page.goto(league_url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_selector(".rcnt", timeout=10000)
                break
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                if "Page crashed" in error_msg or "Target closed" in error_msg:
                    print(f"  ⚠ Page crashed, will be recreated by caller")
                    raise  # Re-raise to let caller handle page recreation
                if retry_count >= max_retries:
                    print(f"Error scraping yesterday's results after {max_retries} retries: {e}")
                    return []
                print(f"  ⚠ Retry {retry_count}/{max_retries} for {league_url}")
                try:
                    page.wait_for_timeout(2000)
                except:
                    raise  # If page is dead, re-raise
        
        results = []
        try:
            game_rows = page.locator(".rcnt").all()
            
            for row in game_rows:
                try:
                    # Check if game has finished (has score)
                    score_elem = row.locator(".lscr_td b.l_scr")
                    if score_elem.count() == 0:
                        continue
                    
                    score_text = score_elem.first.inner_text().strip()
                    if not score_text or score_text == "":
                        continue
                    
                    # Extract date
                    date_elem = row.locator("time[itemprop='startDate']")
                    if date_elem.count() == 0:
                        continue
                    
                    datetime_attr = date_elem.first.get_attribute("datetime")
                    date_bah = row.locator(".date_bah").first.inner_text() if row.locator(".date_bah").count() > 0 else None
                    
                    if not datetime_attr and not date_bah:
                        continue
                    
                    # Parse date
                    game_date = None
                    if datetime_attr:
                        try:
                            # datetime format: "2026-01-17"
                            game_date = datetime.fromisoformat(datetime_attr)
                        except:
                            try:
                                game_date = datetime.strptime(datetime_attr, "%Y-%m-%d")
                            except:
                                pass
                    
                    if not game_date and date_bah:
                        parts = date_bah.split()
                        if len(parts) >= 2:
                            date_str = parts[0]
                            time_str = parts[1] if len(parts) > 1 else "00:00"
                            game_date = self.parse_date_time(date_str, time_str)
                        elif len(parts) == 1:
                            # Only date, no time
                            game_date = self.parse_date_time(parts[0], "00:00")
                    
                    if not game_date:
                        continue
                    
                    # Skip if not yesterday
                    if game_date.date() != yesterday_date:
                        continue
                    
                    # Extract match ID
                    match_id = self.extract_match_id(row)
                    
                    # Skip if already seen (same match appearing in multiple leagues)
                    if match_id and match_id in seen_match_ids:
                        home_team = row.locator(".homeTeam span[itemprop='name']").first.inner_text() if row.locator(".homeTeam span[itemprop='name']").count() > 0 else "Unknown"
                        away_team = row.locator(".awayTeam span[itemprop='name']").first.inner_text() if row.locator(".awayTeam span[itemprop='name']").count() > 0 else "Unknown"
                        print(f"  ⊗ Skipped duplicate result: match_id {match_id} ({home_team} vs {away_team})")
                        continue
                    
                    # Extract team names (only for logging, not included in result)
                    home_team = row.locator(".homeTeam span[itemprop='name']").first.inner_text() if row.locator(".homeTeam span[itemprop='name']").count() > 0 else None
                    away_team = row.locator(".awayTeam span[itemprop='name']").first.inner_text() if row.locator(".awayTeam span[itemprop='name']").count() > 0 else None
                    
                    if not home_team or not away_team:
                        continue
                    
                    # Parse full-time score into separate fields
                    home_correct_score, away_correct_score = self.parse_score(score_text)
                    
                    # Extract half-time score if available and parse into separate fields
                    ht_score_elem = row.locator(".ht_scr")
                    ht_score_str = ht_score_elem.first.inner_text().strip() if ht_score_elem.count() > 0 else None
                    home_ht_score, away_ht_score = self.parse_score(ht_score_str)
                    
                    result = {
                        "match_id": match_id,
                        "home_correct_score": home_correct_score,
                        "away_correct_score": away_correct_score,
                        "home_ht_score": home_ht_score,
                        "away_ht_score": away_ht_score
                    }
                    
                    results.append(result)
                    if match_id:
                        seen_match_ids.add(match_id)
                    score_display = f"{home_correct_score} - {away_correct_score}" if home_correct_score is not None and away_correct_score is not None else "N/A"
                    print(f"  ✓ Found: {home_team} vs {away_team} - {score_display}")
                    
                except Exception as e:
                    print(f"  ✗ Error processing result row: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error scraping yesterday's results: {e}")
            return []
    
    def recreate_page(self, context):
        """Recreate a page if it crashes"""
        try:
            page = context.new_page()
            return page
        except Exception as e:
            print(f"Error recreating page: {e}")
            return None
    
    def run(self):
        """Main scraping function"""
        league_urls = self.load_leagues()
        
        if not league_urls:
            print("No leagues found to scrape")
            return
        
        all_tips = []
        all_results = []
        seen_match_ids = set()  # Track seen match IDs to prevent duplicates
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                for league_info in league_urls:
                    league_url = league_info["url"]
                    country = league_info["country"]
                    league_name = league_info["league_name"]
                    
                    print(f"\n{'='*60}")
                    print(f"Processing league: {country} - {league_name}")
                    print(f"URL: {league_url}")
                    print(f"{'='*60}")
                    
                    # Check if page is still valid, recreate if needed
                    try:
                        page.url
                    except:
                        print("  ⚠ Page crashed, recreating...")
                        page.close()
                        page = self.recreate_page(context)
                        if not page:
                            print("  ✗ Failed to recreate page, skipping league")
                            continue
                    
                    # Scrape tomorrow's tips with duplicate checking
                    try:
                        tips = self.scrape_tomorrow_tips(page, league_url, country, league_name, seen_match_ids)
                        all_tips.extend(tips)
                    except Exception as e:
                        print(f"  ✗ Error scraping tips: {e}")
                        # Try to recreate page
                        try:
                            page.close()
                        except:
                            pass
                        page = self.recreate_page(context)
                        if not page:
                            print("  ✗ Failed to recreate page, skipping rest of leagues")
                            break
                    
                    # Check if page is still valid before scraping results
                    try:
                        page.url
                    except:
                        print("  ⚠ Page crashed, recreating...")
                        page.close()
                        page = self.recreate_page(context)
                        if not page:
                            print("  ✗ Failed to recreate page, skipping league")
                            continue
                    
                    # Scrape yesterday's results with duplicate checking
                    try:
                        results = self.scrape_yesterday_results(page, league_url, country, league_name, seen_match_ids)
                        all_results.extend(results)
                    except Exception as e:
                        print(f"  ✗ Error scraping results: {e}")
                        # Try to recreate page
                        try:
                            page.close()
                        except:
                            pass
                        page = self.recreate_page(context)
                        if not page:
                            print("  ✗ Failed to recreate page, skipping rest of leagues")
                            break
                    
                    # Small delay between leagues
                    try:
                        page.wait_for_timeout(1000)
                    except:
                        pass
                
            except Exception as e:
                print(f"Fatal error during scraping: {e}")
            finally:
                try:
                    browser.close()
                except:
                    pass
        
        # Save results
        self.save_results(all_tips, all_results)
        
        print(f"\n{'='*60}")
        print(f"Scraping completed!")
        print(f"  Tips found: {len(all_tips)}")
        print(f"  Results found: {len(all_results)}")
        print(f"{'='*60}")
    
    def save_results(self, tips: List[Dict], results: List[Dict]):
        """Save scraped data to JSON files"""
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "betting_data"
        )
        
        os.makedirs(data_dir, exist_ok=True)
        
        # Save tips
        if tips:
            tomorrow = datetime.now() + timedelta(days=1)
            tips_date = tomorrow.date()
            tips_file = os.path.join(data_dir, f"forebet_tips_{tomorrow.strftime('%Y-%m-%d')}.json")
            with open(tips_file, 'w', encoding='utf-8') as f:
                json.dump(tips, f, indent=2, ensure_ascii=False)
            print(f"\nTips saved to: {tips_file}")
            
            # Also save to database
            try:
                from betting_engine.importers import import_forebet_tips
                db_result = import_forebet_tips(tips_date, tips)
                print(f"Database: Created {db_result['created']}, Updated {db_result['updated']}")
            except Exception as e:
                print(f"⚠ Database save failed: {str(e)}")
        
        # Save results
        if results:
            yesterday = datetime.now() - timedelta(days=1)
            results_date = yesterday.date()
            results_file = os.path.join(data_dir, f"forebet_results_{yesterday.strftime('%Y-%m-%d')}.json")
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {results_file}")
            
            # Also save to database
            try:
                from betting_engine.importers import import_forebet_results
                db_result = import_forebet_results(results_date, results)
                print(f"Database: Created {db_result['created']}, Updated {db_result['updated']}")
            except Exception as e:
                print(f"⚠ Database save failed: {str(e)}")


if __name__ == "__main__":
    scraper = ForebetScraper(headless=True)
    scraper.run()

