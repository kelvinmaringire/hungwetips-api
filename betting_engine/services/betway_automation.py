from playwright.sync_api import sync_playwright
from django.conf import settings
from datetime import datetime, timedelta, timezone
import time
import json
import os
import uuid
import sys

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration Constants
DOUBLE_CHANCE_MIN_ODDS = 1.2
TEAM_OVER_05_MIN_ODDS = 1.15
MIN_ML_PROBABILITY = 0.6  # Configurable threshold
MAX_SELECTIONS_PER_TICKET = 3


class BetwayAutomation:
    def __init__(self, headless=True):
        self.headless = headless

    def convert_to_float(self, value):
        """Convert string to float, return None if invalid"""
        if value is None or value == "" or value == " - ":
            return None
        try:
            # If already a float/int, return it
            if isinstance(value, (int, float)):
                return float(value)
            # Otherwise, try to convert string
            return float(str(value).strip())
        except (ValueError, AttributeError, TypeError):
            return None

    def select_double_chance_bets(self, games):
        """Filter and select double chance bets based on ML predictions"""
        selections = []
        
        for game in games:
            try:
                home_team = game.get('home_team', 'Unknown')
                away_team = game.get('away_team', 'Unknown')
                
                # Check ML values for double chance
                ml_home_dnb_value = game.get('ml_home_dnb_value', 0)
                ml_away_dnb_value = game.get('ml_away_dnb_value', 0)
                ml_home_dnb_prob = game.get('ml_home_dnb_prob', 0)
                ml_away_dnb_prob = game.get('ml_away_dnb_prob', 0)
                
                home_draw_odds = self.convert_to_float(game.get('home_draw_odds'))
                away_draw_odds = self.convert_to_float(game.get('away_draw_odds'))
                
                print(f"  Checking: {home_team} vs {away_team}")
                print(f"    ml_home_dnb_value: {ml_home_dnb_value}, prob: {ml_home_dnb_prob:.3f}, odds: {home_draw_odds}")
                print(f"    ml_away_dnb_value: {ml_away_dnb_value}, prob: {ml_away_dnb_prob:.3f}, odds: {away_draw_odds}")
                
                # Skip if no valid odds
                if home_draw_odds is None and away_draw_odds is None:
                    print(f"    ✗ Skipping: No valid odds")
                    continue
                
                # Generate match_id for conflict detection
                match_id = game.get('game_url') or f"{home_team}|{away_team}"
                
                # Check for home_draw bet
                if ml_home_dnb_value == 1 and home_draw_odds is not None:
                    if home_draw_odds >= DOUBLE_CHANCE_MIN_ODDS and ml_home_dnb_prob >= MIN_ML_PROBABILITY:
                        selection = {
                            'game': game,
                            'bet_type': 'home_draw',
                            'odds': home_draw_odds,
                            'ml_probability': ml_home_dnb_prob,
                            'ml_value': ml_home_dnb_value,
                            'team': f"{home_team} or Draw",
                            'game_url': game.get('game_url'),
                            'match_id': match_id,
                            'direction': 'home'
                        }
                        selections.append(selection)
                        print(f"    ✓ Selected: {home_team} or Draw @ {home_draw_odds} (prob: {ml_home_dnb_prob:.2f})")
                        continue  # Only one double chance bet per match
                    else:
                        print(f"    ✗ Rejected home_draw: odds={home_draw_odds:.2f} (min {DOUBLE_CHANCE_MIN_ODDS}) or prob={ml_home_dnb_prob:.3f} (min {MIN_ML_PROBABILITY})")
                
                # Check for away_draw bet
                if ml_away_dnb_value == 1 and away_draw_odds is not None:
                    if away_draw_odds >= DOUBLE_CHANCE_MIN_ODDS and ml_away_dnb_prob >= MIN_ML_PROBABILITY:
                        selection = {
                            'game': game,
                            'bet_type': 'away_draw',
                            'odds': away_draw_odds,
                            'ml_probability': ml_away_dnb_prob,
                            'ml_value': ml_away_dnb_value,
                            'team': f"{away_team} or Draw",
                            'game_url': game.get('game_url'),
                            'match_id': match_id,
                            'direction': 'away'
                        }
                        selections.append(selection)
                        print(f"    ✓ Selected: {away_team} or Draw @ {away_draw_odds} (prob: {ml_away_dnb_prob:.2f})")
                    else:
                        print(f"    ✗ Rejected away_draw: odds={away_draw_odds:.2f} (min {DOUBLE_CHANCE_MIN_ODDS}) or prob={ml_away_dnb_prob:.3f} (min {MIN_ML_PROBABILITY})")
            except Exception as e:
                print(f"  ✗ Error processing game for double chance: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return selections

    def select_team_over_05_bets(self, games):
        """Filter and select team over 0.5 bets based on ML predictions"""
        selections = []
        
        for game in games:
            try:
                home_team = game.get('home_team', 'Unknown')
                away_team = game.get('away_team', 'Unknown')
                
                # Check ML values for team over 0.5
                ml_home_over_05_value = game.get('ml_home_over_05_value', 0)
                ml_away_over_05_value = game.get('ml_away_over_05_value', 0)
                ml_home_over_05_prob = game.get('ml_home_over_05_prob', 0)
                ml_away_over_05_prob = game.get('ml_away_over_05_prob', 0)
                
                home_team_over_05 = self.convert_to_float(game.get('home_team_over_0.5'))
                away_team_over_05 = self.convert_to_float(game.get('away_team_over_0.5'))
                
                print(f"  Checking: {home_team} vs {away_team}")
                print(f"    ml_home_over_05_value: {ml_home_over_05_value}, prob: {ml_home_over_05_prob:.3f}, odds: {home_team_over_05}")
                print(f"    ml_away_over_05_value: {ml_away_over_05_value}, prob: {ml_away_over_05_prob:.3f}, odds: {away_team_over_05}")
                
                # Generate match_id for conflict detection
                match_id = game.get('game_url') or f"{home_team}|{away_team}"
                
                # Check for home team over 0.5 bet
                if ml_home_over_05_value == 1 and home_team_over_05 is not None:
                    if home_team_over_05 >= TEAM_OVER_05_MIN_ODDS and ml_home_over_05_prob >= MIN_ML_PROBABILITY:
                        selection = {
                            'game': game,
                            'bet_type': 'home_over_05',
                            'odds': home_team_over_05,
                            'ml_probability': ml_home_over_05_prob,
                            'ml_value': ml_home_over_05_value,
                            'team': f"{home_team} Over 0.5",
                            'game_url': game.get('game_url'),
                            'match_id': match_id,
                            'direction': 'home'
                        }
                        selections.append(selection)
                        print(f"    ✓ Selected: {home_team} Over 0.5 @ {home_team_over_05} (prob: {ml_home_over_05_prob:.2f})")
                        continue  # Only one team over 0.5 bet per match
                    else:
                        print(f"    ✗ Rejected home_over_05: odds={home_team_over_05:.2f} (min {TEAM_OVER_05_MIN_ODDS}) or prob={ml_home_over_05_prob:.3f} (min {MIN_ML_PROBABILITY})")
                
                # Check for away team over 0.5 bet
                if ml_away_over_05_value == 1 and away_team_over_05 is not None:
                    if away_team_over_05 >= TEAM_OVER_05_MIN_ODDS and ml_away_over_05_prob >= MIN_ML_PROBABILITY:
                        selection = {
                            'game': game,
                            'bet_type': 'away_over_05',
                            'odds': away_team_over_05,
                            'ml_probability': ml_away_over_05_prob,
                            'ml_value': ml_away_over_05_value,
                            'team': f"{away_team} Over 0.5",
                            'game_url': game.get('game_url'),
                            'match_id': match_id,
                            'direction': 'away'
                        }
                        selections.append(selection)
                        print(f"    ✓ Selected: {away_team} Over 0.5 @ {away_team_over_05} (prob: {ml_away_over_05_prob:.2f})")
                    else:
                        print(f"    ✗ Rejected away_over_05: odds={away_team_over_05:.2f} (min {TEAM_OVER_05_MIN_ODDS}) or prob={ml_away_over_05_prob:.3f} (min {MIN_ML_PROBABILITY})")
            except Exception as e:
                print(f"  ✗ Error processing game for team over 0.5: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return selections

    def has_match_conflict(self, selections):
        """
        Check if selections contain conflicting bets from the same match.
        Conflicts occur when same match has:
        - home_draw + away_over_05 (home vs away conflict)
        - away_draw + home_over_05 (away vs home conflict)
        
        Returns: (has_conflict: bool, conflict_details: str)
        """
        # Group selections by match_id
        matches = {}
        for sel in selections:
            match_id = sel.get('match_id')
            if not match_id:
                continue
            if match_id not in matches:
                matches[match_id] = []
            matches[match_id].append(sel)
        
        # Check each match for conflicts
        for match_id, match_selections in matches.items():
            if len(match_selections) < 2:
                continue  # No conflict possible with single selection
            
            directions = [sel.get('direction') for sel in match_selections if sel.get('direction')]
            
            # Check for home vs away conflict
            has_home = 'home' in directions
            has_away = 'away' in directions
            
            if has_home and has_away:
                bet_types = [sel.get('bet_type') for sel in match_selections]
                game = match_selections[0].get('game', {})
                home_team = game.get('home_team', 'Unknown')
                away_team = game.get('away_team', 'Unknown')
                return True, f"Conflict in {home_team} vs {away_team}: {', '.join(bet_types)}"
        
        return False, None

    def group_into_tickets(self, selections, max_per_ticket=MAX_SELECTIONS_PER_TICKET):
        """
        Group selections into tickets of up to max_per_ticket selections.
        Prevents conflicting selections from the same match in the same ticket.
        Creates tickets with 1, 2, or 3 selections (up to max_per_ticket).
        Examples:
        - 1 selection -> 1 ticket with 1 selection
        - 2 selections -> 1 ticket with 2 selections
        - 3 selections -> 1 ticket with 3 selections
        - 4 selections -> 2 tickets: [3 selections, 1 selection]
        - 5 selections -> 2 tickets: [3 selections, 2 selections]
        """
        tickets = []
        
        if not selections:
            return tickets
        
        # Group selections into tickets (each ticket can have 1 to max_per_ticket selections)
        for i in range(0, len(selections), max_per_ticket):
            ticket_selections = []
            
            # Try to fill ticket with up to max_per_ticket selections
            for j in range(i, min(i + max_per_ticket, len(selections))):
                candidate = selections[j]
                test_selections = ticket_selections + [candidate]
                
                # Check for conflicts
                has_conflict, conflict_msg = self.has_match_conflict(test_selections)
                
                if has_conflict:
                    print(f"  ⚠ Skipping selection due to match conflict: {candidate.get('team')}")
                    print(f"    Conflict: {conflict_msg}")
                    # Try next selection if we haven't filled the ticket yet
                    if len(ticket_selections) > 0:
                        break  # Ticket is full enough, create it
                    continue  # Skip this selection and try next
                else:
                    ticket_selections.append(candidate)
            
            if not ticket_selections:
                continue  # Skip empty tickets
            
            # Calculate combined odds
            combined_odds = 1.0
            for sel in ticket_selections:
                combined_odds *= sel['odds']
            
            ticket = {
                'ticket_id': str(uuid.uuid4()),
                'selections': ticket_selections,
                'combined_odds': round(combined_odds, 2),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'pending'
            }
            tickets.append(ticket)
        
        return tickets

    def place_double_chance_bet(self, page, selection):
        """Place a single double chance bet (home_draw or away_draw)"""
        game_url = selection.get('game_url')
        bet_type = selection.get('bet_type')
        game = selection.get('game')
        
        if not game_url:
            print(f"    ✗ No game URL for {selection.get('team')}")
            return False
        
        try:
            print(f"    Navigating to: {game_url}")
            page.goto(game_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(2)
            
            # Wait for markets to load
            page.wait_for_selector("div.flex.flex-col.gap-3", timeout=10000)
            time.sleep(1)
            
            # Find all market sections
            market_sections = page.locator("details").all()
            bet_clicked = False
            
            for market in market_sections:
                try:
                    summary_text = market.locator("summary").inner_text().strip()
                    
                    # Look for Double Chance market
                    if "Double Chance" in summary_text:
                        print(f"    ✓ Found Double Chance market")
                        # Double Chance has 3 options in a grid-cols-3 layout
                        odds_grid = market.locator("div.grid.grid-cols-3").first
                        if odds_grid.count() == 0:
                            # Try alternative selector with more specific classes
                            odds_grid = market.locator("div.grid.p-1.rounded-b-lg.shadow-sm.bg-light-50.gap-1.dark\\:bg-dark-800.grid-cols-3").first
                        
                        if odds_grid.count() > 0:
                            odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                            
                            # Double Chance market has 3 options: Home/Draw, Home/Away, Draw/Away
                            # We need to identify by text content, not position
                            home_team = (game.get('home_team') or '').lower()
                            away_team = (game.get('away_team') or '').lower()
                            
                            for item in odds_items:
                                try:
                                    label_div = item.locator("div").first
                                    if label_div.count() > 0:
                                        item_text = label_div.inner_text().strip()
                                        item_text_lower = item_text.lower()
                                        
                                        # Check if this is the bet we want based on text content
                                        is_match = False
                                        
                                        if bet_type == 'home_draw':
                                            # Match: "Home Team Or Draw" or "Home Team or Draw" or "1X"
                                            # The text format is typically: "West Bromwich Albion Or Draw"
                                            # Must have home_team and "draw", but NOT away_team (to exclude home_away)
                                            is_match = False
                                            if home_team and "draw" in item_text_lower:
                                                has_home = home_team in item_text_lower
                                                has_away = away_team and away_team in item_text_lower
                                                has_draw = "draw" in item_text_lower
                                                # home_draw: has home + draw, but NOT away
                                                is_match = has_home and has_draw and not has_away
                                            
                                            # Also check for shorthand notation
                                            if not is_match:
                                                is_match = (
                                                    ("1x" in item_text_lower)
                                                    or ("home/draw" in item_text_lower)
                                                )
                                        elif bet_type == 'away_draw':
                                            # Match: "Draw Or Away Team" or "Draw or Away Team" or "X2"
                                            # The text format is typically: "Draw Or Middlesbrough FC"
                                            # Must have away_team and "draw", but NOT home_team (to exclude home_away)
                                            is_match = False
                                            if away_team and "draw" in item_text_lower:
                                                has_home = home_team and home_team in item_text_lower
                                                has_away = away_team in item_text_lower
                                                has_draw = "draw" in item_text_lower
                                                # away_draw: has away + draw, but NOT home
                                                is_match = has_away and has_draw and not has_home
                                            
                                            # Also check for shorthand notation
                                            if not is_match:
                                                is_match = (
                                                    ("x2" in item_text_lower)
                                                    or ("draw/away" in item_text_lower)
                                                )
                                        
                                        if is_match:
                                            print(f"    ✓ Found {bet_type} option: {item_text}")
                                            bet_button = item
                                            bet_button.scroll_into_view_if_needed()
                                            time.sleep(0.5)
                                            bet_button.click()
                                            print(f"    ✓ Bet clicked: {bet_type}")
                                            time.sleep(1.5)
                                            bet_clicked = True
                                            break
                                except Exception as e:
                                    print(f"    ⚠ Error checking item: {str(e)}")
                                    continue
                            
                            if bet_clicked:
                                break
                except Exception as e:
                    print(f"    ⚠ Error processing market: {str(e)}")
                    continue
            
            if not bet_clicked:
                print(f"    ✗ Could not find/click Double Chance bet for {bet_type}")
                return False
            
            return True
            
        except Exception as e:
            print(f"    ✗ Error placing double chance bet: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def place_team_over_05_bet(self, page, selection):
        """Place a single team over 0.5 bet"""
        game_url = selection.get('game_url')
        bet_type = selection.get('bet_type')
        game = selection.get('game')
        team_name = game.get('home_team') if bet_type == 'home_over_05' else game.get('away_team')
        
        if not game_url:
            print(f"    ✗ No game URL for {selection.get('team')}")
            return False
        
        try:
            print(f"    Navigating to: {game_url}")
            page.goto(game_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(2)
            
            # Wait for markets to load
            page.wait_for_selector("div.flex.flex-col.gap-3", timeout=10000)
            time.sleep(1)
            
            bet_clicked = False
            
            # First, try to find team-specific markets directly without search
            try:
                all_markets = page.locator("details").all()
                for market in all_markets:
                    try:
                        summary_text = market.locator("summary").inner_text().strip()
                        
                        # Check for team-specific Total (0.5) market
                        if team_name and team_name in summary_text and "Total (0.5)" in summary_text and "1st Half" not in summary_text and "2nd Half" not in summary_text:
                            print(f"    ✓ Found {team_name} Total (0.5) market")
                            odds_grid = market.locator("div.grid.grid-cols-2").first
                            if odds_grid.count() > 0:
                                odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                                for item in odds_items:
                                    label_div = item.locator("div").first
                                    if label_div.count() > 0:
                                        item_text = label_div.inner_text().strip()
                                        if "Over" in item_text and "(0.5)" in item_text:
                                            print(f"    ✓ Found Over (0.5) option")
                                            bet_button = item
                                            bet_button.scroll_into_view_if_needed()
                                            time.sleep(0.5)
                                            bet_button.click()
                                            print(f"    ✓ Bet clicked: {team_name} Over 0.5")
                                            time.sleep(1.5)
                                            bet_clicked = True
                                            break
                            if bet_clicked:
                                break
                    except Exception as e:
                        continue
            except Exception as e:
                print(f"    ⚠ Error finding team market directly: {str(e)}")
            
            # If not found directly, try using search
            if not bet_clicked and team_name:
                try:
                    # Click search button
                    search_button = page.locator("div.flex.gap-2.sticky div.flex.items-center.justify-center.rounded-lg.cursor-pointer.bg-dark-800.w-9.h-9").first
                    if search_button.count() > 0:
                        search_button.click()
                        time.sleep(0.5)
                        
                        # Find and fill search input
                        search_input = page.locator("input.w-full.px-2.pr-8.text-xs.border.rounded-lg").first
                        if search_input.count() == 0:
                            search_input = page.locator("div.absolute.top-1\\/2 input").first
                        
                        if search_input.count() > 0:
                            search_input.fill(team_name)
                            time.sleep(1.5)
                            
                            # Wait for filtered market to appear
                            time.sleep(1)
                            
                            # Find all markets and check for team-specific Total market
                            all_markets = page.locator("details").all()
                            for market in all_markets:
                                summary_text = market.locator("summary").inner_text().strip()
                                if team_name in summary_text and "Total (0.5)" in summary_text and "1st Half" not in summary_text and "2nd Half" not in summary_text:
                                    odds_grid = market.locator("div.grid.grid-cols-2").first
                                    if odds_grid.count() > 0:
                                        odds_items = odds_grid.locator("div.flex.items-center.justify-between").all()
                                        for item in odds_items:
                                            label_div = item.locator("div").first
                                            if label_div.count() > 0:
                                                item_text = label_div.inner_text().strip()
                                                if "Over" in item_text and "(0.5)" in item_text:
                                                    bet_button = item
                                                    bet_button.scroll_into_view_if_needed()
                                                    time.sleep(0.5)
                                                    bet_button.click()
                                                    print(f"    ✓ Bet clicked: {team_name} Over 0.5")
                                                    time.sleep(1.5)
                                                    bet_clicked = True
                                                    break
                                    if bet_clicked:
                                        break
                            
                            # Clear search
                            try:
                                search_input.fill("")
                                time.sleep(0.5)
                                search_button.click()
                                time.sleep(0.5)
                            except:
                                pass
                except Exception as e:
                    print(f"    ⚠ Error using search: {str(e)}")
            
            if not bet_clicked:
                print(f"    ✗ Could not find/click Team Over 0.5 bet for {team_name}")
                return False
            
            return True
            
        except Exception as e:
            print(f"    ✗ Error placing team over 0.5 bet: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def place_bets_for_ticket(self, page, ticket, market_type):
        """Place all bets for a single ticket"""
        print(f"\n  Placing bets for ticket {ticket['ticket_id'][:8]}...")
        print(f"    Selections: {len(ticket['selections'])}")
        print(f"    Combined odds: {ticket['combined_odds']}")
        
        placed_count = 0
        for i, selection in enumerate(ticket['selections'], 1):
            print(f"\n    [{i}/{len(ticket['selections'])}] {selection.get('team')} @ {selection.get('odds')}")
            
            if market_type == 'double_chance':
                success = self.place_double_chance_bet(page, selection)
            elif market_type == 'team_over_05':
                success = self.place_team_over_05_bet(page, selection)
            else:
                print(f"    ✗ Unknown market type: {market_type}")
                success = False
            
            if success:
                placed_count += 1
                print(f"    ✓ Bet {i} placed successfully")
            else:
                print(f"    ✗ Bet {i} failed")
        
        ticket['status'] = 'placed' if placed_count == len(ticket['selections']) else 'partial'
        ticket['placed_count'] = placed_count
        return placed_count == len(ticket['selections'])

    def click_bet_now(self, page):
        """Click the Bet Now button to place the betslip"""
        print(f"\n=== CLICKING BET NOW ===")
        try:
            print("Step 1: Navigating back to main page...")
            page.goto("https://betway.co.za/sport/soccer", timeout=60000, wait_until="domcontentloaded")
            print("  ✓ Navigation completed")
            time.sleep(2)
            
            print("Step 2: Waiting for betslip to update...")
            time.sleep(2)
            
            print("Step 3: Looking for Bet Now button...")
            time.sleep(1)
            
            # Try to wait for the button to appear
            try:
                page.wait_for_selector('button[aria-label="Bet Now"]', timeout=5000, state="visible")
                print("  ✓ Bet Now button appeared")
            except:
                print("  ⚠ Bet Now button did not appear within timeout, continuing search...")
            
            # Find and click the "Bet Now" button
            bet_now_button = None
            
            # Try by aria-label first
            bet_now_button = page.locator('button[aria-label="Bet Now"]')
            if bet_now_button.count() > 0:
                if bet_now_button.first.is_visible():
                    print("    ✓ Button is visible")
                else:
                    bet_now_button = None
            
            if bet_now_button is None or (hasattr(bet_now_button, 'count') and bet_now_button.count() == 0):
                bet_now_button = page.locator('button.p-button.bg-identity').filter(has_text="Bet Now")
            
            if bet_now_button is None or (hasattr(bet_now_button, 'count') and bet_now_button.count() == 0):
                bet_now_button = page.locator('button:has-text("Bet Now")')
            
            if bet_now_button is None or (hasattr(bet_now_button, 'count') and bet_now_button.count() == 0):
                bet_now_button = page.locator('#betslip-strike-btn')
            
            if bet_now_button is None or (hasattr(bet_now_button, 'count') and bet_now_button.count() == 0):
                all_buttons = page.locator('button').all()
                for btn in all_buttons[:10]:
                    try:
                        btn_text = btn.inner_text().strip()
                        if "Bet Now" in btn_text:
                            bet_now_button = btn
                            break
                    except:
                        continue
            
            # Check if we found a button
            button_found = False
            if bet_now_button is not None:
                if hasattr(bet_now_button, 'count'):
                    button_found = bet_now_button.count() > 0
                else:
                    button_found = True
            
            if button_found:
                print("  ✓ Bet Now button found")
                try:
                    if hasattr(bet_now_button, 'first'):
                        btn_to_click = bet_now_button.first
                    elif hasattr(bet_now_button, 'count') and bet_now_button.count() > 0:
                        btn_to_click = bet_now_button.first
                    else:
                        btn_to_click = bet_now_button
                    
                    btn_to_click.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    
                    print("  Clicking first Bet Now button (opens modal)...")
                    btn_to_click.click()
                    print("  ✓ First Bet Now button clicked")
                    time.sleep(2)
                    
                    # Wait for modal and click second Bet Now button
                    print("Step 4: Looking for Bet Now button inside modal...")
                    try:
                        page.wait_for_selector('#betslip-strike-btn', timeout=10000, state="visible")
                        print("  ✓ Modal appeared, Bet Now button found")
                        
                        modal_bet_now = page.locator('#betslip-strike-btn')
                        if modal_bet_now.count() > 0:
                            print("  Clicking Bet Now button inside modal...")
                            modal_bet_now.click()
                            print("  ✓ Bet Now button in modal clicked - Bet placed!")
                            time.sleep(3)
                            return True
                        else:
                            print("  ✗ Bet Now button in modal not found")
                    except Exception as modal_error:
                        print(f"  ⚠ Error finding/clicking modal button: {str(modal_error)}")
                        try:
                            modal_bet_now = page.locator('button[aria-label="Bet Now"]#betslip-strike-btn')
                            if modal_bet_now.count() > 0:
                                modal_bet_now.click()
                                print("  ✓ Bet Now button in modal clicked via alternative selector")
                                time.sleep(3)
                                return True
                        except Exception as e2:
                            print(f"  ✗ Error with alternative selector: {str(e2)}")
                except Exception as click_error:
                    print(f"  ✗ Error clicking button: {str(click_error)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("  ✗ Bet Now button not found")
            
            return False
            
        except Exception as e:
            print(f"  ✗ Error clicking Bet Now: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def save_betting_tickets(self, tickets, market_type, date_str):
        """Save comprehensive ticket information to JSON file"""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(project_root, "betting_data")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"betting_tickets_{date_str}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Prepare ticket data with all required information
        ticket_data = {
            'date': date_str,
            'market_type': market_type,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tickets': []
        }
        
        for ticket in tickets:
            ticket_info = {
                'ticket_id': ticket.get('ticket_id'),
                'market_type': market_type,
                'selections': [],
                'combined_odds': ticket.get('combined_odds'),
                'timestamp': ticket.get('timestamp'),
                'status': ticket.get('status'),
                'placed_count': ticket.get('placed_count', 0)
            }
            
            for selection in ticket.get('selections', []):
                selection_info = {
                    'bet_type': selection.get('bet_type'),
                    'team': selection.get('team'),
                    'odds': selection.get('odds'),
                    'ml_probability': selection.get('ml_probability'),
                    'ml_value': selection.get('ml_value'),
                    'game_url': selection.get('game_url'),
                    'game_data': selection.get('game', {})
                }
                ticket_info['selections'].append(selection_info)
            
            ticket_data['tickets'].append(ticket_info)
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(ticket_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Betting tickets saved to: {filepath}")
        print(f"  Total tickets: {len(tickets)}")
        return filepath

    def run(self, date_str=None):
        """Main automation flow with ML-based betting"""
        print("=== STARTING BETWAY AUTOMATION ===")
        
        # Use provided date or default to tomorrow
        if date_str is None:
            SAST = timezone(timedelta(hours=2))
            tomorrow_sast = datetime.now(SAST) + timedelta(days=1)
            date_str = tomorrow_sast.strftime("%Y-%m-%d")
        
        user_agent = getattr(
            settings,
            "PLAYWRIGHT_USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36"
        )
        print(f"✓ User agent configured: {user_agent[:50]}...")
        print(f"✓ Date: {date_str}")

        print("\n[STEP 1] Launching browser...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            print("✓ Browser launched")
            
            context = browser.new_context(user_agent=user_agent)
            print("✓ Browser context created")
            
            page = context.new_page()
            print("✓ New page created")

            print("\n[STEP 2] Navigating to Betway Soccer page...")
            page.goto(
                "https://betway.co.za/sport/soccer",
                timeout=60000,
                wait_until="domcontentloaded",
            )
            print("✓ Page loaded")

            print("\n[STEP 3] Logging in...")
            page.wait_for_selector("#login-btn", timeout=30000)
            page.click("#login-btn")
            print("✓ Login button clicked")
            
            page.wait_for_selector("#login-mobile", timeout=10000)
            page.wait_for_selector("#login-password", timeout=10000)
            time.sleep(0.5)
            
            page.fill("#login-mobile", "606932969")
            page.fill("#login-password", "59356723")
            print("✓ Login form filled")
            
            submit_button = page.locator('button[type="submit"][aria-label="Login"]')
            if submit_button.count() > 0:
                submit_button.click()
                print("✓ Submit button clicked")
            
            try:
                page.wait_for_selector("#login-mobile", state="hidden", timeout=10000)
                print("✓ Login modal disappeared")
            except Exception as e:
                print(f"⚠ Modal didn't disappear: {str(e)}")
            
            time.sleep(3)
            print("✓ Login completed")

            print("\n[STEP 4] Loading predictions file...")
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            predictions_file = os.path.join(project_root, "betting_data", f"predictions_{date_str}.json")
            
            if not os.path.exists(predictions_file):
                print(f"✗ Predictions file not found: {predictions_file}")
                print("  Trying alternative: combined file...")
                predictions_file = os.path.join(project_root, "betting_data", f"combined_{date_str}.json")
            
            if not os.path.exists(predictions_file):
                print(f"✗ Predictions file not found: {predictions_file}")
                context.close()
                browser.close()
                return None
            
            print(f"✓ Loading predictions from: {predictions_file}")
            with open(predictions_file, 'r', encoding='utf-8') as f:
                all_games = json.load(f)
            print(f"✓ Loaded {len(all_games)} games")

            # Process Double Chance bets
            print("\n[STEP 5] Processing Double Chance bets...")
            print("=" * 60)
            double_chance_selections = self.select_double_chance_bets(all_games)
            print(f"\n✓ Selected {len(double_chance_selections)} Double Chance bets")
            
            if double_chance_selections:
                double_chance_tickets = self.group_into_tickets(double_chance_selections)
                print(f"✓ Grouped into {len(double_chance_tickets)} tickets")
                for ticket_idx, ticket in enumerate(double_chance_tickets, 1):
                    print(f"  Ticket {ticket_idx}: {len(ticket['selections'])} selection(s)")
                
                for ticket_idx, ticket in enumerate(double_chance_tickets, 1):
                    print(f"\n--- Ticket {ticket_idx}/{len(double_chance_tickets)} ({len(ticket['selections'])} selections) ---")
                    success = self.place_bets_for_ticket(page, ticket, 'double_chance')
                    
                    if success:
                        # Click Bet Now after placing all bets in ticket
                        print(f"\n  Clicking Bet Now for ticket {ticket_idx}...")
                        bet_placed = self.click_bet_now(page)
                        if bet_placed:
                            ticket['status'] = 'placed'
                            print(f"  ✓ Ticket {ticket_idx} bet placed successfully")
                        else:
                            ticket['status'] = 'pending'
                            print(f"  ⚠ Ticket {ticket_idx} bet placement failed")
                        
                        # Wait before next ticket (if any)
                        if ticket_idx < len(double_chance_tickets):
                            print(f"  Waiting before next ticket...")
                            time.sleep(3)
                    else:
                        ticket['status'] = 'failed'
                        print(f"  ✗ Ticket {ticket_idx} failed to place bets")
                
                # Save tickets
                self.save_betting_tickets(double_chance_tickets, 'double_chance', date_str)
            else:
                print("⚠ No eligible Double Chance bets found")

            # Process Team Over 0.5 bets
            print("\n[STEP 6] Processing Team Over 0.5 bets...")
            print("=" * 60)
            team_over_05_selections = self.select_team_over_05_bets(all_games)
            print(f"\n✓ Selected {len(team_over_05_selections)} Team Over 0.5 bets")
            
            if team_over_05_selections:
                team_over_05_tickets = self.group_into_tickets(team_over_05_selections)
                print(f"✓ Grouped into {len(team_over_05_tickets)} tickets")
                for ticket_idx, ticket in enumerate(team_over_05_tickets, 1):
                    print(f"  Ticket {ticket_idx}: {len(ticket['selections'])} selection(s)")
                
                for ticket_idx, ticket in enumerate(team_over_05_tickets, 1):
                    print(f"\n--- Ticket {ticket_idx}/{len(team_over_05_tickets)} ({len(ticket['selections'])} selections) ---")
                    success = self.place_bets_for_ticket(page, ticket, 'team_over_05')
                    
                    if success:
                        # Click Bet Now after placing all bets in ticket
                        print(f"\n  Clicking Bet Now for ticket {ticket_idx}...")
                        bet_placed = self.click_bet_now(page)
                        if bet_placed:
                            ticket['status'] = 'placed'
                            print(f"  ✓ Ticket {ticket_idx} bet placed successfully")
                        else:
                            ticket['status'] = 'pending'
                            print(f"  ⚠ Ticket {ticket_idx} bet placement failed")
                        
                        # Wait before next ticket (if any)
                        if ticket_idx < len(team_over_05_tickets):
                            print(f"  Waiting before next ticket...")
                            time.sleep(3)
                    else:
                        ticket['status'] = 'failed'
                        print(f"  ✗ Ticket {ticket_idx} failed to place bets")
                
                # Save tickets
                self.save_betting_tickets(team_over_05_tickets, 'team_over_05', date_str)
            else:
                print("⚠ No eligible Team Over 0.5 bets found")

            print("\n[STEP 7] Final delay before closing...")
            time.sleep(10)
            print("✓ Delay completed")

            print("\n[STEP 8] Closing browser...")
            context.close()
            browser.close()
            print("✓ Browser closed")
            
            print("\n=== AUTOMATION COMPLETED ===")
            return True
