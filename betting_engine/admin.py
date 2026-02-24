from django.contrib import admin

from .models import (
    BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot, MergedMatch,
    MarketSelectorMLRun,
)


# Django Admin (for /django-admin/)
@admin.register(BetwayOdds)
class BetwayOddsAdmin(admin.ModelAdmin):
    def match_count(self, obj):
        """Return the number of matches in the JSON field."""
        if isinstance(obj.matches, list):
            return len(obj.matches)
        return 0
    match_count.short_description = 'Matches'
    
    list_display = ('date', 'match_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'match_count')


@admin.register(ForebetTip)
class ForebetTipAdmin(admin.ModelAdmin):
    def tip_count(self, obj):
        """Return the number of tips in the JSON field."""
        if isinstance(obj.tips, list):
            return len(obj.tips)
        return 0
    tip_count.short_description = 'Tips'
    
    list_display = ('date', 'tip_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'tip_count')


@admin.register(ForebetResult)
class ForebetResultAdmin(admin.ModelAdmin):
    def result_count(self, obj):
        """Return the number of results in the JSON field."""
        if isinstance(obj.results, list):
            return len(obj.results)
        return 0
    result_count.short_description = 'Results'
    
    list_display = ('date', 'result_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'result_count')


@admin.register(CombinedMatch)
class CombinedMatchAdmin(admin.ModelAdmin):
    def match_count(self, obj):
        """Return the number of matches in the JSON field."""
        if isinstance(obj.matches, list):
            return len(obj.matches)
        return 0
    match_count.short_description = 'Matches'
    
    list_display = ('date', 'match_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'match_count')


@admin.register(MarketSelection)
class MarketSelectionAdmin(admin.ModelAdmin):
    def selection_count(self, obj):
        """Return the number of selections in the JSON field."""
        if isinstance(obj.selections, list):
            return len(obj.selections)
        return 0
    selection_count.short_description = 'Selections'
    
    list_display = ('date', 'selection_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'selection_count')


@admin.register(SingleBetSnapshot)
class SingleBetSnapshotAdmin(admin.ModelAdmin):
    def bet_count(self, obj):
        """Return the number of bets in the snapshot."""
        if isinstance(obj.snapshot, dict):
            bets = obj.snapshot.get('bets', [])
            if isinstance(bets, list):
                return len(bets)
        return 0
    bet_count.short_description = 'Bets'
    
    def total_bets(self, obj):
        """Return total_bets from snapshot."""
        if isinstance(obj.snapshot, dict):
            return obj.snapshot.get('total_bets', 0)
        return 0
    total_bets.short_description = 'Total'
    
    def placed_bets(self, obj):
        """Return placed_bets from snapshot."""
        if isinstance(obj.snapshot, dict):
            return obj.snapshot.get('placed_bets', 0)
        return 0
    placed_bets.short_description = 'Placed'
    
    def failed_bets(self, obj):
        """Return failed_bets from snapshot."""
        if isinstance(obj.snapshot, dict):
            return obj.snapshot.get('failed_bets', 0)
        return 0
    failed_bets.short_description = 'Failed'
    
    list_display = ('date', 'bet_count', 'total_bets', 'placed_bets', 'failed_bets', 'created_at', 'updated_at')
    list_filter = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'bet_count', 'total_bets', 'placed_bets', 'failed_bets')


@admin.register(MergedMatch)
class MergedMatchAdmin(admin.ModelAdmin):
    def row_count(self, obj):
        """Return the number of rows in the JSON field."""
        if isinstance(obj.rows, list):
            return len(obj.rows)
        return 0
    row_count.short_description = 'Rows'
    
    list_display = ('date', 'row_count', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at', 'row_count')


@admin.register(MarketSelectorMLRun)
class MarketSelectorMLRunAdmin(admin.ModelAdmin):
    list_display = ('date', 'created_at', 'updated_at')
    list_filter = ('date',)
    search_fields = ('date',)
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


# Note: Wagtail ModelAdmin is configured in wagtail_hooks.py
# This groups all models under a single "Betting Engine" menu section in Wagtail admin
