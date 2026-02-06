import json
import os
from pathlib import Path


class MergeYesterdayResults:
    """
    Service to merge yesterday's combined tips & odds with results.
    Combines data from combined_YYYY-MM-DD.json and forebet_results_YYYY-MM-DD.json
    using forebet_match_id/match_id as the key.
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize the merger.
        
        Args:
            data_dir: Directory containing the JSON files. Defaults to betting_data/
        """
        if data_dir is None:
            # Get the project root (assuming this file is in betting_engine/services/)
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / 'betting_data'
        else:
            self.data_dir = Path(data_dir)
    
    def load_combined_tips(self, date_str):
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
        tips_data = combined_match.matches
        if not isinstance(tips_data, list):
            raise ValueError(f"CombinedMatch matches field is not a list for {date_str}")
        
        return tips_data
    
    def load_results(self, date_str):
        """
        Load results from database.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping match_id to result data
        """
        from datetime import datetime
        from betting_engine.models import ForebetResult
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        forebet_result = ForebetResult.objects.using('default').filter(date=date_obj).first()
        
        if not forebet_result:
            # Return empty dict if no results found
            return {}
        
        # Get results from JSONField
        results_list = forebet_result.results
        if not isinstance(results_list, list):
            return {}
        
        # Create a dictionary indexed by match_id for quick lookup
        results_dict = {}
        for result in results_list:
            match_id = result.get('match_id')
            if match_id:
                results_dict[match_id] = result
        
        return results_dict
    
    def merge(self, date_str):
        """
        Merge combined tips & odds with results.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            List of merged dictionaries
        """
        # Load both files
        tips_data = self.load_combined_tips(date_str)
        results_dict = self.load_results(date_str)
        
        merged_data = []
        
        for tip in tips_data:
            # Get the match_id from the tip (it's called forebet_match_id in combined file)
            match_id = tip.get('forebet_match_id') or tip.get('match_id')
            
            # Create a copy of the tip data
            merged_tip = tip.copy()
            
            # Keep only one set of identifiers/prediction fields
            field_map = {
                'forebet_match_id': 'match_id',
                'forebet_pred': 'pred',
                'forebet_home_pred_score': 'home_pred_score',
                'forebet_away_pred_score': 'away_pred_score',
                'forebet_prob_1': 'prob_1',
                'forebet_prob_x': 'prob_x',
                'forebet_prob_2': 'prob_2',
                'forebet_avg_goals': 'avg_goals',
                'forebet_kelly': 'kelly',
                'forebet_game_link': 'game_link',
                'forebet_preview_link': 'preview_link',
                'forebet_country': 'country',
                'forebet_league_name': 'league_name',
            }

            for forebet_key, normalized_key in field_map.items():
                if forebet_key in merged_tip and normalized_key not in merged_tip:
                    merged_tip[normalized_key] = merged_tip.get(forebet_key)
                if forebet_key in merged_tip:
                    del merged_tip[forebet_key]

            # Ensure match_id is set even if only match_id existed
            merged_tip['match_id'] = match_id
            
            # Try to find matching result
            if match_id and match_id in results_dict:
                result = results_dict[match_id]
                # Add result fields to merged tip
                merged_tip['home_correct_score'] = result.get('home_correct_score')
                merged_tip['away_correct_score'] = result.get('away_correct_score')
                merged_tip['home_ht_score'] = result.get('home_ht_score')
                merged_tip['away_ht_score'] = result.get('away_ht_score')
            else:
                # No result found, set to None
                merged_tip['home_correct_score'] = None
                merged_tip['away_correct_score'] = None
                merged_tip['home_ht_score'] = None
                merged_tip['away_ht_score'] = None
            
            merged_data.append(merged_tip)
        
        return merged_data
    
    def merge_and_save(self, date_str, output_filename=None):
        """
        Merge tips with results and save to database.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            output_filename: Optional (kept for compatibility, not used)
            
        Returns:
            String "DB" indicating data was saved to database
        """
        merged_data = self.merge(date_str)
        
        # Save to database
        try:
            from datetime import datetime
            from betting_engine.importers import import_merged_matches
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            db_result = import_merged_matches(date_obj, merged_data)
            print(f"Database: Created {db_result['created']}, Updated {db_result['updated']}")
        except Exception as e:
            print(f"⚠ Database save failed: {str(e)}")
            raise
        
        return "DB"

