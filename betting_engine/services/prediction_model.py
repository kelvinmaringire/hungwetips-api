import lightgbm as lgb
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, log_loss, mean_absolute_error, mean_squared_error
import joblib
from datetime import datetime, timedelta


class SoccerPredictionModel:
    """
    Machine learning model for soccer match predictions using LightGBM.
    Supports multiple prediction tasks:
    - Match outcome (1/X/2) - Multi-class classification
    - Score prediction - Regression
    - Total goals - Regression
    - BTTS - Binary classification
    """

    def __init__(self, data_dir=None, model_dir=None):
        """
        Initialize the prediction model.

        Args:
            data_dir: Directory containing JSON data files. Defaults to betting_data/
            model_dir: Directory to save/load models. Defaults to betting_data/models/
        """
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / 'betting_data'
        else:
            self.data_dir = Path(data_dir)

        if model_dir is None:
            project_root = Path(__file__).parent.parent.parent
            self.model_dir = project_root / 'betting_data' / 'models'
        else:
            self.model_dir = Path(model_dir)

        # Create model directory if it doesn't exist
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Model storage
        self.outcome_model = None
        self.score_model = None
        self.goals_model = None
        self.btts_model = None
        self.home_dnb_model = None  # Home Draw No Bet
        self.away_dnb_model = None  # Away Draw No Bet
        self.over_15_model = None  # Total Over 1.5
        self.under_35_model = None  # Total Under 3.5
        self.home_over_05_model = None  # Home Team Over 0.5
        self.away_over_05_model = None  # Away Team Over 0.5
        
        # Label encoders for categorical features
        self.label_encoders = {}
        
        # Feature columns
        self.feature_columns = None

    def load_historical_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load historical match data from ALL merged JSON files.
        
        IMPORTANT: By default, this combines ALL available merged_*.json files from all dates
        to create a comprehensive training dataset. Use start_date/end_date only to filter
        if needed.

        Args:
            start_date: Start date in YYYY-MM-DD format (optional - filters files before this date)
            end_date: End date in YYYY-MM-DD format (optional - filters files after this date)
            
            If both are None, loads ALL merged_*.json files from all dates.

        Returns:
            DataFrame with combined historical match data from all dates
        """
        all_data = []
        
        # Get all merged JSON files (these contain tips + odds + results)
        merged_files = sorted(self.data_dir.glob('merged_*.json'))
        
        if not merged_files:
            raise ValueError("No merged_*.json files found. Run merge_yesterday_results first.")
        
        print(f"Found {len(merged_files)} merged data files")
        
        for file_path in merged_files:
            # Extract date from filename
            date_str = file_path.stem.replace('merged_', '')
            
            # Filter by date if specified
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_data.extend(data)
                    print(f"  Loaded {len(data)} matches from {file_path.name}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No historical data found")
        
        print(f"\nTotal matches loaded: {len(all_data)} (combined from {len(merged_files)} files)")
        
        return pd.DataFrame(all_data)

    def prepare_features(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """
        Prepare features from raw match data.

        Args:
            df: Raw DataFrame with match data
            is_training: Whether this is training data (has results)

        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # Convert odds to probabilities
        if 'home_win' in df.columns:
            df['home_win_prob'] = 1 / df['home_win'].replace([np.inf, -np.inf], np.nan)
            df['draw_prob'] = 1 / df['draw'].replace([np.inf, -np.inf], np.nan)
            df['away_win_prob'] = 1 / df['away_win'].replace([np.inf, -np.inf], np.nan)
        
        # Odds-derived features
        if 'home_win' in df.columns and 'away_win' in df.columns:
            df['odds_ratio'] = df['home_win'] / df['away_win'].replace(0, np.nan)
            df['favorite'] = (df['home_win'] < df['away_win']).astype(int)
        
        # Forebet probability features
        if 'prob_1' in df.columns:
            df['forebet_home_prob'] = df['prob_1'] / 100.0
            df['forebet_draw_prob'] = df['prob_x'] / 100.0
            df['forebet_away_prob'] = df['prob_2'] / 100.0
            
            # Probability differences
            df['prob_diff'] = df['forebet_home_prob'] - df['forebet_away_prob']
            df['prob_sum'] = df['forebet_home_prob'] + df['forebet_draw_prob'] + df['forebet_away_prob']
        
        # Kelly criterion (betting value indicator)
        if 'kelly' in df.columns:
            df['has_kelly_value'] = (df['kelly'] > 0).astype(int)
            df['kelly'] = df['kelly'].fillna(0)
        
        # Average goals
        if 'avg_goals' in df.columns:
            df['avg_goals'] = df['avg_goals'].fillna(df['avg_goals'].median())
        
        # Predicted scores
        if 'home_pred_score' in df.columns:
            df['home_pred_score'] = df['home_pred_score'].fillna(0)
            df['away_pred_score'] = df['away_pred_score'].fillna(0)
            df['predicted_total_goals'] = df['home_pred_score'] + df['away_pred_score']
        
        # BTTS odds features
        if 'BTTS_yes' in df.columns:
            df['btts_prob'] = 1 / df['BTTS_yes'].replace([np.inf, -np.inf], np.nan)
        
        # Total goals odds features
        if 'total_over_1.5' in df.columns:
            df['over_1.5_prob'] = 1 / df['total_over_1.5'].replace([np.inf, -np.inf], np.nan)
        
        # Normalize field names (handle both forebet_* and normalized names)
        if 'forebet_country' in df.columns and 'country' not in df.columns:
            df['country'] = df['forebet_country']
        if 'forebet_league_name' in df.columns and 'league_name' not in df.columns:
            df['league_name'] = df['forebet_league_name']
        
        # Team and league encoding (for training)
        if is_training:
            categorical_cols = ['home_team', 'away_team', 'country', 'league_name']
            for col in categorical_cols:
                if col in df.columns:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                        df[col] = df[col].fillna('Unknown')
                        # Ensure 'Unknown' is always in the encoder
                        unique_values = df[col].unique().tolist()
                        if 'Unknown' not in unique_values:
                            unique_values.append('Unknown')
                        self.label_encoders[col].fit(unique_values)
                        df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
                    else:
                        df[col] = df[col].fillna('Unknown')
                        # Handle unseen categories - map to 'Unknown' if not in known classes
                        known_classes = set(self.label_encoders[col].classes_)
                        # Ensure 'Unknown' is in known classes
                        if 'Unknown' not in known_classes:
                            # Re-fit encoder to include 'Unknown'
                            all_classes = list(self.label_encoders[col].classes_) + ['Unknown']
                            self.label_encoders[col].fit(all_classes)
                            known_classes.add('Unknown')
                        df[col] = df[col].apply(lambda x: x if x in known_classes else 'Unknown')
                        df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        else:
            # For prediction, use existing encoders
            categorical_cols = ['home_team', 'away_team', 'country', 'league_name']
            for col in categorical_cols:
                if col in df.columns and col in self.label_encoders:
                    df[col] = df[col].fillna('Unknown')
                    known_classes = set(self.label_encoders[col].classes_)
                    
                    # Map unseen values to a known class
                    # If 'Unknown' exists in encoder, use it; otherwise use the first class
                    if 'Unknown' in known_classes:
                        fallback_class = 'Unknown'
                    elif len(known_classes) > 0:
                        # Use the first class as fallback (most common approach)
                        fallback_class = list(known_classes)[0]
                    else:
                        # No classes available, skip encoding
                        continue
                    
                    # Map unseen values to fallback class
                    df[col] = df[col].apply(lambda x: x if x in known_classes else fallback_class)
                    df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        return df

    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns for model training."""
        return [
            # Odds features
            'home_win_prob', 'draw_prob', 'away_win_prob',
            'odds_ratio', 'favorite',
            # Forebet features
            'forebet_home_prob', 'forebet_draw_prob', 'forebet_away_prob',
            'prob_diff', 'prob_sum',
            # Kelly and goals
            'kelly', 'has_kelly_value', 'avg_goals',
            # Predicted scores
            'home_pred_score', 'away_pred_score', 'predicted_total_goals',
            # BTTS and totals
            'btts_prob', 'over_1.5_prob',
            # Encoded categoricals
            'home_team_encoded', 'away_team_encoded',
            'country_encoded', 'league_name_encoded',
        ]
    
    def _ensure_feature_columns(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure all required features exist in the dataframe.
        Creates missing features with appropriate defaults.
        
        Args:
            df_features: DataFrame with features
            
        Returns:
            DataFrame with all required features, in the correct order
        """
        if not self.feature_columns:
            raise ValueError("Feature columns not loaded. Train or load models first.")
        
        # Create a copy with all required features
        result = pd.DataFrame(index=df_features.index)
        
        for col in self.feature_columns:
            if col in df_features.columns:
                result[col] = df_features[col]
            else:
                # Create missing feature with default value
                if col.endswith('_encoded'):
                    # Encoded features default to 0
                    result[col] = 0
                elif 'prob' in col.lower():
                    # Probability features default to 0.5
                    result[col] = 0.5
                elif col in ['kelly', 'has_kelly_value', 'favorite']:
                    # Binary/count features default to 0
                    result[col] = 0
                elif 'score' in col.lower() or 'goals' in col.lower():
                    # Score/goals features default to 0
                    result[col] = 0
                elif col in ['odds_ratio', 'prob_diff', 'prob_sum']:
                    # Ratio/diff features default to 0
                    result[col] = 0
                else:
                    # Default to 0 for any other features
                    result[col] = 0
        
        # Fill NaN values with median (or 0 if all NaN)
        for col in result.columns:
            if result[col].isna().any():
                median_val = result[col].median()
                if pd.isna(median_val):
                    result[col] = result[col].fillna(0)
                else:
                    result[col] = result[col].fillna(median_val)
        
        # Ensure columns are in the exact order expected by the model
        result = result[self.feature_columns]
        
        return result

    def prepare_outcome_target(self, df: pd.DataFrame) -> pd.Series:
        """
        Prepare target variable for match outcome (1/X/2).

        Args:
            df: DataFrame with match results

        Returns:
            Series with encoded outcomes (0=Home, 1=Draw, 2=Away)
        """
        # Use actual results if available
        if 'home_correct_score' in df.columns and 'away_correct_score' in df.columns:
            conditions = [
                df['home_correct_score'] > df['away_correct_score'],  # Home win
                df['home_correct_score'] == df['away_correct_score'],  # Draw
                df['home_correct_score'] < df['away_correct_score'],  # Away win
            ]
            choices = [0, 1, 2]
            return np.select(conditions, choices, default=1)  # Default to draw if missing
        
        # Fallback to prediction if no results
        if 'pred' in df.columns:
            mapping = {'1': 0, 'X': 1, '2': 2}
            return df['pred'].map(mapping).fillna(1)
        
        raise ValueError("No outcome data available")

    def train_outcome_model(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        """
        Train model for match outcome prediction (1/X/2).

        Args:
            df: Training DataFrame
            test_size: Proportion of data for testing
            random_state: Random seed
        """
        print("Preparing features for outcome prediction...")
        df_features = self.prepare_features(df, is_training=True)
        
        # Get feature columns
        feature_cols = self.get_feature_columns()
        available_features = [col for col in feature_cols if col in df_features.columns]
        self.feature_columns = available_features
        
        # Prepare target
        y = self.prepare_outcome_target(df_features)
        
        # Filter out rows with missing target
        valid_mask = ~pd.isna(y)
        X = df_features[available_features][valid_mask]
        y = y[valid_mask]
        
        # Fill missing values
        X = X.fillna(X.median())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # LightGBM parameters for multi-class classification
        params = {
            'objective': 'multiclass',
            'num_class': 3,
            'metric': 'multi_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': random_state,
        }
        
        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Train model
        print("Training outcome model...")
        self.outcome_model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[train_data, test_data],
            valid_names=['train', 'eval'],
            callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=10)]
        )
        
        # Evaluate
        y_pred = self.outcome_model.predict(X_test)
        y_pred_class = np.argmax(y_pred, axis=1)
        
        accuracy = accuracy_score(y_test, y_pred_class)
        logloss = log_loss(y_test, y_pred)
        
        print(f"\nOutcome Model Performance:")
        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Log Loss: {logloss:.4f}")
        
        return accuracy, logloss

    def train_score_model(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        """
        Train model for score prediction (total goals).

        Args:
            df: Training DataFrame
            test_size: Proportion of data for testing
            random_state: Random seed
        """
        print("Preparing features for score prediction...")
        df_features = self.prepare_features(df, is_training=True)
        
        # Get feature columns
        feature_cols = self.get_feature_columns()
        available_features = [col for col in feature_cols if col in df_features.columns]
        
        # Prepare target (total goals)
        if 'home_correct_score' in df_features.columns and 'away_correct_score' in df_features.columns:
            y = df_features['home_correct_score'] + df_features['away_correct_score']
        elif 'predicted_total_goals' in df_features.columns:
            y = df_features['predicted_total_goals']
        else:
            raise ValueError("No score data available")
        
        # Filter valid rows
        valid_mask = ~pd.isna(y) & (y >= 0)
        X = df_features[available_features][valid_mask]
        y = y[valid_mask]
        
        # Fill missing values
        X = X.fillna(X.median())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # LightGBM parameters for regression
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': random_state,
        }
        
        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Train model
        print("Training score model...")
        self.score_model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[train_data, test_data],
            valid_names=['train', 'eval'],
            callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=10)]
        )
        
        # Evaluate
        y_pred = self.score_model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        print(f"\nScore Model Performance:")
        print(f"  MAE: {mae:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        
        return mae, rmse

    def train_btts_model(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        """
        Train model for BTTS (Both Teams To Score) prediction.

        Args:
            df: Training DataFrame
            test_size: Proportion of data for testing
            random_state: Random seed
        """
        print("Preparing features for BTTS prediction...")
        df_features = self.prepare_features(df, is_training=True)
        
        # Get feature columns
        feature_cols = self.get_feature_columns()
        available_features = [col for col in feature_cols if col in df_features.columns]
        
        # Prepare target (BTTS: 1 if both teams scored, 0 otherwise)
        if 'home_correct_score' in df_features.columns and 'away_correct_score' in df_features.columns:
            y = ((df_features['home_correct_score'] > 0) & 
                 (df_features['away_correct_score'] > 0)).astype(int)
        else:
            raise ValueError("No score data available for BTTS")
        
        # Filter valid rows
        valid_mask = ~pd.isna(y)
        X = df_features[available_features][valid_mask]
        y = y[valid_mask]
        
        # Fill missing values
        X = X.fillna(X.median())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # LightGBM parameters for binary classification
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': random_state,
        }
        
        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Train model
        print("Training BTTS model...")
        self.btts_model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[train_data, test_data],
            valid_names=['train', 'eval'],
            callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=10)]
        )
        
        # Evaluate
        y_pred_proba = self.btts_model.predict(X_test)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        accuracy = accuracy_score(y_test, y_pred)
        logloss = log_loss(y_test, y_pred_proba)
        
        print(f"\nBTTS Model Performance:")
        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Log Loss: {logloss:.4f}")
        
        return accuracy, logloss

    def train_market_model(self, df: pd.DataFrame, target_col: str, market_name: str, 
                          test_size: float = 0.2, random_state: int = 42):
        """
        Generic method to train binary classification models for betting markets.
        
        Args:
            df: Training DataFrame
            target_col: Column name for target variable
            market_name: Name of the market (for logging)
            test_size: Proportion of data for testing
            random_state: Random seed
            
        Returns:
            Tuple of (accuracy, logloss)
        """
        print(f"Preparing features for {market_name} prediction...")
        df_features = self.prepare_features(df, is_training=True)
        
        # Get feature columns
        feature_cols = self.get_feature_columns()
        available_features = [col for col in feature_cols if col in df_features.columns]
        
        # Prepare target based on market type
        if target_col == 'home_draw_no_bet':
            # Home wins or draw (not away win)
            if 'home_correct_score' in df_features.columns:
                y = (df_features['home_correct_score'] >= df_features['away_correct_score']).astype(int)
            else:
                raise ValueError("No score data available")
        elif target_col == 'away_draw_no_bet':
            # Away wins or draw (not home win)
            if 'home_correct_score' in df_features.columns:
                y = (df_features['away_correct_score'] >= df_features['home_correct_score']).astype(int)
            else:
                raise ValueError("No score data available")
        elif target_col == 'total_over_1.5':
            # Total goals > 1.5
            if 'home_correct_score' in df_features.columns:
                total_goals = df_features['home_correct_score'] + df_features['away_correct_score']
                y = (total_goals > 1.5).astype(int)
            else:
                raise ValueError("No score data available")
        elif target_col == 'total_under_3.5':
            # Total goals < 3.5
            if 'home_correct_score' in df_features.columns:
                total_goals = df_features['home_correct_score'] + df_features['away_correct_score']
                y = (total_goals < 3.5).astype(int)
            else:
                raise ValueError("No score data available")
        elif target_col == 'home_team_over_0.5':
            # Home team scores > 0.5
            if 'home_correct_score' in df_features.columns:
                y = (df_features['home_correct_score'] > 0.5).astype(int)
            else:
                raise ValueError("No score data available")
        elif target_col == 'away_team_over_0.5':
            # Away team scores > 0.5
            if 'away_correct_score' in df_features.columns:
                y = (df_features['away_correct_score'] > 0.5).astype(int)
            else:
                raise ValueError("No score data available")
        else:
            raise ValueError(f"Unknown target column: {target_col}")
        
        # Filter valid rows
        valid_mask = ~pd.isna(y)
        X = df_features[available_features][valid_mask]
        y = y[valid_mask]
        
        # Fill missing values
        X = X.fillna(X.median())
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
        
        # LightGBM parameters for binary classification
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': random_state,
        }
        
        # Create datasets
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Train model
        print(f"Training {market_name} model...")
        model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[train_data, test_data],
            valid_names=['train', 'eval'],
            callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(period=10)]
        )
        
        # Store model
        model_attr = {
            'home_draw_no_bet': 'home_dnb_model',
            'away_draw_no_bet': 'away_dnb_model',
            'total_over_1.5': 'over_15_model',
            'total_under_3.5': 'under_35_model',
            'home_team_over_0.5': 'home_over_05_model',
            'away_team_over_0.5': 'away_over_05_model',
        }[target_col]
        setattr(self, model_attr, model)
        
        # Evaluate
        y_pred_proba = model.predict(X_test)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        accuracy = accuracy_score(y_test, y_pred)
        logloss = log_loss(y_test, y_pred_proba)
        
        print(f"\n{market_name} Model Performance:")
        print(f"  Accuracy: {accuracy:.4f}")
        print(f"  Log Loss: {logloss:.4f}")
        
        return accuracy, logloss

    def save_models(self):
        """Save trained models and encoders to disk."""
        if self.outcome_model:
            self.outcome_model.save_model(str(self.model_dir / 'outcome_model.txt'))
        if self.score_model:
            self.score_model.save_model(str(self.model_dir / 'score_model.txt'))
        if self.btts_model:
            self.btts_model.save_model(str(self.model_dir / 'btts_model.txt'))
        if self.home_dnb_model:
            self.home_dnb_model.save_model(str(self.model_dir / 'home_dnb_model.txt'))
        if self.away_dnb_model:
            self.away_dnb_model.save_model(str(self.model_dir / 'away_dnb_model.txt'))
        if self.over_15_model:
            self.over_15_model.save_model(str(self.model_dir / 'over_15_model.txt'))
        if self.under_35_model:
            self.under_35_model.save_model(str(self.model_dir / 'under_35_model.txt'))
        if self.home_over_05_model:
            self.home_over_05_model.save_model(str(self.model_dir / 'home_over_05_model.txt'))
        if self.away_over_05_model:
            self.away_over_05_model.save_model(str(self.model_dir / 'away_over_05_model.txt'))
        
        # Save label encoders
        if self.label_encoders:
            joblib.dump(self.label_encoders, str(self.model_dir / 'label_encoders.pkl'))
        
        # Save feature columns
        if self.feature_columns:
            with open(self.model_dir / 'feature_columns.json', 'w') as f:
                json.dump(self.feature_columns, f)
        
        print(f"\nModels saved to {self.model_dir}")

    def load_models(self):
        """Load trained models and encoders from disk."""
        # Load models
        outcome_path = self.model_dir / 'outcome_model.txt'
        score_path = self.model_dir / 'score_model.txt'
        btts_path = self.model_dir / 'btts_model.txt'
        home_dnb_path = self.model_dir / 'home_dnb_model.txt'
        away_dnb_path = self.model_dir / 'away_dnb_model.txt'
        over_15_path = self.model_dir / 'over_15_model.txt'
        under_35_path = self.model_dir / 'under_35_model.txt'
        home_over_05_path = self.model_dir / 'home_over_05_model.txt'
        away_over_05_path = self.model_dir / 'away_over_05_model.txt'
        
        if outcome_path.exists():
            self.outcome_model = lgb.Booster(model_file=str(outcome_path))
        if score_path.exists():
            self.score_model = lgb.Booster(model_file=str(score_path))
        if btts_path.exists():
            self.btts_model = lgb.Booster(model_file=str(btts_path))
        if home_dnb_path.exists():
            self.home_dnb_model = lgb.Booster(model_file=str(home_dnb_path))
        if away_dnb_path.exists():
            self.away_dnb_model = lgb.Booster(model_file=str(away_dnb_path))
        if over_15_path.exists():
            self.over_15_model = lgb.Booster(model_file=str(over_15_path))
        if under_35_path.exists():
            self.under_35_model = lgb.Booster(model_file=str(under_35_path))
        if home_over_05_path.exists():
            self.home_over_05_model = lgb.Booster(model_file=str(home_over_05_path))
        if away_over_05_path.exists():
            self.away_over_05_model = lgb.Booster(model_file=str(away_over_05_path))
        
        # Load label encoders
        encoders_path = self.model_dir / 'label_encoders.pkl'
        if encoders_path.exists():
            self.label_encoders = joblib.load(str(encoders_path))
        
        # Load feature columns
        features_path = self.model_dir / 'feature_columns.json'
        if features_path.exists():
            with open(features_path, 'r') as f:
                self.feature_columns = json.load(f)
        
        print(f"Models loaded from {self.model_dir}")

    def predict_outcome(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict match outcomes (1/X/2).

        Args:
            df: DataFrame with match data

        Returns:
            DataFrame with predictions added
        """
        if not self.outcome_model:
            raise ValueError("Outcome model not loaded. Train or load model first.")
        
        df_features = self.prepare_features(df, is_training=False)
        
        # Ensure all required features exist (create missing ones with defaults)
        X = self._ensure_feature_columns(df_features)
        
        # Predict
        predictions = self.outcome_model.predict(X)
        outcome_probs = pd.DataFrame(predictions, columns=['prob_home', 'prob_draw', 'prob_away'])
        outcome_pred = np.argmax(predictions, axis=1)
        outcome_mapping = {0: '1', 1: 'X', 2: '2'}
        outcome_pred_str = pd.Series(outcome_pred).map(outcome_mapping)
        
        # Add to dataframe
        df_result = df.copy()
        df_result['ml_pred'] = outcome_pred_str
        df_result['ml_prob_home'] = outcome_probs['prob_home']
        df_result['ml_prob_draw'] = outcome_probs['prob_draw']
        df_result['ml_prob_away'] = outcome_probs['prob_away']
        
        return df_result

    def predict_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict total goals.

        Args:
            df: DataFrame with match data

        Returns:
            DataFrame with score predictions added
        """
        if not self.score_model:
            raise ValueError("Score model not loaded. Train or load model first.")
        
        df_features = self.prepare_features(df, is_training=False)
        
        # Ensure all required features exist (create missing ones with defaults)
        X = self._ensure_feature_columns(df_features)
        
        # Predict
        total_goals = self.score_model.predict(X)
        
        # Add to dataframe
        df_result = df.copy()
        df_result['ml_predicted_total_goals'] = total_goals
        
        return df_result

    def predict_btts(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict BTTS (Both Teams To Score).

        Args:
            df: DataFrame with match data

        Returns:
            DataFrame with BTTS predictions added
        """
        if not self.btts_model:
            raise ValueError("BTTS model not loaded. Train or load model first.")
        
        df_features = self.prepare_features(df, is_training=False)
        
        # Ensure all required features exist (create missing ones with defaults)
        X = self._ensure_feature_columns(df_features)
        
        # Predict
        btts_proba = self.btts_model.predict(X)
        btts_pred = (btts_proba > 0.5).astype(int)
        
        # Add to dataframe
        df_result = df.copy()
        df_result['ml_btts_prob'] = btts_proba
        df_result['ml_btts_pred'] = btts_pred
        
        return df_result
    
    def predict_all_markets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict all betting markets and return value bets (1 if positive value, 0 if not).
        Compares predicted probability vs implied probability from odds.
        Only assigns ml_value=1 when outcome is "most likely to happen" and "properly justified"
        (i.e., highest probability AND meets minimum probability threshold).
        
        IMPORTANT: This method is used for PREDICTION on NEW data (tomorrow's matches).
        Input should be from combined_YYYY-MM-DD.json files (from match_betway_forebet command).
        Training uses merged_*.json files (from merge_yesterday_results command).
        
        Args:
            df: DataFrame with match data and odds (typically from combined_*.json)
                Should contain: odds, Forebet predictions, team names, league info
            
        Returns:
            DataFrame with all market predictions added
        """
        df_result = df.copy()
        
        # Configuration: Minimum probability thresholds and margins for value bets
        MIN_PROBABILITY_THRESHOLD = 0.65  # Outcome must have at least 65% predicted probability
        MIN_PROBABILITY_MARGIN = 0.03  # Must exceed implied probability by at least 3%
        
        # Ensure odds are numeric
        odds_columns = ['home_win', 'draw', 'away_win', 'home_draw_no_bet', 'away_draw_no_bet',
                    'total_over_1.5', 'total_under_3.5', 'BTTS_yes', 'BTTS_no',
                    'home_team_over_0.5', 'away_team_over_0.5']
        
        for col in odds_columns:
            if col in df_result.columns:
                df_result[col] = pd.to_numeric(df_result[col], errors='coerce')
        
        df_features = self.prepare_features(df, is_training=False)
        # Ensure all required features exist (create missing ones with defaults)
        X = self._ensure_feature_columns(df_features)
        
        # Predict Home Draw No Bet
        if self.home_dnb_model and 'home_draw_no_bet' in df_result.columns:
            prob = self.home_dnb_model.predict(X)
            implied_prob = 1 / df_result['home_draw_no_bet'].replace([0, np.inf, -np.inf], np.nan)
            # Stricter criteria: prob > implied_prob AND prob >= MIN_PROBABILITY_THRESHOLD AND (prob - implied_prob) >= MIN_PROBABILITY_MARGIN
            df_result['ml_home_dnb_value'] = ((prob > implied_prob) & 
                                            (prob >= MIN_PROBABILITY_THRESHOLD) &
                                            ((prob - implied_prob) >= MIN_PROBABILITY_MARGIN) &
                                            (implied_prob.notna())).astype(int)
            df_result['ml_home_dnb_prob'] = prob
        
        # Predict Away Draw No Bet
        if self.away_dnb_model and 'away_draw_no_bet' in df_result.columns:
            prob = self.away_dnb_model.predict(X)
            implied_prob = 1 / df_result['away_draw_no_bet'].replace([0, np.inf, -np.inf], np.nan)
            df_result['ml_away_dnb_value'] = ((prob > implied_prob) & 
                                            (prob >= MIN_PROBABILITY_THRESHOLD) &
                                            ((prob - implied_prob) >= MIN_PROBABILITY_MARGIN) &
                                            (implied_prob.notna())).astype(int)
            df_result['ml_away_dnb_prob'] = prob
        
        # Predict Total Over 1.5
        if self.over_15_model and 'total_over_1.5' in df_result.columns:
            prob = self.over_15_model.predict(X)
            implied_prob = 1 / df_result['total_over_1.5'].replace([0, np.inf, -np.inf], np.nan)
            df_result['ml_over_15_value'] = ((prob > implied_prob) & 
                                            (prob >= MIN_PROBABILITY_THRESHOLD) &
                                            ((prob - implied_prob) >= MIN_PROBABILITY_MARGIN) &
                                            (implied_prob.notna())).astype(int)
            df_result['ml_over_15_prob'] = prob
        
        # Predict Total Under 3.5
        if self.under_35_model and 'total_under_3.5' in df_result.columns:
            prob = self.under_35_model.predict(X)
            implied_prob = 1 / df_result['total_under_3.5'].replace([0, np.inf, -np.inf], np.nan)
            df_result['ml_under_35_value'] = ((prob > implied_prob) & 
                                            (prob >= MIN_PROBABILITY_THRESHOLD) &
                                            ((prob - implied_prob) >= MIN_PROBABILITY_MARGIN) &
                                            (implied_prob.notna())).astype(int)
            df_result['ml_under_35_prob'] = prob
        
        # Predict Home Team Over 0.5
        if self.home_over_05_model and 'home_team_over_0.5' in df_result.columns:
            prob = self.home_over_05_model.predict(X)
            implied_prob = 1 / df_result['home_team_over_0.5'].replace([0, np.inf, -np.inf], np.nan)
            df_result['ml_home_over_05_value'] = ((prob > implied_prob) & 
                                                (prob >= MIN_PROBABILITY_THRESHOLD) &
                                                ((prob - implied_prob) >= MIN_PROBABILITY_MARGIN) &
                                                (implied_prob.notna())).astype(int)
            df_result['ml_home_over_05_prob'] = prob
        
        # Predict Away Team Over 0.5
        if self.away_over_05_model and 'away_team_over_0.5' in df_result.columns:
            prob = self.away_over_05_model.predict(X)
            implied_prob = 1 / df_result['away_team_over_0.5'].replace([0, np.inf, -np.inf], np.nan)
            df_result['ml_away_over_05_value'] = ((prob > implied_prob) & 
                                                (prob >= MIN_PROBABILITY_THRESHOLD) &
                                                ((prob - implied_prob) >= MIN_PROBABILITY_MARGIN) &
                                                (implied_prob.notna())).astype(int)
            df_result['ml_away_over_05_prob'] = prob
        
        # Predict BTTS (update with value calculation)
        if self.btts_model and 'BTTS_yes' in df_result.columns:
            prob = self.btts_model.predict(X)
            implied_prob = 1 / df_result['BTTS_yes'].replace([0, np.inf, -np.inf], np.nan)
            df_result['ml_btts_value'] = ((prob > implied_prob) & 
                                        (prob >= MIN_PROBABILITY_THRESHOLD) &
                                        ((prob - implied_prob) >= MIN_PROBABILITY_MARGIN) &
                                        (implied_prob.notna())).astype(int)
            df_result['ml_btts_prob'] = prob
        
        # Predict Match Outcome (1/X/2) with value
        # For match outcomes, we also require the outcome to be the MOST LIKELY (highest probability)
        if self.outcome_model:
            predictions = self.outcome_model.predict(X)
            outcome_probs = pd.DataFrame(predictions, columns=['prob_home', 'prob_draw', 'prob_away'])
            
            # Determine which outcome is most likely (highest probability)
            max_probs = outcome_probs.max(axis=1)
            is_home_most_likely = (outcome_probs['prob_home'] == max_probs)
            is_draw_most_likely = (outcome_probs['prob_draw'] == max_probs)
            is_away_most_likely = (outcome_probs['prob_away'] == max_probs)
            
            # Calculate value for each outcome - only if it's the most likely AND meets thresholds
            if 'home_win' in df_result.columns:
                implied_home = 1 / df_result['home_win'].replace([0, np.inf, -np.inf], np.nan)
                df_result['ml_home_win_value'] = ((outcome_probs['prob_home'] > implied_home) & 
                                                is_home_most_likely &
                                                (outcome_probs['prob_home'] >= MIN_PROBABILITY_THRESHOLD) &
                                                ((outcome_probs['prob_home'] - implied_home) >= MIN_PROBABILITY_MARGIN) &
                                                (implied_home.notna())).astype(int)
            
            if 'draw' in df_result.columns:
                implied_draw = 1 / df_result['draw'].replace([0, np.inf, -np.inf], np.nan)
                df_result['ml_draw_value'] = ((outcome_probs['prob_draw'] > implied_draw) & 
                                            is_draw_most_likely &
                                            (outcome_probs['prob_draw'] >= MIN_PROBABILITY_THRESHOLD) &
                                            ((outcome_probs['prob_draw'] - implied_draw) >= MIN_PROBABILITY_MARGIN) &
                                            (implied_draw.notna())).astype(int)
            
            if 'away_win' in df_result.columns:
                implied_away = 1 / df_result['away_win'].replace([0, np.inf, -np.inf], np.nan)
                df_result['ml_away_win_value'] = ((outcome_probs['prob_away'] > implied_away) & 
                                                is_away_most_likely &
                                                (outcome_probs['prob_away'] >= MIN_PROBABILITY_THRESHOLD) &
                                                ((outcome_probs['prob_away'] - implied_away) >= MIN_PROBABILITY_MARGIN) &
                                                (implied_away.notna())).astype(int)
            
            df_result['ml_prob_home'] = outcome_probs['prob_home']
            df_result['ml_prob_draw'] = outcome_probs['prob_draw']
            df_result['ml_prob_away'] = outcome_probs['prob_away']
        
        return df_result
