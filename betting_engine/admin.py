from django.contrib import admin

from .models import (
    Match, BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot
)


# Django Admin (for /django-admin/)
@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'away_team', 'date', 'time', 'country', 'league_name', 'forebet_match_id')
    list_filter = ('date', 'country', 'league_name')
    search_fields = ('home_team', 'away_team', 'country', 'league_name')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BetwayOdds)
class BetwayOddsAdmin(admin.ModelAdmin):
    list_display = ('match', 'date', 'created_at')
    list_filter = ('date',)
    search_fields = ('match__home_team', 'match__away_team')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ForebetTip)
class ForebetTipAdmin(admin.ModelAdmin):
    list_display = ('forebet_match_id', 'home_team', 'away_team', 'date', 'pred', 'prob_1', 'prob_x', 'prob_2')
    list_filter = ('date', 'country', 'league_name', 'pred')
    search_fields = ('home_team', 'away_team', 'country', 'league_name')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ForebetResult)
class ForebetResultAdmin(admin.ModelAdmin):
    list_display = ('forebet_match_id', 'date', 'home_correct_score', 'away_correct_score', 'home_ht_score', 'away_ht_score')
    list_filter = ('date',)
    search_fields = ('forebet_match_id',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CombinedMatch)
class CombinedMatchAdmin(admin.ModelAdmin):
    list_display = ('match', 'date', 'match_confidence', 'created_at')
    list_filter = ('date',)
    search_fields = ('match__home_team', 'match__away_team')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MarketSelection)
class MarketSelectionAdmin(admin.ModelAdmin):
    list_display = ('match', 'date', 'home_over_bet', 'away_over_bet', 'home_draw_bet', 'away_draw_bet', 'over_1_5_bet')
    list_filter = ('date', 'home_over_bet', 'away_over_bet', 'home_draw_bet', 'away_draw_bet', 'over_1_5_bet')
    search_fields = ('match__home_team', 'match__away_team')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SingleBetSnapshot)
class SingleBetSnapshotAdmin(admin.ModelAdmin):
    list_display = ('date', 'timestamp', 'total_bets', 'placed_bets', 'failed_bets')
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')

# Note: Wagtail ModelAdmin is configured in wagtail_hooks.py
# This groups all models under a single "Betting Engine" menu section in Wagtail admin
