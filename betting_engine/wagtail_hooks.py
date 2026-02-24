"""
Wagtail hooks for betting_engine app.
Groups all betting models under a single "Betting Engine" menu section.
"""
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from .models import (
    BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot, MergedMatch,
    MarketSelectorMLRun,
)


class BetwayOddsAdmin(ModelAdmin):
    model = BetwayOdds
    menu_label = "Betway Odds"
    menu_icon = "fa-money"
    add_to_settings_menu = False
    exclude_from_explorer = False

    def match_count(self, obj):
        if isinstance(obj.matches, list):
            return len(obj.matches)
        return 0
    match_count.short_description = 'Matches'

    list_display = ('date', 'match_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)


class ForebetTipAdmin(ModelAdmin):
    model = ForebetTip
    menu_label = "Forebet Tips"
    menu_icon = "fa-lightbulb-o"
    add_to_settings_menu = False
    exclude_from_explorer = False

    def tip_count(self, obj):
        if isinstance(obj.tips, list):
            return len(obj.tips)
        return 0
    tip_count.short_description = 'Tips'

    list_display = ('date', 'tip_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)


class ForebetResultAdmin(ModelAdmin):
    model = ForebetResult
    menu_label = "Forebet Results"
    menu_icon = "fa-trophy"
    add_to_settings_menu = False
    exclude_from_explorer = False

    def result_count(self, obj):
        if isinstance(obj.results, list):
            return len(obj.results)
        return 0
    result_count.short_description = 'Results'

    list_display = ('date', 'result_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)


class CombinedMatchAdmin(ModelAdmin):
    model = CombinedMatch
    menu_label = "Combined Matches"
    menu_icon = "fa-link"
    add_to_settings_menu = False
    exclude_from_explorer = False

    def match_count(self, obj):
        if isinstance(obj.matches, list):
            return len(obj.matches)
        return 0
    match_count.short_description = 'Matches'

    list_display = ('date', 'match_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)


class MarketSelectionAdmin(ModelAdmin):
    model = MarketSelection
    menu_label = "Market Selections"
    menu_icon = "fa-check-square-o"
    add_to_settings_menu = False
    exclude_from_explorer = False

    def selection_count(self, obj):
        if isinstance(obj.selections, list):
            return len(obj.selections)
        return 0
    selection_count.short_description = 'Selections'

    list_display = ('date', 'selection_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)


class SingleBetSnapshotAdmin(ModelAdmin):
    model = SingleBetSnapshot
    menu_label = "Single Bet Snapshots"
    menu_icon = "fa-file-text-o"
    add_to_settings_menu = False
    exclude_from_explorer = False

    def bet_count(self, obj):
        if isinstance(obj.snapshot, dict):
            bets = obj.snapshot.get('bets', [])
            if isinstance(bets, list):
                return len(bets)
        return 0
    bet_count.short_description = 'Bets'

    def total_bets(self, obj):
        if isinstance(obj.snapshot, dict):
            return obj.snapshot.get('total_bets', 0)
        return 0
    total_bets.short_description = 'Total'

    def placed_bets(self, obj):
        if isinstance(obj.snapshot, dict):
            return obj.snapshot.get('placed_bets', 0)
        return 0
    placed_bets.short_description = 'Placed'

    def failed_bets(self, obj):
        if isinstance(obj.snapshot, dict):
            return obj.snapshot.get('failed_bets', 0)
        return 0
    failed_bets.short_description = 'Failed'

    list_display = ('date', 'bet_count', 'total_bets', 'placed_bets', 'failed_bets', 'created_at', 'updated_at')
    list_filter = ('date',)
    ordering = ('-date',)


class MergedMatchAdmin(ModelAdmin):
    model = MergedMatch
    menu_label = "Merged Matches"
    menu_icon = "fa-object-group"
    add_to_settings_menu = False
    exclude_from_explorer = False

    def row_count(self, obj):
        if isinstance(obj.rows, list):
            return len(obj.rows)
        return 0
    row_count.short_description = 'Rows'

    list_display = ('date', 'row_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)


class MarketSelectorMLRunAdmin(ModelAdmin):
    model = MarketSelectorMLRun
    menu_label = "Market Selector ML Runs"
    menu_icon = "fa-line-chart"
    add_to_settings_menu = False
    exclude_from_explorer = False

    list_display = ('date', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    ordering = ('-date',)


# Group all betting models under a single "Betting Engine" menu section
class BettingEngineAdminGroup(ModelAdminGroup):
    menu_label = "Betting Engine"
    menu_icon = "fa-database"
    menu_order = 200
    items = (
        BetwayOddsAdmin,
        ForebetTipAdmin,
        ForebetResultAdmin,
        CombinedMatchAdmin,
        MarketSelectionAdmin,
        SingleBetSnapshotAdmin,
        MergedMatchAdmin,
        MarketSelectorMLRunAdmin,
    )


# Register the Betting Engine group (this registers all models under one menu section)
modeladmin_register(BettingEngineAdminGroup)
