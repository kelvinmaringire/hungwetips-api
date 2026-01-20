# Soccer Prediction Model Documentation

This module provides machine learning models for soccer match predictions using LightGBM.

## Features

The prediction system supports predictions for all major betting markets:

### Core Predictions
1. **Match Outcome (1/X/2)** - Multi-class classification predicting home win, draw, or away win
2. **Total Goals** - Regression model predicting total goals in a match
3. **BTTS (Both Teams To Score)** - Binary classification predicting if both teams will score

### Additional Market Predictions
4. **Home Draw No Bet** - Binary classification (Home wins or draw, not away win)
5. **Away Draw No Bet** - Binary classification (Away wins or draw, not home win)
6. **Total Over 1.5** - Binary classification (Total goals > 1.5)
7. **Total Under 3.5** - Binary classification (Total goals < 3.5)
8. **Home Team Over 0.5** - Binary classification (Home team scores > 0.5)
9. **Away Team Over 0.5** - Binary classification (Away team scores > 0.5)

### Value Bet Detection
All markets include **value bet predictions** that compare ML-predicted probabilities against bookmaker odds:
- **1** = Positive value bet (predicted probability > implied probability from odds)
- **0** = No value (predicted probability ≤ implied probability from odds)

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Required ML libraries:
- `lightgbm==4.1.0` - Gradient boosting framework
- `pandas==2.1.0` - Data manipulation
- `numpy==1.24.0` - Numerical computing
- `scikit-learn==1.3.0` - Machine learning utilities
- `joblib==1.3.0` - Model serialization

## Usage

### 1. Train Models

Train models using historical match data:

```bash
# Train all models with default settings (last 90 days)
python manage.py train_model

# Train specific model
python manage.py train_model --model outcome
python manage.py train_model --model score
python manage.py train_model --model btts

# Train all models (including all betting markets)
python manage.py train_model --model all

# Train with custom date range
python manage.py train_model --start-date 2025-01-01 --end-date 2026-01-15

# Custom test split
python manage.py train_model --test-size 0.3
```

**Requirements:**
- Historical match data in `betting_data/merged_*.json` files
- Matches must have results (`home_correct_score`, `away_correct_score`)
- Minimum 50 matches with results for training

**Output:**
- Models saved to `betting_data/models/`
- `outcome_model.txt` - Match outcome model
- `score_model.txt` - Total goals model
- `btts_model.txt` - BTTS model
- `home_dnb_model.txt` - Home Draw No Bet model
- `away_dnb_model.txt` - Away Draw No Bet model
- `over_15_model.txt` - Total Over 1.5 model
- `under_35_model.txt` - Total Under 3.5 model
- `home_over_05_model.txt` - Home Team Over 0.5 model
- `away_over_05_model.txt` - Away Team Over 0.5 model
- `label_encoders.pkl` - Categorical feature encoders
- `feature_columns.json` - Feature column names

### 2. Make Predictions

Generate predictions for upcoming matches:

```bash
# Predict for tomorrow's matches (default)
python manage.py predict_matches

# Predict for specific date
python manage.py predict_matches --date 2026-01-15

# Predict specific type
python manage.py predict_matches --model outcome
python manage.py predict_matches --model score
python manage.py predict_matches --model btts

# Predict all markets with value bets (recommended)
python manage.py predict_matches --model all

# Custom input/output files
python manage.py predict_matches \
    --input-file betting_data/combined_2026-01-15.json \
    --output-file betting_data/predictions_2026-01-15.json

# Predict from Betway file directly
python manage.py predict_matches \
    --input-file betting_data/2026-01-11.json \
    --model all
```

**Input:**
- Match data from `betting_data/combined_*.json`, `betting_data/YYYY-MM-DD.json` (Betway files), or custom file
- Must include: odds, Forebet predictions (optional), team names, league info
- Required odds fields for full predictions:
  - `home_win`, `draw`, `away_win` - Match outcome odds
  - `home_draw_no_bet`, `away_draw_no_bet` - Draw No Bet odds
  - `total_over_1.5`, `total_under_3.5` - Total goals odds
  - `BTTS_yes`, `BTTS_no` - BTTS odds
  - `home_team_over_0.5`, `away_team_over_0.5` - Team total odds

**Output:**
- Predictions saved to `betting_data/predictions_*.json`
- Added fields when using `--model all`:

  **Match Outcome:**
  - `ml_pred` - Predicted outcome (1/X/2)
  - `ml_prob_home`, `ml_prob_draw`, `ml_prob_away` - Outcome probabilities
  - `ml_home_win_value` - Home win value bet (1/0)
  - `ml_draw_value` - Draw value bet (1/0)
  - `ml_away_win_value` - Away win value bet (1/0)

  **Total Goals:**
  - `ml_predicted_total_goals` - Predicted total goals
  - `ml_over_15_prob` - Probability of over 1.5 goals
  - `ml_over_15_value` - Over 1.5 value bet (1/0)
  - `ml_under_35_prob` - Probability of under 3.5 goals
  - `ml_under_35_value` - Under 3.5 value bet (1/0)

  **BTTS:**
  - `ml_btts_prob` - BTTS probability
  - `ml_btts_value` - BTTS value bet (1/0)

  **Draw No Bet:**
  - `ml_home_dnb_prob` - Home Draw No Bet probability
  - `ml_home_dnb_value` - Home DNB value bet (1/0)
  - `ml_away_dnb_prob` - Away Draw No Bet probability
  - `ml_away_dnb_value` - Away DNB value bet (1/0)

  **Team Totals:**
  - `ml_home_over_05_prob` - Home team over 0.5 probability
  - `ml_home_over_05_value` - Home over 0.5 value bet (1/0)
  - `ml_away_over_05_prob` - Away team over 0.5 probability
  - `ml_away_over_05_value` - Away over 0.5 value bet (1/0)

## Feature Engineering

The model uses the following features:

### Odds Features
- `home_win_prob`, `draw_prob`, `away_win_prob` - Implied probabilities from odds
- `odds_ratio` - Ratio of home to away odds
- `favorite` - Binary indicator of favorite team

### Forebet Features
- `forebet_home_prob`, `forebet_draw_prob`, `forebet_away_prob` - Forebet probabilities
- `prob_diff` - Difference between home and away probabilities
- `prob_sum` - Sum of all probabilities
- `avg_goals` - Average predicted goals
- `kelly` - Kelly criterion value
- `has_kelly_value` - Binary indicator for Kelly value

### Predicted Scores
- `home_pred_score`, `away_pred_score` - Predicted scores
- `predicted_total_goals` - Sum of predicted scores

### Market Features
- `btts_prob` - Implied probability from BTTS odds
- `over_1.5_prob` - Implied probability from over 1.5 odds

### Categorical Features (Encoded)
- `home_team_encoded`, `away_team_encoded` - Team identifiers
- `country_encoded`, `league_name_encoded` - League identifiers

## Model Architecture

### Match Outcome Model
- **Type:** Multi-class classification (3 classes)
- **Objective:** `multiclass`
- **Metric:** `multi_logloss`
- **Output:** Probabilities for Home/Draw/Away
- **Value Calculation:** Compares each outcome probability vs implied probability from odds

### Score Model
- **Type:** Regression
- **Objective:** `regression`
- **Metric:** `rmse`
- **Output:** Total goals prediction

### BTTS Model
- **Type:** Binary classification
- **Objective:** `binary`
- **Metric:** `binary_logloss`
- **Output:** Probability and prediction for BTTS
- **Value Calculation:** Compares BTTS probability vs implied probability from BTTS_yes odds

### Additional Market Models
All additional markets use binary classification:
- **Home Draw No Bet** - Predicts if home wins or draws (not away win)
- **Away Draw No Bet** - Predicts if away wins or draws (not home win)
- **Total Over 1.5** - Predicts if total goals > 1.5
- **Total Under 3.5** - Predicts if total goals < 3.5
- **Home Team Over 0.5** - Predicts if home team scores > 0.5
- **Away Team Over 0.5** - Predicts if away team scores > 0.5

Each model:
- **Type:** Binary classification
- **Objective:** `binary`
- **Metric:** `binary_logloss`
- **Value Calculation:** Compares predicted probability vs implied probability from corresponding odds

## Model Performance

Models are evaluated using:
- **Outcome Model:** Accuracy, Log Loss
- **Score Model:** MAE (Mean Absolute Error), RMSE (Root Mean Squared Error)
- **BTTS Model:** Accuracy, Log Loss
- **All Market Models:** Accuracy, Log Loss

Early stopping is used to prevent overfitting (20 rounds patience).

## Value Bet Detection

The system automatically calculates value bets by comparing:
- **Predicted Probability** (from ML model) vs **Implied Probability** (from bookmaker odds)

**Value Bet Formula:**
```
Value = 1 if (Predicted Probability > Implied Probability) else 0
```

Where:
- Implied Probability = 1 / Odds

**Example:**
- Bookmaker offers Home Win at odds of 2.0 (implied prob = 50%)
- ML model predicts Home Win probability = 55%
- Result: `ml_home_win_value = 1` (positive value bet)

This helps identify bets where the model believes the bookmaker has mispriced the market.

## Data Requirements

### Training Data
- `merged_*.json` files with match results
- Required fields:
  - `home_correct_score`, `away_correct_score` - Actual match results
  - `home_win`, `draw`, `away_win` - Betting odds
  - `prob_1`, `prob_x`, `prob_2` - Forebet probabilities
  - `home_team`, `away_team` - Team names
  - `country`, `league_name` - League information

### Prediction Data
- `combined_*.json` files with upcoming matches (includes Forebet predictions)
- `YYYY-MM-DD.json` files (Betway files) - Works directly without Forebet data
- Required fields:
  - Betting odds (from Betway) - All odds fields listed in Input section
  - Forebet predictions (optional but recommended for better accuracy)
  - Team names (`home_team`, `away_team`)
  - League information (`country`, `league_name`)

## Example Workflow

1. **Collect historical data:**
   ```bash
   python manage.py scrape_forebet
   python manage.py scrape_betway
   python manage.py match_betway_forebet
   python manage.py merge_yesterday_results
   ```

2. **Train models:**
   ```bash
   python manage.py train_model --start-date 2025-10-01
   ```

3. **Make predictions:**
   ```bash
   python manage.py predict_matches --date 2026-01-16
   ```

4. **Use predictions:**
   - Load `predictions_*.json` in your application
   - Filter for value bets: `ml_*_value == 1`
   - Use `ml_pred`, `ml_prob_*` fields for match outcomes
   - Use `ml_predicted_total_goals` for score predictions
   - Use `ml_btts_pred` and `ml_btts_value` for BTTS predictions
   - Check all `ml_*_value` fields to find value bets across all markets

**Example: Find all value bets:**
```python
import json

with open('betting_data/predictions_2026-01-15.json', 'r') as f:
    predictions = json.load(f)

# Find matches with any value bets
value_bets = []
for match in predictions:
    value_fields = {k: v for k, v in match.items() 
                   if k.endswith('_value') and v == 1}
    if value_fields:
        value_bets.append({
            'match': f"{match['home_team']} vs {match['away_team']}",
            'value_markets': list(value_fields.keys())
        })
```

## Tips

1. **Regular Retraining:** Retrain models weekly or monthly with new data
2. **Feature Selection:** Monitor feature importance and remove irrelevant features
3. **Hyperparameter Tuning:** Adjust LightGBM parameters for better performance
4. **Ensemble Methods:** Combine predictions from multiple models
5. **Validation:** Always validate predictions against actual results

## Troubleshooting

**Error: "Not enough training data"**
- Collect more historical match data
- Reduce date range restrictions

**Error: "Models not loaded"**
- Train models first using `train_model` command
- Check if model files exist in `betting_data/models/`

**Poor Prediction Accuracy**
- Collect more training data
- Check data quality (missing values, outliers)
- Tune hyperparameters
- Add more features (team form, head-to-head, etc.)

## Market Coverage

The system predicts all major betting markets available in your Betway data:

| Market | Model | Value Field | Probability Field |
|--------|-------|-------------|-------------------|
| Home Win | Outcome | `ml_home_win_value` | `ml_prob_home` |
| Draw | Outcome | `ml_draw_value` | `ml_prob_draw` |
| Away Win | Outcome | `ml_away_win_value` | `ml_prob_away` |
| Home Draw No Bet | Binary | `ml_home_dnb_value` | `ml_home_dnb_prob` |
| Away Draw No Bet | Binary | `ml_away_dnb_value` | `ml_away_dnb_prob` |
| Total Over 1.5 | Binary | `ml_over_15_value` | `ml_over_15_prob` |
| Total Under 3.5 | Binary | `ml_under_35_value` | `ml_under_35_prob` |
| BTTS Yes | Binary | `ml_btts_value` | `ml_btts_prob` |
| Home Team Over 0.5 | Binary | `ml_home_over_05_value` | `ml_home_over_05_prob` |
| Away Team Over 0.5 | Binary | `ml_away_over_05_value` | `ml_away_over_05_prob` |

## Future Enhancements

- Add team form features (last 5 matches)
- Include head-to-head statistics
- Add player injury/suspension data
- Implement ensemble methods
- Add time-series features
- Include weather data
- Add referee statistics
- Add Asian Handicap predictions
- Add Correct Score predictions
- Add First/Last Goal Scorer predictions

