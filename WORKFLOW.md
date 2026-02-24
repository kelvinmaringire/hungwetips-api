# HungweTips Workflow Guide

This document outlines the recommended order of operations for running the betting system commands.

## 🚀 Quick Start: Run All Commands at Once

Use the master workflow command to run all steps automatically:

```bash
# Run complete workflow (all steps)
python manage.py run_workflow

docker exec hungwetips_web python manage.py run_workflow

# Skip optional steps
python manage.py run_workflow --skip-betting      # Don't place bets automatically
python manage.py run_workflow --skip-merge        # Skip merging yesterday's results
python manage.py run_workflow --skip-settlement   # Skip bet settlement step
python manage.py run_workflow --skip-ml-train     # Skip training market selector ML models

# Custom date (default: tomorrow SAST)
python manage.py run_workflow --date 2026-01-16

# Stop on first error (default: continue and report)
python manage.py run_workflow --stop-on-error

# Combine options
python manage.py run_workflow --skip-betting --skip-merge --date 2026-01-16
```

**What it does:**
- Runs all 8 steps in order
- Shows progress and timing for each step
- Handles errors gracefully (continues unless `--stop-on-error`)
- Prints summary at the end

---

## 📋 Workflow Steps (from `run_workflow.py`)

| Step | Command | Date Used | Required |
|------|---------|-----------|----------|
| 1 | `scrape_forebet` | — | Yes |
| 2 | `scrape_betway` | — | Yes |
| 3 | `match_betway_forebet` | Target date | Yes |
| 4 | `merge_yesterday_results` | Yesterday | No (`--skip-merge`) |
| 5 | `bet_settlement` | Yesterday | No (`--skip-settlement`) |
| 6 | `market_selector` | Target date | Yes |
| 7 | `train_market_selector_ml` | Market selector data | No (`--skip-ml-train`) |
| 8 | `automate_betting` | Target date | No (`--skip-betting`) |

**Date behavior:** Default target date is **tomorrow (SAST)**. Steps 4 and 5 use **yesterday** internally for results/settlement.

---

### Step 1: Scrape Forebet Tips
**Command:** `python manage.py scrape_forebet`

Scrapes tomorrow's match tips and predictions from Forebet.com.

**Output:** `betting_data/forebet_tips_YYYY-MM-DD.json`

---

### Step 2: Scrape Betway Odds
**Command:** `python manage.py scrape_betway`

Scrapes betting odds from Betway for tomorrow's matches.

**Output:** `betting_data/YYYY-MM-DD.json`

---

### Step 3: Match Betway with Forebet
**Command:** `python manage.py match_betway_forebet --date YYYY-MM-DD`

Combines Betway odds with Forebet predictions using fuzzy matching.

**Output:** `betting_data/combined_YYYY-MM-DD.json`

**Options:** `--threshold 90` (default 85), `--date YYYY-MM-DD`

---

### Step 4: Merge Yesterday Results
**Command:** `python manage.py merge_yesterday_results`

Merges yesterday's tips/odds with actual match results for training data.

**Output:** `betting_data/merged_YYYY-MM-DD.json`

**Options:** `--date YYYY-MM-DD`, `--output custom_merged.json`

---

### Step 5: Bet Settlement
**Command:** `python manage.py bet_settlement`

Records bet settlement status from Betway for yesterday's bets.

**Options:** `--date YYYY-MM-DD` (default: yesterday)

---

### Step 6: Select Markets
**Command:** `python manage.py market_selector --date YYYY-MM-DD`

Selects betting markets based on odds thresholds and Forebet predictions.

**Output:** `betting_data/market_selectors_YYYY-MM-DD.json`

**Conditions (examples):**
- **Home Over 0.5:** `home_team_over_0.5 >= 1.25` and Forebet predicts home scores ≥1
- **Home Draw:** `home_draw_odds >= 1.35` and Forebet (home + draw) > 70%
- **Over 1.5 Goals:** `total_over_1.5 >= 1.35` and Forebet predicts total goals > 2

---

### Step 7: Train Market Selector ML
**Command:** `python manage.py train_market_selector_ml`

Trains LGBM models per bet type (home_over_05, home_draw, over_1_5) from market selector data. Used by the ML filter during automate_betting to keep top 75% of bets by predicted win probability.

**Output:** Models in `betting_data/models/market_selector_ml_*.joblib`

**When to run:** After market_selector. Periodically (e.g. weekly) or before first use. Requires ≥30 MergedMatch samples per bet type.

---

### Step 8: Automate Betting
**Command:** `python manage.py automate_betting --date YYYY-MM-DD`

Places single bets on Betway based on market selectors (browser automation).

**Output:** `betting_data/single_bets_YYYY-MM-DD.json`

**⚠️ Warning:** Places real bets. Test thoroughly before using with real money.

---

## 🔄 Daily Cycle (Manual)

```bash
# Morning/afternoon (before matches)
python manage.py scrape_forebet
python manage.py scrape_betway
python manage.py match_betway_forebet
python manage.py merge_yesterday_results
python manage.py bet_settlement
python manage.py market_selector
python manage.py train_market_selector_ml
python manage.py automate_betting
```

---

## 🎯 Quick Reference

| Step | Command | Dependencies |
|------|---------|--------------|
| 1 | `scrape_forebet` | None |
| 2 | `scrape_betway` | None |
| 3 | `match_betway_forebet` | Steps 1, 2 |
| 4 | `merge_yesterday_results` | Previous day's data |
| 5 | `bet_settlement` | Previous day's bets |
| 6 | `market_selector` | Step 3 |
| 7 | `train_market_selector_ml` | Step 6 (market_selector) |
| 8 | `automate_betting` | Step 7 |

---

## 🚨 Important Notes

1. **Timing:** Run scraping during business hours when sites are accessible.
2. **Rate limiting:** Commands include delays to avoid being blocked.
3. **Betting safety:** Review predictions before placing real bets.
4. **Error handling:** If a command fails, check logs and retry. Use `--stop-on-error` to halt on first failure.

---

## 🔍 Troubleshooting

- **"No matches found"** — Check date format (YYYY-MM-DD) and that data files exist.
- **"Scraping failed"** — Check internet connection and site availability.
- **Individual commands:** `python manage.py <command> --help`
