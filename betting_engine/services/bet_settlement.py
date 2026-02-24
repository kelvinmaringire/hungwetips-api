"""
Bet settlement service: merges SingleBetSnapshot with MergedMatch by match_id and date
to determine which bets won or lost. Only processes home_over_05, home_draw, over_1_5.
"""
from datetime import datetime

from betting_engine.models import SingleBetSnapshot, MergedMatch
from betting_engine.importers import import_bet_settlements

SETTLED_BET_TYPES = {'home_over_05', 'home_draw', 'over_1_5'}


class BetSettlement:
    """Merge bets with results to determine won/lost status."""

    def load_bets(self, date_str):
        """Load SingleBetSnapshot for date. Return bets list (only settled bet types)."""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        snapshot = SingleBetSnapshot.objects.using('default').filter(date=date_obj).first()
        if not snapshot or not isinstance(snapshot.snapshot, dict):
            return []
        bets = snapshot.snapshot.get('bets', [])
        return [b for b in bets if b.get('bet_type') in SETTLED_BET_TYPES]

    def load_results(self, date_str):
        """Load MergedMatch for date. Return {match_id: row} for lookup."""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        merged = MergedMatch.objects.using('default').filter(date=date_obj).first()
        if not merged or not isinstance(merged.rows, list):
            return {}
        return {row.get('match_id'): row for row in merged.rows if row.get('match_id') is not None}

    def _evaluate_settlement(self, bet, merged_row):
        """Return 'won', 'lost', or 'pending' based on bet_type and scores."""
        home = merged_row.get('home_correct_score')
        away = merged_row.get('away_correct_score')
        if home is None or away is None:
            return 'pending'

        bet_type = bet.get('bet_type')
        if bet_type == 'home_over_05':
            return 'won' if home >= 1 else 'lost'
        if bet_type == 'home_draw':
            return 'won' if home >= away else 'lost'
        if bet_type == 'over_1_5':
            return 'won' if (home + away) >= 2 else 'lost'
        return 'pending'

    def settle(self, date_str):
        """
        Merge bets with results by match_id and date.
        Output: list of dicts with common fields + settlement_status.
        """
        bets = self.load_bets(date_str)
        results = self.load_results(date_str)
        settlements = []

        for bet in bets:
            match_id = bet.get('match_id') or (bet.get('game_data') or {}).get('forebet_match_id')
            merged_row = results.get(match_id) if match_id else None

            home_team = (bet.get('game_data') or {}).get('home_team') or (merged_row or {}).get('home_team')
            away_team = (bet.get('game_data') or {}).get('away_team') or (merged_row or {}).get('away_team')

            home_score = merged_row.get('home_correct_score') if merged_row else None
            away_score = merged_row.get('away_correct_score') if merged_row else None

            settlement_status = self._evaluate_settlement(bet, merged_row) if merged_row else 'pending'

            record = {
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'home_correct_score': home_score,
                'away_correct_score': away_score,
                'bet_id': bet.get('bet_id'),
                'bet_type': bet.get('bet_type'),
                'team': bet.get('team'),
                'odds': bet.get('odds'),
                'status': bet.get('status'),
                'settlement_status': settlement_status,
            }
            settlements.append(record)

        return settlements

    def settle_and_save(self, date_str):
        """Settle and save to BetSettlementSnapshot. Return 'DB'."""
        settlements = self.settle(date_str)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        db_result = import_bet_settlements(date_obj, settlements)
        print(f"Database: Created {db_result['created']}, Updated {db_result['updated']}")
        return "DB"
