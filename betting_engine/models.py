from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Match(models.Model):
    """Central fixture model linking Betway and Forebet data."""
    date = models.DateField(db_index=True)
    time = models.CharField(max_length=10, null=True, blank=True)
    home_team = models.CharField(max_length=200, db_index=True)
    away_team = models.CharField(max_length=200, db_index=True)
    country = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    league_name = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    forebet_match_id = models.IntegerField(unique=True, null=True, blank=True, db_index=True)
    game_url = models.URLField(max_length=500, null=True, blank=True)  # Betway URL
    game_link = models.URLField(max_length=500, null=True, blank=True)  # Forebet URL
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'home_team']
        indexes = [
            models.Index(fields=['date', 'home_team', 'away_team']),
            models.Index(fields=['date', 'country', 'league_name']),
        ]
        # Unique constraint: either forebet_match_id (when set) or (date, home_team, away_team)
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'home_team', 'away_team'],
                name='unique_match_date_teams',
                condition=models.Q(forebet_match_id__isnull=True)
            ),
        ]

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} ({self.date})"


class BetwayOdds(models.Model):
    """Betway odds data for a match."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='betway_odds')
    date = models.DateField(db_index=True)
    odds_data = models.JSONField(default=dict)  # Stores all odds: home_win, draw, total_over_1.5, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'match']
        unique_together = [['match', 'date']]
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"BetwayOdds for {self.match} ({self.date})"


class ForebetTip(models.Model):
    """Forebet prediction/tip data for a match."""
    forebet_match_id = models.IntegerField(db_index=True)
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, null=True, blank=True, related_name='forebet_tips')
    date = models.DateField(db_index=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    league_name = models.CharField(max_length=200, null=True, blank=True)
    home_team = models.CharField(max_length=200)
    away_team = models.CharField(max_length=200)
    game_link = models.URLField(max_length=500, null=True, blank=True)
    preview_link = models.URLField(max_length=500, null=True, blank=True)
    preview_html = models.TextField(null=True, blank=True)
    prob_1 = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    prob_x = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    prob_2 = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    pred = models.CharField(max_length=10, null=True, blank=True)  # '1', 'X', '2'
    home_pred_score = models.IntegerField(null=True, blank=True)
    away_pred_score = models.IntegerField(null=True, blank=True)
    avg_goals = models.FloatField(null=True, blank=True)
    kelly = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'forebet_match_id']
        unique_together = [['forebet_match_id', 'date']]
        indexes = [
            models.Index(fields=['date', 'forebet_match_id']),
        ]

    def __str__(self):
        return f"ForebetTip {self.forebet_match_id} ({self.date})"


class ForebetResult(models.Model):
    """Forebet match result data."""
    forebet_match_id = models.IntegerField(db_index=True)
    date = models.DateField(db_index=True)
    home_correct_score = models.IntegerField(null=True, blank=True)
    away_correct_score = models.IntegerField(null=True, blank=True)
    home_ht_score = models.IntegerField(null=True, blank=True)
    away_ht_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'forebet_match_id']
        unique_together = [['forebet_match_id', 'date']]
        indexes = [
            models.Index(fields=['date', 'forebet_match_id']),
        ]

    def __str__(self):
        return f"ForebetResult {self.forebet_match_id} ({self.date})"


class CombinedMatch(models.Model):
    """Matched Betway + Forebet data for a date."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='combined_matches')
    date = models.DateField(db_index=True)
    match_confidence = models.FloatField(null=True, blank=True)
    payload = models.JSONField(default=dict)  # Full combined row data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'match']
        unique_together = [['match', 'date']]
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"CombinedMatch for {self.match} ({self.date})"


class MarketSelection(models.Model):
    """Market selection flags for betting."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='market_selections')
    date = models.DateField(db_index=True)
    home_over_bet = models.BooleanField(default=False)
    away_over_bet = models.BooleanField(default=False)
    home_draw_bet = models.BooleanField(default=False)
    away_draw_bet = models.BooleanField(default=False)
    over_1_5_bet = models.BooleanField(default=False)
    extra_data = models.JSONField(default=dict, null=True, blank=True)  # For any additional fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'match']
        unique_together = [['match', 'date']]
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['home_over_bet', 'away_over_bet', 'home_draw_bet', 'away_draw_bet', 'over_1_5_bet']),
        ]

    def __str__(self):
        return f"MarketSelection for {self.match} ({self.date})"


class SingleBetSnapshot(models.Model):
    """Single bet snapshot from automation for a date."""
    date = models.DateField(unique=True, db_index=True)
    timestamp = models.DateTimeField()
    total_bets = models.IntegerField(default=0)
    placed_bets = models.IntegerField(default=0)
    failed_bets = models.IntegerField(default=0)
    bets = models.JSONField(default=list)  # List of bet objects
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"SingleBetSnapshot for {self.date}"
