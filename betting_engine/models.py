from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class BetwayOdds(models.Model):
    """Betway odds data - stores full match and odds information for a date."""
    date = models.DateField(db_index=True, unique=True)
    matches = models.JSONField(default=list)  # List of match objects with all odds data
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        match_count = len(self.matches) if isinstance(self.matches, list) else 0
        return f"BetwayOdds({self.date}, {match_count} matches)"


class ForebetTip(models.Model):
    """Forebet prediction/tip data - stores full match and prediction information for a date."""
    date = models.DateField(db_index=True, unique=True)
    tips = models.JSONField(default=list)  # List of tip objects with all prediction data
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        tip_count = len(self.tips) if isinstance(self.tips, list) else 0
        return f"ForebetTip({self.date}, {tip_count} tips)"


class ForebetResult(models.Model):
    """Forebet match result data - stores full result information for a date."""
    date = models.DateField(db_index=True, unique=True)
    results = models.JSONField(default=list)  # List of result objects with all score data
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        result_count = len(self.results) if isinstance(self.results, list) else 0
        return f"ForebetResult({self.date}, {result_count} results)"


class CombinedMatch(models.Model):
    """Matched Betway + Forebet data - stores full combined match information for a date."""
    date = models.DateField(db_index=True, unique=True)
    matches = models.JSONField(default=list)  # List of combined match objects with all odds and prediction data
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        match_count = len(self.matches) if isinstance(self.matches, list) else 0
        return f"CombinedMatch({self.date}, {match_count} matches)"


class MarketSelection(models.Model):
    """Market selection flags for betting - stores full match and selection data for a date."""
    date = models.DateField(db_index=True, unique=True)
    selections = models.JSONField(default=list)  # List of selection objects with all market flags and odds data
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        selection_count = len(self.selections) if isinstance(self.selections, list) else 0
        return f"MarketSelection({self.date}, {selection_count} selections)"


class SingleBetSnapshot(models.Model):
    """Single bet snapshot from automation for a date."""
    date = models.DateField(unique=True, db_index=True)
    snapshot = models.JSONField(default=dict)  # Dictionary with timestamp, total_bets, placed_bets, failed_bets, bets list
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        bets_count = len(self.snapshot.get('bets', [])) if isinstance(self.snapshot, dict) else 0
        return f"SingleBetSnapshot({self.date}, {bets_count} bets)"


class MergedMatch(models.Model):
    """Merged tips and results data - stores yesterday's combined tips with actual results for historical analysis."""
    date = models.DateField(db_index=True, unique=True)
    rows = models.JSONField(default=list)  # List of merged tip/result dictionaries
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        row_count = len(self.rows) if isinstance(self.rows, list) else 0
        return f"MergedMatch({self.date}, {row_count} rows)"


class BetSettlementSnapshot(models.Model):
    """Settled bets - merged SingleBetSnapshot with MergedMatch to show won/lost status."""
    date = models.DateField(unique=True, db_index=True)
    settlements = models.JSONField(default=list)  # List of merged bet+result records

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        count = len(self.settlements) if isinstance(self.settlements, list) else 0
        return f"BetSettlementSnapshot({self.date}, {count} settlements)"


class MarketSelectorMLRun(models.Model):
    """ML filter run - selected bets, rejected bets, and metrics for a date."""
    date = models.DateField(unique=True, db_index=True)
    data = models.JSONField(default=dict)  # selected_bets, rejected_bets, metrics

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        d = self.data or {}
        sel = len(d.get('selected_bets', []))
        rej = len(d.get('rejected_bets', []))
        return f"MarketSelectorMLRun({self.date}, selected={sel}, rejected={rej})"
