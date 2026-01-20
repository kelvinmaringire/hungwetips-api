from django.core.management.base import BaseCommand, CommandError
from betting_engine.services.prediction_model import SoccerPredictionModel
from datetime import datetime, timedelta, timezone
import json


class Command(BaseCommand):
    help = "Train machine learning models for soccer match predictions"

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for training data in YYYY-MM-DD format',
            default=None,
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for training data in YYYY-MM-DD format',
            default=None,
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['outcome', 'score', 'btts', 'all'],
            help='Which model to train (default: all)',
            default='all',
        )
        parser.add_argument(
            '--test-size',
            type=float,
            help='Proportion of data for testing (default: 0.2)',
            default=0.2,
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("Training Soccer Prediction Models")
        self.stdout.write("=" * 60)

        # Initialize model
        model = SoccerPredictionModel()

        # Load historical data
        try:
            self.stdout.write("\nLoading historical data...")
            start_date = options['start_date']
            end_date = options['end_date']
            
            if start_date or end_date:
                self.stdout.write(f"  Date filter: {start_date or 'all'} to {end_date or 'all'}")
            else:
                self.stdout.write("  Loading ALL available merged_*.json files (all dates)")
                self.stdout.write("  This combines data from all historical matches for comprehensive training")
            
            df = model.load_historical_data(start_date=start_date, end_date=end_date)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Loaded {len(df)} total matches from all merged files"))
            
            # Filter matches with results
            if 'home_correct_score' in df.columns and 'away_correct_score' in df.columns:
                # Check for matches with valid results (not null/NaN)
                # Note: 0 is a valid score, so we only filter out null/NaN values
                df_with_results = df[
                    df['home_correct_score'].notna() & 
                    df['away_correct_score'].notna()
                ]
                
                self.stdout.write(f"  ✓ Total matches loaded: {len(df)}")
                self.stdout.write(f"  ✓ Matches with results: {len(df_with_results)}")
                
                if len(df_with_results) < 50:
                    raise CommandError(
                        f"Not enough training data. Found only {len(df_with_results)} matches with results "
                        f"(out of {len(df)} total matches). Need at least 50 matches for training.\n"
                        f"Please collect more historical data by running Steps 1-4 for additional dates."
                    )
                
                df = df_with_results
            else:
                raise CommandError("No match results found in data. Cannot train models.")
            
        except Exception as e:
            raise CommandError(f"Error loading data: {str(e)}")

        # Train models
        model_type = options['model']
        test_size = options['test_size']

        try:
            if model_type in ['outcome', 'all']:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("Training Outcome Model (1/X/2)")
                self.stdout.write("=" * 60)
                accuracy, logloss = model.train_outcome_model(df, test_size=test_size)
                self.stdout.write(self.style.SUCCESS(
                    f"\n✓ Outcome model trained successfully!"
                ))

            if model_type in ['score', 'all']:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("Training Score Model (Total Goals)")
                self.stdout.write("=" * 60)
                mae, rmse = model.train_score_model(df, test_size=test_size)
                self.stdout.write(self.style.SUCCESS(
                    f"\n✓ Score model trained successfully!"
                ))

            if model_type in ['btts', 'all']:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("Training BTTS Model (Both Teams To Score)")
                self.stdout.write("=" * 60)
                accuracy, logloss = model.train_btts_model(df, test_size=test_size)
                self.stdout.write(self.style.SUCCESS(
                    f"\n✓ BTTS model trained successfully!"
                ))

            if model_type == 'all':
                # Train all additional market models
                markets = [
                    ('home_draw_no_bet', 'Home Draw No Bet'),
                    ('away_draw_no_bet', 'Away Draw No Bet'),
                    ('total_over_1.5', 'Total Over 1.5'),
                    ('total_under_3.5', 'Total Under 3.5'),
                    ('home_team_over_0.5', 'Home Team Over 0.5'),
                    ('away_team_over_0.5', 'Away Team Over 0.5'),
                ]
                
                for target_col, market_name in markets:
                    try:
                        self.stdout.write("\n" + "=" * 60)
                        self.stdout.write(f"Training {market_name} Model")
                        self.stdout.write("=" * 60)
                        accuracy, logloss = model.train_market_model(
                            df, target_col, market_name, test_size=test_size
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f"\n✓ {market_name} model trained successfully!"
                        ))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f"\n⚠ Failed to train {market_name} model: {str(e)}"
                        ))

            # Save models
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("Saving Models")
            self.stdout.write("=" * 60)
            model.save_models()
            self.stdout.write(self.style.SUCCESS("\n✓ All models saved successfully!"))

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("Training completed successfully!"))
            self.stdout.write("=" * 60)

        except Exception as e:
            raise CommandError(f"Error during training: {str(e)}")

