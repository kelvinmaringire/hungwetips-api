from django.core.management.base import BaseCommand, CommandError
from betting_engine.services.betway_forebet_matcher import BetwayForebetMatcher
from datetime import datetime, timedelta, timezone
import os


class Command(BaseCommand):
    help = "Match Betway odds with Forebet tips using fuzzy string matching"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYY-MM-DD format (defaults to tomorrow)',
            default=None,
        )
        parser.add_argument(
            '--threshold',
            type=int,
            help='Minimum similarity score (0-100) to consider a match (default: 85)',
            default=85,
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Custom output filename (default: combined_YYYY-MM-DD.json)',
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
            # Default to tomorrow (SAST timezone)
            SAST = timezone(timedelta(hours=2))
            today_sast = datetime.now(SAST)
            tomorrow_sast = today_sast + timedelta(days=1)
            date_str = tomorrow_sast.strftime('%Y-%m-%d')
            date_obj = tomorrow_sast
        
        # Validate threshold
        threshold = options['threshold']
        if not 0 <= threshold <= 100:
            raise CommandError("Threshold must be between 0 and 100")
        
        self.stdout.write(f"Matching Betway odds with Forebet tips for date: {date_str}")
        self.stdout.write(f"Similarity threshold: {threshold}")
        
        try:
            matcher = BetwayForebetMatcher()
            output_path = matcher.match_and_save(
                date_str=date_str,
                threshold=threshold,
                output_filename=options['output']
            )
            
            # Load the combined data from database to show statistics
            from betting_engine.models import CombinedMatch
            
            combined_match = CombinedMatch.objects.using('default').filter(date=date_obj).first()
            
            if not combined_match:
                raise CommandError(f"No combined matches found for {date_str}")
            
            matches_data = combined_match.matches if isinstance(combined_match.matches, list) else []
            total_games = len(matches_data)
            matched_games = sum(1 for m in matches_data if m.get('forebet_match_id') is not None)
            unmatched_games = total_games - matched_games
            
            self.stdout.write(self.style.SUCCESS(f"\nMatching completed successfully!"))
            self.stdout.write(f"\n=== SUMMARY ===")
            self.stdout.write(f"Total Betway games: {total_games}")
            self.stdout.write(f"Matched games: {matched_games}")
            self.stdout.write(f"Unmatched games: {unmatched_games}")
            self.stdout.write(f"Match rate: {(matched_games/total_games*100):.1f}%" if total_games > 0 else "N/A")
            self.stdout.write(f"\nOutput saved to: database")
            
            # Show sample matched game
            matched_samples = [m for m in matches_data if m.get('forebet_match_id') is not None]
            if matched_samples:
                sample = matched_samples[0]
                self.stdout.write(f"\n=== SAMPLE MATCHED GAME ===")
                self.stdout.write(f"Betway: {sample.get('home_team')} vs {sample.get('away_team')}")
                self.stdout.write(f"Forebet: {sample.get('forebet_match_id')}")
                self.stdout.write(f"Match Confidence: {sample.get('match_confidence')}%")
                self.stdout.write(f"Forebet Prediction: {sample.get('forebet_pred')}")
                self.stdout.write(f"Forebet Score: {sample.get('forebet_home_pred_score')}-{sample.get('forebet_away_pred_score')}")
            
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Error during matching: {str(e)}")

