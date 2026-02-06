import json
import os
from typing import List, Dict, Optional, Tuple
from rapidfuzz import fuzz


class BetwayForebetMatcher:
    """Match Betway odds with Forebet tips using fuzzy string matching"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the matcher
        
        Args:
            data_dir: Directory containing JSON files. If None, uses betting_data directory
        """
        if data_dir is None:
            # Get project root (assuming we're in betting_engine/services/)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(project_root, "betting_data")
        self.data_dir = data_dir
    
    def normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for better matching"""
        if not team_name:
            return ""
        # Remove common suffixes and normalize
        normalized = team_name.strip()
        # Remove common suffixes
        suffixes = [" FC"," FC."," F.C."," AFC"," A.F.C."," CF"," C.F."," CD"," C.D."," UD"," U.D."," SD"," S.D."," AC"," A.C."," AS"," A.S."," SC"," S.C."," SV"," VfB"," VfL"," FK"," NK"," SK"]

        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        return normalized
    
    def match_teams(self, team1: str, team2: str, threshold: int = 75) -> Tuple[bool, float]:
        """
        Match two team names using fuzzy string matching
        
        Args:
            team1: First team name
            team2: Second team name
            threshold: Minimum similarity score (0-100) to consider a match
            
        Returns:
            Tuple of (is_match, similarity_score)
        """
        if not team1 or not team2:
            return False, 0.0
        
        # Try exact match first
        if team1.lower() == team2.lower():
            return True, 100.0
        
        # Try normalized match
        norm1 = self.normalize_team_name(team1)
        norm2 = self.normalize_team_name(team2)
        if norm1.lower() == norm2.lower():
            return True, 100.0
        
        # Use RapidFuzz for fuzzy matching
        # Try ratio (overall similarity)
        ratio_score = fuzz.ratio(team1.lower(), team2.lower())
        
        # Try partial ratio (handles substrings better)
        partial_score = fuzz.partial_ratio(team1.lower(), team2.lower())
        
        # Try token sort ratio (handles word order differences)
        token_sort_score = fuzz.token_sort_ratio(team1.lower(), team2.lower())
        
        # Use the best score
        best_score = max(ratio_score, partial_score, token_sort_score)
        
        is_match = best_score >= threshold
        return is_match, best_score
    
    def match_games(self, betway_game: Dict, forebet_tips: List[Dict], threshold: int = 75) -> Optional[Dict]:
        """
        Find the best matching Forebet tip for a Betway game
        
        Args:
            betway_game: Game data from Betway
            forebet_tips: List of Forebet tips
            threshold: Minimum similarity score to consider a match
            
        Returns:
            Best matching Forebet tip or None
        """
        betway_home = betway_game.get('home_team', '')
        betway_away = betway_game.get('away_team', '')
        
        if not betway_home or not betway_away:
            return None
        
        best_match = None
        best_score = 0.0
        
        for tip in forebet_tips:
            forebet_home = tip.get('home_team', '')
            forebet_away = tip.get('away_team', '')
            
            if not forebet_home or not forebet_away:
                continue
            
            # Match both home and away teams
            home_match, home_score = self.match_teams(betway_home, forebet_home, threshold)
            away_match, away_score = self.match_teams(betway_away, forebet_away, threshold)
            
            # Both teams must match
            if home_match and away_match:
                # Average score for overall match quality
                avg_score = (home_score + away_score) / 2.0
                if avg_score > best_score:
                    best_score = avg_score
                    best_match = tip
        
        return best_match
    
    def combine_data(self, betway_data: List[Dict], forebet_data: List[Dict], 
                    threshold: int = 75) -> List[Dict]:
        """
        Combine Betway odds with Forebet tips
        Only includes games that have a match from both Betway and Forebet
        
        Args:
            betway_data: List of Betway game data
            forebet_data: List of Forebet tips
            threshold: Minimum similarity score to consider a match
            
        Returns:
            List of combined game data (only matched games)
        """
        combined = []
        matched_forebet_ids = set()
        
        for betway_game in betway_data:
            matched_tip = self.match_games(betway_game, forebet_data, threshold)
            
            # Only process if we found a match
            if not matched_tip:
                continue
            
            # Create combined game data
            combined_game = {
                # Betway data
                **betway_game,
                # Forebet data (guaranteed to have match)
                'forebet_match_id': matched_tip.get('match_id'),
                'forebet_country': matched_tip.get('country'),
                'forebet_league_name': matched_tip.get('league_name'),
                'forebet_preview_link': matched_tip.get('preview_link'),
                'forebet_game_link': matched_tip.get('game_link'),
                'forebet_prob_1': matched_tip.get('prob_1'),
                'forebet_prob_x': matched_tip.get('prob_x'),
                'forebet_prob_2': matched_tip.get('prob_2'),
                'forebet_pred': matched_tip.get('pred'),
                'forebet_home_pred_score': matched_tip.get('home_pred_score'),
                'forebet_away_pred_score': matched_tip.get('away_pred_score'),
                'forebet_avg_goals': matched_tip.get('avg_goals'),
                'forebet_kelly': matched_tip.get('kelly'),
                'match_confidence': None,  # Will be calculated below
            }
            
            # Calculate match confidence
            betway_home = betway_game.get('home_team', '')
            betway_away = betway_game.get('away_team', '')
            forebet_home = matched_tip.get('home_team', '')
            forebet_away = matched_tip.get('away_team', '')
            
            _, home_score = self.match_teams(betway_home, forebet_home, 0)
            _, away_score = self.match_teams(betway_away, forebet_away, 0)
            combined_game['match_confidence'] = round((home_score + away_score) / 2.0, 2)
            matched_forebet_ids.add(matched_tip.get('match_id'))
            
            combined.append(combined_game)
        
        return combined
    
    
    def match_and_save(self, date_str: str, threshold: int = 75, 
                      output_filename: Optional[str] = None) -> str:
        """
        Load Betway and Forebet data from database, match them, and save combined data to database
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            threshold: Minimum similarity score to consider a match
            output_filename: Optional (kept for compatibility, not used)
            
        Returns:
            String "DB" indicating data was saved to database
        """
        # Load Betway data from database
        from datetime import datetime
        from betting_engine.models import BetwayOdds, ForebetTip
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        betway_odds = BetwayOdds.objects.using('default').filter(date=date_obj).first()
        
        if not betway_odds:
            raise FileNotFoundError(f"No Betway odds found for {date_str}. Run scrape_betway first.")
        
        betway_data = betway_odds.matches
        if not isinstance(betway_data, list):
            raise ValueError(f"Betway odds matches field is not a list for {date_str}")
        
        # Load Forebet data from database
        forebet_tip = ForebetTip.objects.using('default').filter(date=date_obj).first()
        
        if not forebet_tip:
            raise FileNotFoundError(f"No Forebet tips found for {date_str}. Run scrape_forebet first.")
        
        # Get tips from JSONField
        forebet_data = forebet_tip.tips
        if not isinstance(forebet_data, list):
            raise ValueError(f"ForebetTip tips field is not a list for {date_str}")
        
        # Combine data
        combined_data = self.combine_data(betway_data, forebet_data, threshold)
        
        # Save to database
        try:
            from betting_engine.importers import import_combined_matches
            db_result = import_combined_matches(date_obj, combined_data)
            print(f"Database: Created {db_result['created']}, Updated {db_result['updated']}")
        except Exception as e:
            print(f"⚠ Database save failed: {str(e)}")
            raise
        
        return "DB"

