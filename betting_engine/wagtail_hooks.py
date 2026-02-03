"""
Wagtail hooks for betting_engine app.
Groups all betting models under a single "Betting Engine" menu section.
"""
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from .models import (
    Match, BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot
)


class MatchAdmin(ModelAdmin):
    model = Match
    menu_label = "Matches"
    menu_icon = "fa-futbol-o"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('home_team', 'away_team', 'date', 'time', 'country', 'league_name', 'forebet_match_id')
    list_filter = ('date', 'country', 'league_name')
    search_fields = ('home_team', 'away_team', 'country', 'league_name')
    ordering = ('-date', 'home_team')


class BetwayOddsAdmin(ModelAdmin):
    model = BetwayOdds
    menu_label = "Betway Odds"
    menu_icon = "fa-money"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('match', 'date', 'created_at')
    list_filter = ('date',)
    search_fields = ('match__home_team', 'match__away_team')
    ordering = ('-date', 'match')


class ForebetTipAdmin(ModelAdmin):
    model = ForebetTip
    menu_label = "Forebet Tips"
    menu_icon = "fa-lightbulb-o"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('forebet_match_id', 'home_team', 'away_team', 'date', 'pred', 'prob_1', 'prob_x', 'prob_2')
    list_filter = ('date', 'country', 'league_name', 'pred')
    search_fields = ('home_team', 'away_team', 'country', 'league_name')
    ordering = ('-date', 'forebet_match_id')


class ForebetResultAdmin(ModelAdmin):
    model = ForebetResult
    menu_label = "Forebet Results"
    menu_icon = "fa-trophy"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('forebet_match_id', 'date', 'home_correct_score', 'away_correct_score', 'home_ht_score', 'away_ht_score')
    list_filter = ('date',)
    search_fields = ('forebet_match_id',)
    ordering = ('-date', 'forebet_match_id')


class CombinedMatchAdmin(ModelAdmin):
    model = CombinedMatch
    menu_label = "Combined Matches"
    menu_icon = "fa-link"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('match', 'date', 'match_confidence', 'created_at')
    list_filter = ('date',)
    search_fields = ('match__home_team', 'match__away_team')
    ordering = ('-date', 'match')


class MarketSelectionAdmin(ModelAdmin):
    model = MarketSelection
    menu_label = "Market Selections"
    menu_icon = "fa-check-square-o"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('match', 'date', 'home_over_bet', 'away_over_bet', 'home_draw_bet', 'away_draw_bet', 'over_1_5_bet')
    list_filter = ('date', 'home_over_bet', 'away_over_bet', 'home_draw_bet', 'away_draw_bet', 'over_1_5_bet')
    search_fields = ('match__home_team', 'match__away_team')
    ordering = ('-date', 'match')


class SingleBetSnapshotAdmin(ModelAdmin):
    model = SingleBetSnapshot
    menu_label = "Single Bet Snapshots"
    menu_icon = "fa-file-text-o"
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('date', 'timestamp', 'total_bets', 'placed_bets', 'failed_bets')
    list_filter = ('date',)
    ordering = ('-date',)


# Group all betting models under a single "Betting Engine" menu section
class BettingEngineAdminGroup(ModelAdminGroup):
    menu_label = "Betting Engine"  # Main menu label
    menu_icon = "fa-database"  # Main menu icon
    menu_order = 200  # Menu order in sidebar
    items = (
        MatchAdmin,
        BetwayOddsAdmin,
        ForebetTipAdmin,
        ForebetResultAdmin,
        CombinedMatchAdmin,
        MarketSelectionAdmin,
        SingleBetSnapshotAdmin,
    )


# Register the Betting Engine group (this registers all models under one menu section)
modeladmin_register(BettingEngineAdminGroup)
