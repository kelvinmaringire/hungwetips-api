import json
from pathlib import Path


class MarketSelector:
    """
    Service to select betting markets based on odds thresholds and Forebet predictions.
    Analyzes combined_YYYY-MM-DD.json files and flags matches that meet betting criteria.
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize the market selector.
        
        Args:
            data_dir: Directory containing the JSON files. Defaults to betting_data/
        """
        if data_dir is None:
            # Get the project root (assuming this file is in betting_engine/services/)
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / 'betting_data'
        else:
            self.data_dir = Path(data_dir)
        
        # Minimum odds thresholds (configurable)
        self.home_over_min_odds = 1.25
        self.away_over_min_odds = 1.30
        self.home_draw_min_odds = 1.35
        self.away_draw_min_odds = 1.30
        self.over_1_5_min_odds = 1.35
    
    def load_combined_data(self, date_str):
        """
        Load combined tips & odds from database.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            List of dictionaries containing tips & odds data
        """
        from datetime import datetime
        from betting_engine.models import CombinedMatch
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        combined_match = CombinedMatch.objects.using('default').filter(date=date_obj).first()
        
        if not combined_match:
            raise FileNotFoundError(f"No combined matches found for {date_str}. Run match_betway_forebet first.")
        
        # Get matches from JSONField
        matches_data = combined_match.matches
        if not isinstance(matches_data, list):
            raise ValueError(f"CombinedMatch matches field is not a list for {date_str}")
        
        return matches_data
    
    def _safe_get(self, match, key, default=None):
        """Safely get value from match dict, handling None/null values."""
        value = match.get(key, default)
        return value if value is not None else default
    
    def select_markets(self, date_str):
        """
        Apply betting conditions to matches and flag qualifying markets.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            List of dictionaries with added boolean flags for each market type
        """
        matches = self.load_combined_data(date_str)
        
        selected_matches = []
        
        for match in matches:
            # Create a copy of the match data
            flagged_match = match.copy()
            
            # Get values with safe handling for None/null
            home_team_over_0_5 = self._safe_get(match, 'home_team_over_0.5', 0)
            away_team_over_0_5 = self._safe_get(match, 'away_team_over_0.5', 0)
            home_draw_odds = self._safe_get(match, 'home_draw_odds', 0)
            away_draw_odds = self._safe_get(match, 'away_draw_odds', 0)
            total_over_1_5 = self._safe_get(match, 'total_over_1.5', 0)
            
            forebet_home_pred_score = self._safe_get(match, 'forebet_home_pred_score', 0)
            forebet_away_pred_score = self._safe_get(match, 'forebet_away_pred_score', 0)
            forebet_prob_1 = self._safe_get(match, 'forebet_prob_1', 0)
            forebet_prob_x = self._safe_get(match, 'forebet_prob_x', 0)
            forebet_prob_2 = self._safe_get(match, 'forebet_prob_2', 0)
            forebet_avg_goals = self._safe_get(match, 'forebet_avg_goals', 0)
            
            # 1. Home Over 0.5 Bet
            home_over_bet = (
                home_team_over_0_5 >= self.home_over_min_odds and
                forebet_home_pred_score >= 1 and
                forebet_home_pred_score >= forebet_away_pred_score
            )
            
            # 2. Away Over 0.5 Bet
            away_over_bet = (
                away_team_over_0_5 >= self.away_over_min_odds and
                forebet_away_pred_score >= 2 and
                forebet_away_pred_score > forebet_home_pred_score
            )
            
            # 3. Home Draw Bet
            home_draw_bet = (
                home_draw_odds >= self.home_draw_min_odds and
                forebet_home_pred_score >= forebet_away_pred_score and
                (forebet_prob_1 + forebet_prob_x) > 70
            )
            
            # 4. Away Draw Bet
            away_draw_bet = (
                away_draw_odds >= self.away_draw_min_odds and
                forebet_away_pred_score > forebet_home_pred_score and
                (forebet_prob_2 + forebet_prob_x) > 70
            )
            
            # 5. Over 1.5 Goals Bet (fixed: was using away_pred_score twice)
            over_1_5_bet = (
                total_over_1_5 >= self.over_1_5_min_odds and
                (forebet_home_pred_score + forebet_away_pred_score) >= 2 and
                forebet_avg_goals > 2
            )
            
            # Add boolean flags to match
            flagged_match['home_over_bet'] = home_over_bet
            flagged_match['away_over_bet'] = away_over_bet
            flagged_match['home_draw_bet'] = home_draw_bet
            flagged_match['away_draw_bet'] = away_draw_bet
            flagged_match['over_1_5_bet'] = over_1_5_bet
            
            selected_matches.append(flagged_match)
        
        return selected_matches
    
    def select_and_save(self, date_str, output_filename=None):
        """
        Select markets and save to database.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            output_filename: Optional (kept for compatibility, not used)
            
        Returns:
            String "DB" indicating data was saved to database
        """
        selected_matches = self.select_markets(date_str)
        
        # Save to database
        try:
            from datetime import datetime
            from betting_engine.importers import import_market_selectors
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            db_result = import_market_selectors(date_obj, selected_matches)
            print(f"Database: Created {db_result['created']}, Updated {db_result['updated']}")
        except Exception as e:
            print(f"⚠ Database save failed: {str(e)}")
            raise
        
        # Print summary statistics
        total_matches = len(selected_matches)
        home_over_count = sum(1 for m in selected_matches if m.get('home_over_bet', False))
        away_over_count = sum(1 for m in selected_matches if m.get('away_over_bet', False))
        home_draw_count = sum(1 for m in selected_matches if m.get('home_draw_bet', False))
        away_draw_count = sum(1 for m in selected_matches if m.get('away_draw_bet', False))
        over_1_5_count = sum(1 for m in selected_matches if m.get('over_1_5_bet', False))
        
        print(f"\nMarket selectors saved to database")
        print(f"  Total matches: {total_matches}")
        print(f"  Home Over 0.5: {home_over_count} matches ({home_over_count/total_matches*100:.2f}%)" if total_matches > 0 else "  Home Over 0.5: 0 matches")
        print(f"  Away Over 0.5: {away_over_count} matches ({away_over_count/total_matches*100:.2f}%)" if total_matches > 0 else "  Away Over 0.5: 0 matches")
        print(f"  Home Draw: {home_draw_count} matches ({home_draw_count/total_matches*100:.2f}%)" if total_matches > 0 else "  Home Draw: 0 matches")
        print(f"  Away Draw: {away_draw_count} matches ({away_draw_count/total_matches*100:.2f}%)" if total_matches > 0 else "  Away Draw: 0 matches")
        print(f"  Over 1.5 Goals: {over_1_5_count} matches ({over_1_5_count/total_matches*100:.2f}%)" if total_matches > 0 else "  Over 1.5 Goals: 0 matches")
        
        return "DB"
