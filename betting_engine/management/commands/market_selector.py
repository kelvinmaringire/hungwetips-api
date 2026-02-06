from django.core.management.base import BaseCommand, CommandError
from betting_engine.services.market_selector import MarketSelector
from datetime import datetime, timedelta, timezone
import json


class Command(BaseCommand):
    help = "Select betting markets based on odds thresholds and Forebet predictions"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYY-MM-DD format (defaults to tomorrow)',
            default=None,
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Custom output filename (default: market_selectors_YYYY-MM-DD.json)',
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
        
        self.stdout.write(f"Selecting markets for date: {date_str}")
        
        try:
            selector = MarketSelector()
            output_path = selector.select_and_save(
                date_str=date_str,
                output_filename=options['output']
            )
            
            # Load the selected markets from database to show detailed statistics
            from betting_engine.models import MarketSelection
            
            market_selection = MarketSelection.objects.using('default').filter(date=date_obj).first()
            
            if not market_selection:
                raise CommandError(f"No market selections found for {date_str}")
            
            selections_data = market_selection.selections if isinstance(market_selection.selections, list) else []
            total_matches = len(selections_data)
            home_over_count = sum(1 for m in selections_data if m.get('home_over_bet', False))
            away_over_count = sum(1 for m in selections_data if m.get('away_over_bet', False))
            home_draw_count = sum(1 for m in selections_data if m.get('home_draw_bet', False))
            away_draw_count = sum(1 for m in selections_data if m.get('away_draw_bet', False))
            over_1_5_count = sum(1 for m in selections_data if m.get('over_1_5_bet', False))
            
            self.stdout.write(self.style.SUCCESS(f"\nMarket selection completed successfully!"))
            self.stdout.write(f"\n=== SUMMARY ===")
            self.stdout.write(f"Total matches: {total_matches}")
            self.stdout.write(f"Home Over 0.5: {home_over_count} matches ({home_over_count/total_matches*100:.2f}%)" if total_matches > 0 else "Home Over 0.5: 0 matches")
            self.stdout.write(f"Away Over 0.5: {away_over_count} matches ({away_over_count/total_matches*100:.2f}%)" if total_matches > 0 else "Away Over 0.5: 0 matches")
            self.stdout.write(f"Home Draw: {home_draw_count} matches ({home_draw_count/total_matches*100:.2f}%)" if total_matches > 0 else "Home Draw: 0 matches")
            self.stdout.write(f"Away Draw: {away_draw_count} matches ({away_draw_count/total_matches*100:.2f}%)" if total_matches > 0 else "Away Draw: 0 matches")
            self.stdout.write(f"Over 1.5 Goals: {over_1_5_count} matches ({over_1_5_count/total_matches*100:.2f}%)" if total_matches > 0 else "Over 1.5 Goals: 0 matches")
            self.stdout.write(f"\nOutput saved to: database")
            
            # Show sample selected markets
            home_over_samples = [m for m in selections_data if m.get('home_over_bet', False)]
            if home_over_samples:
                sample = home_over_samples[0]
                self.stdout.write(f"\n=== SAMPLE HOME OVER 0.5 BET ===")
                self.stdout.write(f"Match ID: {sample.get('forebet_match_id')}")
                self.stdout.write(f"Teams: {sample.get('home_team')} vs {sample.get('away_team')}")
                self.stdout.write(f"Odds: {sample.get('home_team_over_0.5')}")
                self.stdout.write(f"Prediction: {sample.get('forebet_pred')} ({sample.get('forebet_home_pred_score')}-{sample.get('forebet_away_pred_score')})")
            
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Error during market selection: {str(e)}")
