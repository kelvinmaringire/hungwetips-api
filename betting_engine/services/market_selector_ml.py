"""
ML-based filter for market selector bets.
Trains on MergedMatch data, scores bets by predicted win probability, keeps top 75%.
"""
import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

# Match market_selector thresholds
HOME_OVER_MIN_ODDS = 1.25
HOME_DRAW_MIN_ODDS = 1.35
OVER_15_MIN_ODDS = 1.35
HOME_DRAW_MIN_PROBABILITY = 70

BET_TYPES = ['home_over_05', 'home_draw', 'over_1_5']
MIN_TRAINING_SAMPLES = 30
TOP_LEAGUES_COUNT = 20
KEEP_FRACTION = 0.75


def _get(match, key, default=0):
    """Safe get with fallback for forebet_/normalized keys."""
    value = match.get(key)
    if value is not None:
        return value
    forebet_key = f'forebet_{key}' if not key.startswith('forebet_') else key.replace('forebet_', '')
    if forebet_key != key:
        value = match.get(forebet_key)
    if value is not None:
        return value
    return default


def _would_qualify(row, bet_type):
    """Replicate market_selector rules. Returns True if row qualifies for this bet type."""
    home_over_05 = _get(row, 'home_team_over_0.5')
    home_draw_odds = _get(row, 'home_draw_odds')
    over_15 = _get(row, 'total_over_1.5')
    home_pred = _get(row, 'home_pred_score') or _get(row, 'forebet_home_pred_score')
    away_pred = _get(row, 'away_pred_score') or _get(row, 'forebet_away_pred_score')
    prob_1 = _get(row, 'prob_1') or _get(row, 'forebet_prob_1')
    prob_x = _get(row, 'prob_x') or _get(row, 'forebet_prob_x')
    avg_goals = _get(row, 'avg_goals') or _get(row, 'forebet_avg_goals')

    if bet_type == 'home_over_05':
        return (
            home_over_05 >= HOME_OVER_MIN_ODDS
            and home_pred >= 1
            and home_pred >= away_pred
        )
    if bet_type == 'home_draw':
        return (
            home_draw_odds >= HOME_DRAW_MIN_ODDS
            and home_pred >= away_pred
            and (prob_1 + prob_x) > HOME_DRAW_MIN_PROBABILITY
        )
    if bet_type == 'over_1_5':
        return (
            over_15 >= OVER_15_MIN_ODDS
            and (home_pred + away_pred) >= 2
            and avg_goals > 2
        )
    return False


def _eval_win(row, bet_type):
    """Return 1 if won, 0 if lost. Assumes row has home_correct_score, away_correct_score."""
    home = row.get('home_correct_score')
    away = row.get('away_correct_score')
    if home is None or away is None:
        return None
    if bet_type == 'home_over_05':
        return 1 if home >= 1 else 0
    if bet_type == 'home_draw':
        return 1 if home >= away else 0
    if bet_type == 'over_1_5':
        return 1 if (home + away) >= 2 else 0
    return None


def _get_odds(row, bet_type):
    """Get odds for bet type from row."""
    if bet_type == 'home_over_05':
        return row.get('home_team_over_0.5')
    if bet_type == 'home_draw':
        return row.get('home_draw_odds')
    if bet_type == 'over_1_5':
        return row.get('total_over_1.5')
    return None


class MarketSelectorML:
    """
    ML filter for market selector bets.
    Trains on MergedMatch, filters bets to top 75% by predicted win probability.
    """

    def __init__(self, models_dir=None):
        project_root = Path(settings.BASE_DIR) if hasattr(settings, 'BASE_DIR') else Path(__file__).parent.parent.parent
        self.models_dir = Path(models_dir) if models_dir else project_root / 'betting_data' / 'models'
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._models = {}
        self._league_encoder = None
        self._feature_cols = None

    def _extract_features(self, row, bet_type):
        """Build feature dict for model. Handles both MergedMatch and CombinedMatch key formats."""
        home_over = _get(row, 'home_team_over_0.5', 0)
        home_draw = _get(row, 'home_draw_odds', 0)
        over_15 = _get(row, 'total_over_1.5', 0)
        home_pred = _get(row, 'home_pred_score') or _get(row, 'forebet_home_pred_score')
        away_pred = _get(row, 'away_pred_score') or _get(row, 'forebet_away_pred_score')
        prob_1 = _get(row, 'prob_1') or _get(row, 'forebet_prob_1')
        prob_x = _get(row, 'prob_x') or _get(row, 'forebet_prob_x')
        avg_goals = _get(row, 'avg_goals') or _get(row, 'forebet_avg_goals')

        country = row.get('country') or row.get('forebet_country') or ''
        league = row.get('league_name') or row.get('forebet_league_name') or ''
        league_key = f"{country}_{league}".strip('_') or 'unknown'

        odds = _get_odds(row, bet_type) or 0
        implied_prob = 1.0 / float(odds) if odds and float(odds) > 0 else 0

        return {
            'home_team_over_0.5': float(home_over) if home_over else 0,
            'home_draw_odds': float(home_draw) if home_draw else 0,
            'total_over_1.5': float(over_15) if over_15 else 0,
            'home_pred_score': float(home_pred) if home_pred is not None else 0,
            'away_pred_score': float(away_pred) if away_pred is not None else 0,
            'prob_1': float(prob_1) if prob_1 is not None else 0,
            'prob_x': float(prob_x) if prob_x is not None else 0,
            'prob_1_plus_prob_x': float(prob_1 or 0) + float(prob_x or 0),
            'pred_total_goals': float(home_pred or 0) + float(away_pred or 0),
            'avg_goals': float(avg_goals) if avg_goals is not None else 0,
            'implied_prob': implied_prob,
            'league_key': league_key,
        }

    def _get_league_encoded(self, league_key):
        """Encode league. Uses persisted encoder or returns 0 if not available."""
        if self._league_encoder is None:
            return 0
        try:
            return self._league_encoder.get(league_key, -1)
        except Exception:
            return -1

    def build_training_data(self):
        """Build training DataFrame from MergedMatch. Returns list of dicts."""
        from betting_engine.models import MergedMatch
        from collections import Counter

        rows = []
        league_counts = Counter()

        for mm in MergedMatch.objects.all().order_by('date'):
            for row in mm.rows or []:
                if row.get('home_correct_score') is None or row.get('away_correct_score') is None:
                    continue
                country = row.get('country') or ''
                league = row.get('league_name') or ''
                league_key = f"{country}_{league}".strip('_') or 'unknown'
                league_counts[league_key] += 1

                for bt in BET_TYPES:
                    if not _would_qualify(row, bt):
                        continue
                    won = _eval_win(row, bt)
                    if won is None:
                        continue
                    feats = self._extract_features(row, bt)
                    feats['bet_type'] = bt
                    feats['target'] = won
                    rows.append(feats)

        top_leagues = [k for k, _ in league_counts.most_common(TOP_LEAGUES_COUNT)]
        self._league_encoder = {k: i for i, k in enumerate(top_leagues)}

        for r in rows:
            r['league_encoded'] = self._league_encoder.get(r['league_key'], -1)

        return rows

    def _get_feature_cols(self):
        """Feature columns for model (excluding target, bet_type, league_key)."""
        return [
            'home_team_over_0.5', 'home_draw_odds', 'total_over_1.5',
            'home_pred_score', 'away_pred_score', 'prob_1', 'prob_x',
            'prob_1_plus_prob_x', 'pred_total_goals', 'avg_goals',
            'implied_prob', 'league_encoded',
        ]

    def train_models(self):
        """Train LGBM per bet_type, save to disk. Returns dict of metrics."""
        import pandas as pd
        import joblib
        from lightgbm import LGBMClassifier

        data = self.build_training_data()
        if not data:
            return {'error': 'No training data'}

        df = pd.DataFrame(data)
        self._feature_cols = self._get_feature_cols()
        metrics = {}

        for bt in BET_TYPES:
            df_bt = df[df['bet_type'] == bt]
            n = len(df_bt)
            metrics[bt] = {'samples': n}

            if n < MIN_TRAINING_SAMPLES:
                metrics[bt]['skipped'] = True
                metrics[bt]['reason'] = f'Insufficient samples ({n} < {MIN_TRAINING_SAMPLES})'
                continue

            X = df_bt[self._feature_cols].fillna(0)
            y = df_bt['target']

            model = LGBMClassifier(n_estimators=100, max_depth=5, random_state=42, verbose=-1)
            model.fit(X, y)

            preds = model.predict(X)
            acc = (preds == y).mean()
            metrics[bt]['accuracy'] = round(float(acc), 4)

            path = self.models_dir / f'market_selector_ml_{bt}.joblib'
            joblib.dump(model, path)

        encoder_path = self.models_dir / 'market_selector_ml_league_encoder.joblib'
        joblib.dump({'encoder': self._league_encoder, 'feature_cols': self._feature_cols}, encoder_path)

        return metrics

    def _load_models(self):
        """Load saved models. Returns True if all loaded."""
        import joblib

        if self._models:
            return True

        try:
            enc_path = self.models_dir / 'market_selector_ml_league_encoder.joblib'
            if not enc_path.exists():
                return False
            enc_data = joblib.load(enc_path)
            self._league_encoder = enc_data.get('encoder', {})
            self._feature_cols = enc_data.get('feature_cols', self._get_feature_cols())

            for bt in BET_TYPES:
                path = self.models_dir / f'market_selector_ml_{bt}.joblib'
                if path.exists():
                    self._models[bt] = joblib.load(path)
            return len(self._models) > 0
        except Exception as e:
            logger.warning(f"Failed to load ML models: {e}")
            return False

    def _row_to_feature_vector(self, game, bet_type):
        """Convert game dict to feature vector for prediction."""
        feats = self._extract_features(game, bet_type)
        feats['league_encoded'] = self._get_league_encoded(feats['league_key'])
        return feats

    def filter_bets(self, bets):
        """
        Score each bet by ML win probability, keep top 75%.
        Returns (selected_bets, rejected_bets) - selected_bets for placement.
        If models missing, returns (bets, []).
        """
        if not bets:
            return bets, []

        if not self._load_models():
            return bets, []

        import pandas as pd

        try:
            for bet in bets:
                game = bet.get('game', bet)
                bt = bet.get('bet_type')
                if bt not in self._models:
                    bet['ml_win_prob'] = 1.0
                    continue
                feats = self._row_to_feature_vector(game, bt)
                X = pd.DataFrame([{c: feats.get(c, 0) for c in self._feature_cols}])
                X = X[self._feature_cols].fillna(0)
                proba = self._models[bt].predict_proba(X)[0]
                bet['ml_win_prob'] = float(proba[1]) if len(proba) > 1 else float(proba[0])

            ranked = sorted(bets, key=lambda b: b.get('ml_win_prob', 1.0), reverse=True)
            keep_count = max(1, int(len(ranked) * KEEP_FRACTION))
            selected = ranked[:keep_count]
            rejected = ranked[keep_count:]
            return selected, rejected
        except Exception as e:
            logger.warning(f"ML filter failed: {e}. Returning all bets.")
            return bets, []
