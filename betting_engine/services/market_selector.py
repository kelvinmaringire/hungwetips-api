from datetime import datetime
from pathlib import Path

from betting_engine.models import CombinedMatch
from betting_engine.importers import import_market_selectors


# Odds thresholds
HOME_OVER_MIN_ODDS = 1.25
HOME_DRAW_MIN_ODDS = 1.35
OVER_15_MIN_ODDS = 1.35
HOME_DRAW_MIN_PROBABILITY = 70


class MarketSelector:
    """
    Selects betting markets based on odds thresholds and Forebet predictions.
    Flags matches that meet betting criteria for home_over_05, home_draw, and over_1_5.
    """

    def __init__(self, data_dir=None):
        project_root = Path(__file__).parent.parent.parent
        self.data_dir = Path(data_dir) if data_dir else project_root / 'betting_data'

    def load_combined_data(self, date_str):
        """Load combined tips and odds from database for the given date."""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        combined = CombinedMatch.objects.using('default').filter(date=date_obj).first()

        if not combined:
            raise FileNotFoundError(
                f"No combined matches found for {date_str}. Run match_betway_forebet first."
            )

        matches = combined.matches
        if not isinstance(matches, list):
            raise ValueError(f"CombinedMatch matches field is not a list for {date_str}")

        return matches

    def _get(self, match, key, default=0):
        """Safely get numeric value from match dict, treating None as default."""
        value = match.get(key, default)
        return value if value is not None else default

    def _evaluate_bets(self, match):
        """Evaluate bet conditions for a single match. Returns dict of bet flags."""
        home_over_05 = self._get(match, 'home_team_over_0.5')
        home_draw_odds = self._get(match, 'home_draw_odds')
        over_15 = self._get(match, 'total_over_1.5')

        home_pred = self._get(match, 'forebet_home_pred_score')
        away_pred = self._get(match, 'forebet_away_pred_score')
        prob_1 = self._get(match, 'forebet_prob_1')
        prob_x = self._get(match, 'forebet_prob_x')
        avg_goals = self._get(match, 'forebet_avg_goals')

        home_over_bet = (
            home_over_05 >= HOME_OVER_MIN_ODDS
            and home_pred >= 1
            and home_pred >= away_pred
        )

        home_draw_bet = (
            home_draw_odds >= HOME_DRAW_MIN_ODDS
            and home_pred >= away_pred
            and (prob_1 + prob_x) > HOME_DRAW_MIN_PROBABILITY
        )

        over_15_bet = (
            over_15 >= OVER_15_MIN_ODDS
            and (home_pred + away_pred) >= 2
            and avg_goals > 2
        )

        return {
            'home_over_bet': home_over_bet,
            'away_over_bet': False,
            'home_draw_bet': home_draw_bet,
            'away_draw_bet': False,
            'over_1_5_bet': over_15_bet,
        }

    def select_markets(self, date_str):
        """Apply betting conditions and return matches with bet flags."""
        matches = self.load_combined_data(date_str)
        result = []

        for match in matches:
            flagged = match.copy()
            flagged.update(self._evaluate_bets(match))
            result.append(flagged)

        return result

    def select_and_save(self, date_str, output_filename=None):
        """Select markets and save to database. Returns 'DB'."""
        selected = self.select_markets(date_str)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        try:
            db_result = import_market_selectors(date_obj, selected)
            print(f"Database: Created {db_result['created']}, Updated {db_result['updated']}")
        except Exception as e:
            print(f"⚠ Database save failed: {str(e)}")
            raise

        self._print_summary(selected)
        return "DB"

    def _print_summary(self, matches):
        """Print market selection summary statistics."""
        total = len(matches)
        home_over = sum(1 for m in matches if m.get('home_over_bet', False))
        home_draw = sum(1 for m in matches if m.get('home_draw_bet', False))
        over_15 = sum(1 for m in matches if m.get('over_1_5_bet', False))

        pct = lambda n: f" ({n / total * 100:.2f}%)" if total else ""
        print(f"\nMarket selectors saved to database")
        print(f"  Total matches: {total}")
        print(f"  Home Over 0.5: {home_over} matches{pct(home_over)}")
        print(f"  Home Draw: {home_draw} matches{pct(home_draw)}")
        print(f"  Over 1.5 Goals: {over_15} matches{pct(over_15)}")
