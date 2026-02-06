# HungweTips Workflow Guide

This document outlines the recommended order of operations for running the betting system commands.

## 🚀 Quick Start: Run All Commands at Once

**New!** Use the master workflow command to run all steps automatically:

```bash
# Run complete workflow (all steps)
python manage.py run_workflow

# Skip optional steps
python manage.py run_workflow --skip-betting    # Don't place bets automatically
python manage.py run_workflow --skip-merge      # Skip merging yesterday's results

# Custom date
python manage.py run_workflow --date 2026-01-16

# Stop on first error
python manage.py run_workflow --stop-on-error

# Combine options
python manage.py run_workflow --skip-betting --skip-merge
```

This command will:
- ✅ Run all steps in order
- ✅ Show progress for each step
- ✅ Track timing for each step
- ✅ Handle errors gracefully
- ✅ Show a summary at the end
- ✅ Indicate where it stopped if it fails

**See detailed steps below for manual execution or troubleshooting.**

## Analytics database (`hungwetips_analysis.db`)

Data is written to **both** the default DB (PostgreSQL) and the analytics DB (SQLite: `hungwetips_analysis.db`). If you see errors like:

- `no such column: betting_engine_combinedmatch.matches`
- `no such column: betting_engine_marketselection.selections`

the analytics DB schema is behind. Apply **only** the betting_engine migrations to analytics (other apps like Wagtail are not used on analytics):

```bash
python manage.py migrate betting_engine --database=analytics
```

Run this once after pulling schema changes, or when setting up a new analytics DB.

## 📋 Daily Workflow (For Tomorrow's Matches)

### Step 1: Scrape Forebet Tips
**Command:** `python manage.py scrape_forebet`

**Purpose:** Scrapes tomorrow's match tips and predictions from Forebet.com and previous match results.

**Output:** `betting_data/forebet_tips_YYYY-MM-DD.json`

**What it does:**
- Scrapes tips for tomorrow's matches from all configured leagues
- Extracts: probabilities, predictions, scores, preview links
- Automatically scrapes preview HTML if preview links are available

**When to run:** Daily, preferably in the morning or afternoon before matches

---

### Step 2: Scrape Betway Odds
**Command:** `python manage.py scrape_betway`

**Purpose:** Scrapes betting odds from Betway for tomorrow's matches

**Output:** `betting_data/YYYY-MM-DD.json`

**What it does:**
- Scrapes odds for all markets (1X2, Draw No Bet, Totals, BTTS, Team Totals)
- Extracts detailed odds for each match
- Matches games by team names

**When to run:** After Step 1, or simultaneously (they're independent) 

---

### Step 3: Match Betway Odds with Forebet Tips
**Command:** `python manage.py match_betway_forebet`

**Purpose:** Combines Betway odds with Forebet predictions using fuzzy matching

**Output:** `betting_data/combined_YYYY-MM-DD.json`

**What it does:**
- Matches Betway games with Forebet tips using team name similarity
- Combines odds and predictions into single records
- Shows match confidence scores

**When to run:** After Steps 1 and 2 are complete

**Options:**
```bash
# Custom similarity threshold (default: 85)
python manage.py match_betway_forebet --threshold 90

# Custom date
python manage.py match_betway_forebet --date 2026-01-16
```

---


### Step 4: Merge Yesterday's Results
**Command:** `python manage.py merge_yesterday_results`

**Purpose:** Combines yesterday's tips/odds with actual match results to create training data

**Output:** `betting_data/merged_YYYY-MM-DD.json`

**What it does:**
- Loads combined tips & odds from yesterday (`combined_YYYY-MM-DD.json`)
- Loads actual results from Forebet (`forebet_results_YYYY-MM-DD.json`)
- Merges them using `match_id`
- Creates training data for ML model training
- **Important:** The ML training process combines ALL available `merged_*.json` files from all dates

**When to run:** Daily, after matches have finished (usually next day)

**Options:**
```bash
# Custom date
python manage.py merge_yesterday_results --date 2026-01-13

# Custom output filename
python manage.py merge_yesterday_results --output custom_merged.json
```

**Why it's important:**
- Creates historical data for training ML models
- Each merged file adds to the training dataset
- **ML training automatically combines ALL `merged_*.json` files** from all dates
- Example: If you have `merged_2026-01-10.json`, `merged_2026-01-11.json`, `merged_2026-01-13.json`
  - Training will use ALL of them combined (not just one)
  - More historical data = better model performance
- Allows you to evaluate prediction accuracy
- Builds dataset for continuous model improvement

**Note:** Previews are automatically scraped during Step 1 (`scrape_forebet`), so no separate preview scraping step is needed.

---

### Step 5: Train ML Models (Optional)
**Command:** `python manage.py train_model --model all`

**Purpose:** Train machine learning models separately (optional step)

**Note:** This step is optional. If skipped, Step 6 (`predict_matches`) will train models automatically. If this step runs, Step 6 will skip training to avoid double training.

---

### Step 6: Make Predictions (Trains automatically if Step 5 skipped)
**Command:** `python manage.py predict_matches --model all`

**Purpose:** Trains machine learning models on latest data (if Step 5 skipped) and makes predictions

**Output:** 
- Models kept in memory (for immediate predictions)
- Predictions saved to `betting_data/predictions_YYYY-MM-DD.json`
- Training metrics saved to `betting_data/models/training_metrics_YYYY-MM-DD.json`

**What it does:**
- **Trains models first** on ALL available `merged_*.json` files (includes yesterday's new data)
- Trains models for all betting markets (outcome, score, BTTS, all market models)
- **Keeps models in memory** for immediate prediction
- Makes predictions on tomorrow's matches
- Saves training metrics separately for tracking

**Data Sources:**
- **Training Data:** ALL `merged_*.json` files (combines all dates automatically)
  - Example: `merged_2026-01-10.json`, `merged_2026-01-11.json`, `merged_2026-01-13.json` → All combined
  - Each file contains: tips + odds + actual results
  - More files = more training data = better models
  - **Trains daily** to include latest results
  
- **Prediction Data:** Single `combined_YYYY-MM-DD.json` file (tomorrow's matches)
  - Example: `combined_2026-01-15.json` (from Step 3)
  - Contains: tips + odds (no results yet - matches haven't been played)

**When to run:**
- **Daily:** Run every morning to train on latest data and get predictions
- **First time:** Before making predictions (needs at least 50 matches with results)

**Options:**
```bash
# Train and predict (default - trains every time)
python manage.py predict_matches --model all

# Skip training, use existing models
python manage.py predict_matches --model all --no-train

# Custom test split for training
python manage.py predict_matches --model all --test-size 0.3
```

**Options:**
```bash
# Train specific model
python manage.py train_model --model outcome
python manage.py train_model --model score
python manage.py train_model --model btts

# Custom date range
python manage.py train_model --start-date 2025-10-01 --end-date 2026-01-15

# Custom test split
python manage.py train_model --test-size 0.3
```

**Requirements:**
- Need at least 50 matches with results in `merged_*.json` files
- Historical data must include actual match results (`home_correct_score`, `away_correct_score`)

---

**Note:** Step 5 now combines training and prediction. Models are trained fresh daily with latest data, then immediately used for predictions. This ensures you always use the most up-to-date models.

**Options:**
```bash
# Predict for specific date
python manage.py predict_matches --date 2026-01-16

# Custom input/output files
python manage.py predict_matches \
    --input-file betting_data/combined_2026-01-16.json \
    --output-file betting_data/predictions_2026-01-16.json

# Predict specific model type
python manage.py predict_matches --model outcome
python manage.py predict_matches --model score
python manage.py predict_matches --model btts
```

**Output Fields:**
- `ml_*_value` - Value bet indicators (1 = bet, 0 = skip)
- `ml_*_prob` - Predicted probabilities
- `ml_pred` - Predicted match outcome (1/X/2)

---

### Step 5: Select Markets
**Command:** `python manage.py market_selector`

**Purpose:** Selects betting markets based on odds thresholds and Forebet predictions

**Output:** `betting_data/market_selectors_YYYY-MM-DD.json`

**What it does:**
- Loads combined tips & odds from `combined_YYYY-MM-DD.json`
- Applies betting conditions based on odds thresholds and Forebet predictions:
  - **Home Over 0.5:** `home_team_over_0.5 >= 1.25` and Forebet predicts home team scores ≥1
  - **Away Over 0.5:** `away_team_over_0.5 >= 1.30` and Forebet predicts away team scores ≥2
  - **Home Draw:** `home_draw_odds >= 1.35` and Forebet probability (home + draw) > 70%
  - **Away Draw:** `away_draw_odds >= 1.30` and Forebet probability (away + draw) > 70%
  - **Over 1.5 Goals:** `total_over_1.5 >= 1.35` and Forebet predicts total goals > 2
- Flags matches with boolean indicators (`home_over_bet`, `away_over_bet`, `home_draw_bet`, `away_draw_bet`, `over_1_5_bet`)
- Creates market selector file with all matches and their betting flags

**When to run:** After Step 3 (match_betway_forebet), before placing bets

**Options:**
```bash
# Custom date
python manage.py market_selector --date 2026-01-25

# Custom output filename
python manage.py market_selector --date 2026-01-25 --output custom_selectors.json
```

**Requirements:**
- Combined file from Step 3 must exist
- File must contain Forebet predictions and Betway odds

---

### Step 6: Automate Betting
**Command:** `python manage.py automate_betting`

**Purpose:** Automatically places single bets on Betway based on market selectors

**Output:** 
- Places bets via browser automation (one bet at a time)
- Saves bet information to `betting_data/single_bets_YYYY-MM-DD.json`

**What it does:**
- Reads market selector data from `market_selectors_YYYY-MM-DD.json`
- Extracts bets based on boolean flags:
  - `home_over_bet` → Home Team Over 0.5 Goals
  - `away_over_bet` → Away Team Over 0.5 Goals
  - `home_draw_bet` → Home or Draw (Double Chance)
  - `away_draw_bet` → Away or Draw (Double Chance)
  - `over_1_5_bet` → Total Goals Over 1.5
- Places each bet individually (single bets, not accumulators)
- Confirms each bet immediately after placing
- Uses browser automation (Playwright) to interact with Betway website
- Logs comprehensive bet information with status (placed/failed)

**When to run:** After Step 5 (market_selector), when you're ready to place bets

**Options:**
```bash
# Use specific date
python manage.py automate_betting --date 2026-01-25
```

**Requirements:**
- Betway account logged in
- Market selector file must exist
- Browser automation configured

**⚠️ Warning:** This command will place real bets. Test thoroughly before using with real money!

**Note:** This workflow uses market selectors (based on odds thresholds and Forebet predictions) instead of ML predictions. For ML-based betting, use the prediction workflow (Steps 5-6 in the ML workflow section).

---

## 📊 Post-Match Workflow (For Yesterday's Results)



## 🔄 Complete Daily Cycle

### Morning/Afternoon (Before Matches)
```bash
# 1. Get tomorrow's tips (includes preview scraping)
python manage.py scrape_forebet

# 2. Get tomorrow's odds
python manage.py scrape_betway

# 3. Combine them
python manage.py match_betway_forebet

# 4. Merge yesterday's results (for training data)
python manage.py merge_yesterday_results

# 5. Select markets based on odds thresholds and Forebet predictions
python manage.py market_selector

# 6. Place bets (if automated) - uses market selectors for single bets
python manage.py automate_betting
```

**Note:** This workflow uses market selectors (odds thresholds + Forebet predictions) for betting. For ML-based predictions and betting, see the ML workflow section below.

---

## 🤖 ML-Based Workflow (Alternative)

If you prefer to use ML predictions instead of market selectors:

```bash
# Steps 1-4 are the same
python manage.py scrape_forebet
python manage.py scrape_betway
python manage.py match_betway_forebet
python manage.py merge_yesterday_results

# ML-specific steps
python manage.py train_model --model all  # Optional: train separately
python manage.py predict_matches --model all  # Trains automatically if Step 5 skipped
python manage.py automate_betting  # Uses predictions instead of market selectors
```

**Difference:** ML workflow uses trained models to predict value bets, while market selector workflow uses simple rules based on odds thresholds and Forebet predictions.

### Next Day (After Matches)
```bash
# Merge results for training data (adds to historical dataset)
python manage.py merge_yesterday_results

# (Periodically - weekly/monthly) Retrain models with all accumulated data
python manage.py train_model --model all
```

---

## 🎯 Quick Reference

| Step | Command | Frequency | Dependencies |
|------|---------|-----------|--------------|
| 1 | `scrape_forebet` | Daily | None |
| 2 | `scrape_betway` | Daily | None |
| 3 | `match_betway_forebet` | Daily | Steps 1, 2 |
| 4 | `merge_yesterday_results` | Daily | Previous day's data |
| 5 | `market_selector` | Daily | Step 3 |
| 6 | `automate_betting` | Daily | Step 5 |

---

## 📝 Example Complete Workflow

### Day 1: Initial Setup
```bash
# First time setup - collect historical data
python manage.py scrape_forebet
python manage.py scrape_betway
python manage.py match_betway_forebet

# Wait for matches to finish, then merge results
python manage.py merge_yesterday_results

# Train models (combines all merged_*.json files)
# Repeat until you have enough data (50+ matches)
python manage.py train_model --model all
```

### Day 2+: Daily Operations
```bash
# Morning routine - Get tomorrow's data
python manage.py scrape_forebet
python manage.py scrape_betway
python manage.py match_betway_forebet
# Creates: combined_2026-01-16.json (tomorrow's matches - no results yet)

# Merge yesterday's results (adds to training dataset)
python manage.py merge_yesterday_results
# Creates: merged_2026-01-15.json (yesterday's tips + odds + results)

# Option A: Train separately, then predict (skip training in predict step)
python manage.py train_model --model all
python manage.py predict_matches --model all --no-train --date 2026-01-16

# Option B: Train and predict in one command (recommended - simpler)
python manage.py predict_matches --model all --date 2026-01-16
# Training: Uses ALL merged_*.json files (includes yesterday's new data)
# Prediction: Uses combined_2026-01-16.json (from Step 3)
# Models stay in memory for immediate prediction
# Training metrics saved to: betting_data/models/training_metrics_YYYY-MM-DD.json

# Review predictions, then place bets
python manage.py automate_betting --date 2026-01-16
```

---

## ⚙️ Advanced Workflows

### Workflow A: Manual Review Before Betting
```bash
# Get data and predictions
python manage.py scrape_forebet
python manage.py scrape_betway
python manage.py match_betway_forebet
python manage.py merge_yesterday_results
python manage.py predict_matches --model all

# Review predictions_*.json file manually
# Then manually place bets on Betway
```

### Workflow B: Automated Full Cycle (Recommended)
```bash
# Run all steps automatically with progress tracking
python manage.py run_workflow

# Or with bash (alternative, but less informative)
python manage.py scrape_forebet && \
python manage.py scrape_betway && \
python manage.py match_betway_forebet && \
python manage.py merge_yesterday_results && \
python manage.py predict_matches --model all && \
python manage.py automate_betting
```

### Workflow C: Focus on Specific Markets
```bash
# Only predict specific markets
python manage.py predict_matches --model outcome
python manage.py predict_matches --model btts
```

---

## 🚨 Important Notes

1. **Timing:** Run scraping commands during business hours when websites are accessible
2. **Rate Limiting:** Commands include delays to avoid being blocked
3. **Data Quality:** Ensure you have enough historical data (50+ matches) before training models
4. **Model Updates:** Retrain models regularly (weekly/monthly) as you collect more data
5. **Betting Safety:** Always review predictions before placing bets, especially with real money
6. **Error Handling:** If a command fails, check logs and retry. Some commands can be run independently.

---

## 🔍 Troubleshooting

**Problem:** "Not enough training data"
- **Solution:** Collect more historical data by running Steps 1-3 and Step 4 for multiple days. The training process combines ALL `merged_*.json` files, so each day adds to your dataset.

**Problem:** "Models not loaded"
- **Solution:** Run `python manage.py train_model --model all` first

**Problem:** "No matches found"
- **Solution:** Check date format (YYYY-MM-DD) and ensure data files exist

**Problem:** "Scraping failed"
- **Solution:** Check internet connection, website availability, and retry

---

## 📚 Related Documentation

- **Prediction Models:** See `betting_engine/services/README_PREDICTION.md`
- **Individual Commands:** Use `python manage.py <command> --help` for detailed options
- **Master Workflow Command:** `python manage.py run_workflow --help` for automated workflow options

