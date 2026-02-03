"""
URL configuration for betting_engine app.
Defines all betting data API endpoints.
"""
from django.urls import path
from .views import (
    # Match views
    MatchListView,
    MatchDetailView,
    # BetwayOdds views
    BetwayOddsListView,
    BetwayOddsDetailView,
    # ForebetTip views
    ForebetTipListView,
    ForebetTipDetailView,
    # ForebetResult views
    ForebetResultListView,
    ForebetResultDetailView,
    # CombinedMatch views
    CombinedMatchListView,
    CombinedMatchDetailView,
    # MarketSelection views
    MarketSelectionListView,
    MarketSelectionDetailView,
    # SingleBetSnapshot views
    SingleBetSnapshotListView,
    SingleBetSnapshotDetailView,
    # Import views
    BetwayOddsImportView,
    ForebetTipsImportView,
    ForebetResultsImportView,
    CombinedMatchImportView,
    MergedMatchImportView,
    MarketSelectorsImportView,
    SingleBetsImportView,
)

app_name = 'betting_engine'

urlpatterns = [
    # Match endpoints
    path('matches/', MatchListView.as_view(), name='match_list'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match_detail'),
    
    # BetwayOdds endpoints
    path('betway-odds/', BetwayOddsListView.as_view(), name='betway_odds_list'),
    path('betway-odds/<int:pk>/', BetwayOddsDetailView.as_view(), name='betway_odds_detail'),
    
    # ForebetTip endpoints
    path('forebet-tips/', ForebetTipListView.as_view(), name='forebet_tip_list'),
    path('forebet-tips/<int:pk>/', ForebetTipDetailView.as_view(), name='forebet_tip_detail'),
    
    # ForebetResult endpoints
    path('forebet-results/', ForebetResultListView.as_view(), name='forebet_result_list'),
    path('forebet-results/<int:pk>/', ForebetResultDetailView.as_view(), name='forebet_result_detail'),
    
    # CombinedMatch endpoints
    path('combined-matches/', CombinedMatchListView.as_view(), name='combined_match_list'),
    path('combined-matches/<int:pk>/', CombinedMatchDetailView.as_view(), name='combined_match_detail'),
    
    # MarketSelection endpoints
    path('market-selections/', MarketSelectionListView.as_view(), name='market_selection_list'),
    path('market-selections/<int:pk>/', MarketSelectionDetailView.as_view(), name='market_selection_detail'),
    
    # SingleBetSnapshot endpoints
    path('single-bets/', SingleBetSnapshotListView.as_view(), name='single_bet_snapshot_list'),
    path('single-bets/<int:pk>/', SingleBetSnapshotDetailView.as_view(), name='single_bet_snapshot_detail'),
    
    # Import endpoints
    path('import/betway-odds/', BetwayOddsImportView.as_view(), name='import_betway_odds'),
    path('import/forebet-tips/', ForebetTipsImportView.as_view(), name='import_forebet_tips'),
    path('import/forebet-results/', ForebetResultsImportView.as_view(), name='import_forebet_results'),
    path('import/combined/', CombinedMatchImportView.as_view(), name='import_combined'),
    path('import/merged/', MergedMatchImportView.as_view(), name='import_merged'),
    path('import/market-selectors/', MarketSelectorsImportView.as_view(), name='import_market_selectors'),
    path('import/single-bets/', SingleBetsImportView.as_view(), name='import_single_bets'),
]
