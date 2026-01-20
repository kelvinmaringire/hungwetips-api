from django.core.management.base import BaseCommand, CommandError
from betting_engine.services.prediction_model import SoccerPredictionModel
from datetime import datetime, timedelta, timezone
import json
import pandas as pd
import numpy as np
from pathlib import Path


class Command(BaseCommand):
    help = "Make predictions for upcoming matches using trained ML models"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYY-MM-DD format (defaults to tomorrow)',
            default=None,
        )
        parser.add_argument(
            '--input-file',
            type=str,
            help='Input JSON file with match data (default: combined_YYYY-MM-DD.json)',
            default=None,
        )
        parser.add_argument(
            '--output-file',
            type=str,
            help='Output JSON file for predictions (default: predictions_YYYY-MM-DD.json)',
            default=None,
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['outcome', 'score', 'btts', 'all'],
            help='Which predictions to make (default: all)',
            default='all',
        )
        parser.add_argument(
            '--no-train',
            action='store_true',
            help='Skip training and use existing models from disk',
            default=False,
        )
        parser.add_argument(
            '--test-size',
            type=float,
            help='Proportion of data for testing during training (default: 0.2)',
            default=0.2,
        )
        parser.add_argument(
            '--save-models',
            action='store_true',
            help='Save trained models to disk (default: models stay in memory only)',
            default=False,
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("Making Match Predictions")
        self.stdout.write("=" * 60)

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

        # Initialize model
        model = SoccerPredictionModel()

        # Train models first (unless --no-train flag is used)
        if not options['no_train']:
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("Training Models (with latest data)")
            self.stdout.write("=" * 60)
            
            try:
                # Check if merged files exist first
                project_root = Path(__file__).parent.parent.parent.parent
                data_dir = project_root / 'betting_data'
                merged_files = list(data_dir.glob('merged_*.json'))
                
                if not merged_files:
                    self.stdout.write(self.style.WARNING(
                        "\n⚠ No merged_*.json files found. Cannot train models."
                    ))
                    self.stdout.write("  Options:")
                    self.stdout.write("    1. Run 'python manage.py merge_yesterday_results' to create training data")
                    self.stdout.write("    2. Use '--no-train' flag to skip training and use existing models")
                    
                    # Try to load existing models instead
                    try:
                        self.stdout.write("\nAttempting to load existing models from disk...")
                        model.load_models()
                        self.stdout.write(self.style.SUCCESS("  ✓ Existing models loaded successfully"))
                    except Exception as e:
                        raise CommandError(
                            f"No training data available and no existing models found.\n"
                            f"Please run 'python manage.py merge_yesterday_results' first to create training data,\n"
                            f"or ensure models exist in {model.model_dir}"
                        )
                else:
                    # Load historical data (all merged files)
                    self.stdout.write("\nLoading historical data...")
                    self.stdout.write("  Loading ALL available merged_*.json files (all dates)")
                    self.stdout.write("  This combines data from all historical matches for comprehensive training")
                    
                    df_train = model.load_historical_data()
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Loaded {len(df_train)} total matches from all merged files"))
                    
                    # Filter matches with results
                    if 'home_correct_score' in df_train.columns and 'away_correct_score' in df_train.columns:
                        df_train = df_train[
                            df_train['home_correct_score'].notna() & 
                            df_train['away_correct_score'].notna()
                        ]
                        self.stdout.write(f"  ✓ Total matches loaded: {len(df_train)}")
                        self.stdout.write(f"  ✓ Matches with results: {len(df_train)}")
                        
                        if len(df_train) < 50:
                            raise CommandError(
                                f"Not enough training data. Found only {len(df_train)} matches with results "
                                f"(out of {len(df_train)} total matches). Need at least 50 matches for training.\n"
                                f"Please collect more historical data by running Steps 1-4 for additional dates."
                            )
                    else:
                        raise CommandError("No match results found in data. Cannot train models.")
                    
                    # Train models
                    model_type = options['model']
                    test_size = options['test_size']
                    training_metrics = {}
                    
                    if model_type in ['outcome', 'all']:
                        self.stdout.write("\n" + "=" * 60)
                        self.stdout.write("Training Outcome Model (1/X/2)")
                        self.stdout.write("=" * 60)
                        accuracy, logloss = model.train_outcome_model(df_train, test_size=test_size)
                        training_metrics['outcome'] = {'accuracy': accuracy, 'logloss': logloss}
                        self.stdout.write(self.style.SUCCESS(f"\n✓ Outcome model trained successfully!"))

                    if model_type in ['score', 'all']:
                        self.stdout.write("\n" + "=" * 60)
                        self.stdout.write("Training Score Model (Total Goals)")
                        self.stdout.write("=" * 60)
                        mae, rmse = model.train_score_model(df_train, test_size=test_size)
                        training_metrics['score'] = {'mae': mae, 'rmse': rmse}
                        self.stdout.write(self.style.SUCCESS(f"\n✓ Score model trained successfully!"))

                    if model_type in ['btts', 'all']:
                        self.stdout.write("\n" + "=" * 60)
                        self.stdout.write("Training BTTS Model (Both Teams To Score)")
                        self.stdout.write("=" * 60)
                        accuracy, logloss = model.train_btts_model(df_train, test_size=test_size)
                        training_metrics['btts'] = {'accuracy': accuracy, 'logloss': logloss}
                        self.stdout.write(self.style.SUCCESS(f"\n✓ BTTS model trained successfully!"))

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
                                    df_train, target_col, market_name, test_size=test_size
                                )
                                training_metrics[target_col] = {'accuracy': accuracy, 'logloss': logloss}
                                self.stdout.write(self.style.SUCCESS(
                                    f"\n✓ {market_name} model trained successfully!"
                                ))
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(
                                    f"\n⚠ Failed to train {market_name} model: {str(e)}"
                                ))
                                training_metrics[target_col] = {'error': str(e)}
                    
                    # Save training metrics to separate file
                    self._save_training_metrics(model, date_str, training_metrics, len(df_train))
                    
                    # Optionally save models to disk (if requested)
                    if options.get('save_models', False):
                        self.stdout.write("\n" + "=" * 60)
                        self.stdout.write("Saving Models to Disk")
                        self.stdout.write("=" * 60)
                        model.save_models()
                        self.stdout.write(self.style.SUCCESS("  ✓ Models saved to disk"))
                    else:
                        self.stdout.write("\n" + "=" * 60)
                        self.stdout.write(self.style.SUCCESS("✓ All models trained and ready in memory"))
                        self.stdout.write("  Note: Models are kept in memory only (not saved to disk)")
                        self.stdout.write("  Use --save-models flag if you want to save them")
                        self.stdout.write("=" * 60)
                
            except Exception as e:
                raise CommandError(f"Error during training: {str(e)}")
        else:
            # Load existing models from disk
            try:
                self.stdout.write("\nLoading trained models from disk...")
                model.load_models()
                self.stdout.write(self.style.SUCCESS("  ✓ Models loaded successfully"))
            except Exception as e:
                raise CommandError(f"Error loading models: {str(e)}\nPlease train models first using 'python manage.py predict_matches' (without --no-train flag)")

        # Determine input file
        if options['input_file']:
            input_path = Path(options['input_file'])
        else:
            # Default to combined file, fallback to Betway file
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / 'betting_data'
            combined_path = data_dir / f'combined_{date_str}.json'
            betway_path = data_dir / f'{date_str}.json'
            
            if combined_path.exists():
                input_path = combined_path
            elif betway_path.exists():
                input_path = betway_path
            else:
                # Check if any combined files exist
                existing_combined = list(data_dir.glob('combined_*.json'))
                existing_betway = list(data_dir.glob('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].json'))
                
                error_msg = f"Input file not found for date {date_str}.\n"
                error_msg += f"  Tried:\n"
                error_msg += f"    - {combined_path}\n"
                error_msg += f"    - {betway_path}\n"
                
                if existing_combined:
                    error_msg += f"\n  Available combined files:\n"
                    for f in sorted(existing_combined)[-5:]:  # Show last 5
                        error_msg += f"    - {f.name}\n"
                
                if existing_betway:
                    error_msg += f"\n  Available Betway files:\n"
                    for f in sorted(existing_betway)[-5:]:  # Show last 5
                        error_msg += f"    - {f.name}\n"
                
                if not existing_combined and not existing_betway:
                    error_msg += f"\n  No data files found. Please run the workflow steps first:\n"
                    error_msg += f"    1. python manage.py scrape_forebet\n"
                    error_msg += f"    2. python manage.py scrape_betway\n"
                    error_msg += f"    3. python manage.py match_betway_forebet\n"
                
                error_msg += f"\n  Or use --input-file to specify a custom file, or --date to specify a different date."
                
                raise CommandError(error_msg)

        if not input_path.exists():
            raise CommandError(f"Input file not found: {input_path}")

        # Load match data
        try:
            self.stdout.write(f"\nLoading match data from {input_path}...")
            self.stdout.write("  Note: Using combined_*.json file (tomorrow's matches) for prediction")
            self.stdout.write("  Training uses merged_*.json files (all historical data)")
            
            with open(input_path, 'r', encoding='utf-8') as f:
                match_data = json.load(f)
            
            if not match_data:
                raise CommandError("No match data found in input file")
            
            self.stdout.write(self.style.SUCCESS(f"  ✓ Loaded {len(match_data)} matches"))
        except Exception as e:
            raise CommandError(f"Error loading match data: {str(e)}")

        # Convert to DataFrame
        df = pd.DataFrame(match_data)

        # Make predictions
        model_type = options['model']

        try:
            if model_type == 'all':
                # Predict all markets with value calculations
                self.stdout.write("\nMaking predictions for all markets...")
                df = model.predict_all_markets(df)
                self.stdout.write(self.style.SUCCESS("  ✓ All market predictions completed"))
            else:
                # Individual model predictions
                predictions_made = False
                
                if model_type == 'outcome':
                    if model.outcome_model:
                        self.stdout.write("\nMaking outcome predictions (1/X/2)...")
                        df = model.predict_outcome(df)
                        predictions_made = True
                        self.stdout.write(self.style.SUCCESS("  ✓ Outcome predictions completed"))
                    else:
                        self.stdout.write(self.style.WARNING("  ⚠ Outcome model not available"))

                if model_type == 'score':
                    if model.score_model:
                        self.stdout.write("\nMaking score predictions (total goals)...")
                        df = model.predict_score(df)
                        predictions_made = True
                        self.stdout.write(self.style.SUCCESS("  ✓ Score predictions completed"))
                    else:
                        self.stdout.write(self.style.WARNING("  ⚠ Score model not available"))

                if model_type == 'btts':
                    if model.btts_model:
                        self.stdout.write("\nMaking BTTS predictions...")
                        df = model.predict_btts(df)
                        predictions_made = True
                        self.stdout.write(self.style.SUCCESS("  ✓ BTTS predictions completed"))
                    else:
                        self.stdout.write(self.style.WARNING("  ⚠ BTTS model not available"))

                if not predictions_made:
                    raise CommandError("No predictions were made. Check if models are trained.")

            # Convert back to list of dicts
            # Replace NaN/NaT with None so JSON serializes as null instead of NaN
            # Convert DataFrame to dict first, then clean NaN values
            result_data = df.to_dict('records')
            
            # Recursively replace all NaN/NaT values with None
            def replace_nan(obj):
                if isinstance(obj, dict):
                    return {k: replace_nan(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [replace_nan(item) for item in obj]
                elif pd.isna(obj) or (isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj))):
                    return None
                return obj
            
            result_data = replace_nan(result_data)

            # Determine output file
            if options['output_file']:
                output_path = Path(options['output_file'])
            else:
                project_root = Path(__file__).parent.parent.parent.parent
                data_dir = project_root / 'betting_data'
                output_path = data_dir / f'predictions_{date_str}.json'

            # Save predictions
            self.stdout.write(f"\nSaving predictions to {output_path}...")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            self.stdout.write(self.style.SUCCESS(f"  ✓ Predictions saved successfully"))

            # Show summary
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("Prediction Summary")
            self.stdout.write("=" * 60)
            
            if model_type == 'all':
                # Show value bets summary
                value_columns = [col for col in df.columns if col.endswith('_value')]
                if value_columns:
                    self.stdout.write("\nValue Bets (1 = Positive Value, 0 = No Value):")
                    for col in value_columns:
                        value_count = df[col].sum()
                        total = len(df[df[col].notna()])
                        if total > 0:
                            market_name = col.replace('ml_', '').replace('_value', '').replace('_', ' ').title()
                            self.stdout.write(f"  {market_name}: {value_count}/{total} matches ({value_count/total*100:.1f}%)")
                
                if 'ml_pred' in df.columns:
                    outcome_counts = df['ml_pred'].value_counts()
                    self.stdout.write("\nOutcome Predictions:")
                    for outcome, count in outcome_counts.items():
                        self.stdout.write(f"  {outcome}: {count} matches")
            else:
                if 'ml_pred' in df.columns:
                    outcome_counts = df['ml_pred'].value_counts()
                    self.stdout.write("\nOutcome Predictions:")
                    for outcome, count in outcome_counts.items():
                        self.stdout.write(f"  {outcome}: {count} matches")
                
                if 'ml_predicted_total_goals' in df.columns:
                    avg_goals = df['ml_predicted_total_goals'].mean()
                    self.stdout.write(f"\nAverage Predicted Total Goals: {avg_goals:.2f}")
                
                if 'ml_btts_pred' in df.columns:
                    btts_yes = df['ml_btts_pred'].sum()
                    btts_no = len(df) - btts_yes
                    self.stdout.write(f"\nBTTS Predictions:")
                    self.stdout.write(f"  Yes: {btts_yes} matches")
                    self.stdout.write(f"  No: {btts_no} matches")

            # Show sample predictions
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("Sample Predictions")
            self.stdout.write("=" * 60)
            
            sample = result_data[0]
            self.stdout.write(f"\nMatch: {sample.get('home_team', 'Unknown')} vs {sample.get('away_team', 'Unknown')}")
            
            if model_type == 'all':
                # Show value bets for sample
                value_columns = [col for col in sample.keys() if col.endswith('_value')]
                if value_columns:
                    self.stdout.write("\n  Value Bets:")
                    for col in value_columns[:6]:  # Show first 6
                        if sample.get(col) is not None:
                            market_name = col.replace('ml_', '').replace('_value', '').replace('_', ' ').title()
                            value = "✓ YES" if sample[col] == 1 else "✗ NO"
                            prob_col = col.replace('_value', '_prob')
                            prob = sample.get(prob_col, 0)
                            self.stdout.write(f"    {market_name}: {value} (Prob: {prob:.2%})")
            
            if 'ml_pred' in sample:
                self.stdout.write(f"\n  Predicted Outcome: {sample['ml_pred']}")
                if 'ml_prob_home' in sample:
                    self.stdout.write(f"    Probabilities - Home: {sample['ml_prob_home']:.2%}, "
                                    f"Draw: {sample['ml_prob_draw']:.2%}, "
                                    f"Away: {sample['ml_prob_away']:.2%}")
            
            if 'ml_predicted_total_goals' in sample:
                self.stdout.write(f"  Predicted Total Goals: {sample['ml_predicted_total_goals']:.2f}")
            
            if 'ml_btts_pred' in sample:
                btts_result = "Yes" if sample['ml_btts_pred'] == 1 else "No"
                self.stdout.write(f"  BTTS Prediction: {btts_result} (Probability: {sample.get('ml_btts_prob', 0):.2%})")

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("Predictions completed successfully!"))
            self.stdout.write("=" * 60)

        except Exception as e:
            raise CommandError(f"Error during prediction: {str(e)}")
    
    def _save_training_metrics(self, model, date_str, metrics, training_samples):
        """Save training metrics to a separate JSON file."""
        project_root = Path(__file__).parent.parent.parent.parent
        model_dir = project_root / 'betting_data' / 'models'
        model_dir.mkdir(parents=True, exist_ok=True)
        
        metrics_data = {
            'training_date': date_str,
            'training_timestamp': datetime.now().isoformat(),
            'training_samples': training_samples,
            'models_trained': list(metrics.keys()),
            'metrics': metrics
        }
        
        metrics_path = model_dir / f'training_metrics_{date_str}.json'
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(f"\nTraining metrics saved to {metrics_path}")

