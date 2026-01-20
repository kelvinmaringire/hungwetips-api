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
        Load combined tips & odds file.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            List of dictionaries containing tips & odds data
        """
        file_path = self.data_dir / f'combined_{date_str}.json'
        if not file_path.exists():
            raise FileNotFoundError(f"Combined tips file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_results(self, date_str):
        """
        Load results file.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Dictionary mapping match_id to result data
        """
        file_path = self.data_dir / f'forebet_results_{date_str}.json'
        if not file_path.exists():
            raise FileNotFoundError(f"Results file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Create a dictionary indexed by match_id for quick lookup
        results_dict = {}
        for result in results:
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
            match_id = tip.get('forebet_match_id')
            
            # Create a copy of the tip data
            merged_tip = tip.copy()
            
            # Add match_id field for consistency
            merged_tip['match_id'] = match_id
            
            # Add normalized field names for compatibility (map forebet_* fields)
            if 'forebet_pred' in merged_tip:
                merged_tip['pred'] = merged_tip.get('forebet_pred')
            if 'forebet_home_pred_score' in merged_tip:
                merged_tip['home_pred_score'] = merged_tip.get('forebet_home_pred_score')
            if 'forebet_away_pred_score' in merged_tip:
                merged_tip['away_pred_score'] = merged_tip.get('forebet_away_pred_score')
            if 'forebet_prob_1' in merged_tip:
                merged_tip['prob_1'] = merged_tip.get('forebet_prob_1')
            if 'forebet_prob_x' in merged_tip:
                merged_tip['prob_x'] = merged_tip.get('forebet_prob_x')
            if 'forebet_prob_2' in merged_tip:
                merged_tip['prob_2'] = merged_tip.get('forebet_prob_2')
            if 'forebet_avg_goals' in merged_tip:
                merged_tip['avg_goals'] = merged_tip.get('forebet_avg_goals')
            if 'forebet_kelly' in merged_tip:
                merged_tip['kelly'] = merged_tip.get('forebet_kelly')
            if 'forebet_game_link' in merged_tip:
                merged_tip['game_link'] = merged_tip.get('forebet_game_link')
            if 'forebet_preview_link' in merged_tip:
                merged_tip['preview_link'] = merged_tip.get('forebet_preview_link')
            if 'forebet_country' in merged_tip:
                merged_tip['country'] = merged_tip.get('forebet_country')
            if 'forebet_league_name' in merged_tip:
                merged_tip['league_name'] = merged_tip.get('forebet_league_name')
            
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
        Merge tips with results and save to file.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            output_filename: Optional custom output filename. Defaults to merged_YYYY-MM-DD.json
            
        Returns:
            Path to the saved output file
        """
        merged_data = self.merge(date_str)
        
        # Determine output filename
        if output_filename:
            output_path = self.data_dir / output_filename
        else:
            output_path = self.data_dir / f'merged_{date_str}.json'
        
        # Save merged data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
        
        return output_path

