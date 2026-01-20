from django.core.management.base import BaseCommand, CommandError
from betting_engine.services.merge_yesterday_results import MergeYesterdayResults
from datetime import datetime, timedelta, timezone
import os


class Command(BaseCommand):
    help = "Merge yesterday's combined tips & odds with results using match_id"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYY-MM-DD format (defaults to yesterday)',
            default=None,
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Custom output filename (default: merged_YYYY-MM-DD.json)',
            default=None,
        )

    def handle(self, *args, **options):
        # Determine date
        if options['date']:
            try:
                date_obj = datetime.strptime(options['date'], '%Y-%m-%d')
                date_str = options['date']
            except ValueError:
                raise CommandError(f"Invalid date format: {options['date']}. Use YYYY-MM-DD format.")
        else:
            # Default to yesterday (SAST timezone)
            SAST = timezone(timedelta(hours=2))
            today_sast = datetime.now(SAST)
            yesterday_sast = today_sast - timedelta(days=1)
            date_str = yesterday_sast.strftime('%Y-%m-%d')
            date_obj = yesterday_sast
        
        self.stdout.write(f"Merging combined tips & odds with results for date: {date_str}")
        
        try:
            merger = MergeYesterdayResults()
            output_path = merger.merge_and_save(
                date_str=date_str,
                output_filename=options['output']
            )
            
            # Load the merged data to show statistics
            import json
            with open(output_path, 'r', encoding='utf-8') as f:
                merged_data = json.load(f)
            
            total_tips = len(merged_data)
            tips_with_results = sum(1 for item in merged_data if item.get('home_correct_score') is not None)
            tips_without_results = total_tips - tips_with_results
            
            self.stdout.write(self.style.SUCCESS(f"\nMerging completed successfully!"))
            self.stdout.write(f"\n=== SUMMARY ===")
            self.stdout.write(f"Total tips: {total_tips}")
            self.stdout.write(f"Tips with results: {tips_with_results}")
            self.stdout.write(f"Tips without results: {tips_without_results}")
            self.stdout.write(f"Match rate: {(tips_with_results/total_tips*100):.1f}%" if total_tips > 0 else "N/A")
            self.stdout.write(f"\nOutput saved to: {output_path}")
            
            # Show sample merged game
            merged_samples = [g for g in merged_data if g.get('home_correct_score') is not None]
            if merged_samples:
                sample = merged_samples[0]
                self.stdout.write(f"\n=== SAMPLE MERGED GAME ===")
                self.stdout.write(f"Match ID: {sample.get('match_id')}")
                self.stdout.write(f"Teams: {sample.get('home_team')} vs {sample.get('away_team')}")
                self.stdout.write(f"Prediction: {sample.get('pred')} ({sample.get('home_pred_score')}-{sample.get('away_pred_score')})")
                self.stdout.write(f"Actual Result: {sample.get('home_correct_score')}-{sample.get('away_correct_score')}")
                self.stdout.write(f"Half-time: {sample.get('home_ht_score')}-{sample.get('away_ht_score')}")
            
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Error during merging: {str(e)}")

