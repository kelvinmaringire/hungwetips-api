"""
Import functions for betting data.
Handles saving data to both default and analytics databases.
"""
from datetime import datetime
from .models import (
    BetwayOdds, ForebetTip, ForebetResult, CombinedMatch,
    MarketSelection, SingleBetSnapshot, MergedMatch
)


def import_betway_odds(date, matches_list, using=None):
    """
    Import Betway odds data for a date.
    
    Args:
        date: Date object for the matches
        matches_list: List of match dictionaries with odds data
        using: Database alias ('default', 'analytics', or None for both)
    
    Returns:
        dict with 'created' and 'updated' counts
    """
    if not matches_list:
        return {'created': 0, 'updated': 0}
    
    # Ensure matches_list is a list
    if not isinstance(matches_list, list):
        raise ValueError("matches_list must be a list")
    
    created = 0
    updated = 0
    
    if using is None:
        # Save to both databases
        obj_default, created_flag = BetwayOdds.objects.using('default').get_or_create(
            date=date,
            defaults={'matches': matches_list}
        )
        if not created_flag:
            obj_default.matches = matches_list
            obj_default.save(using='default')
            updated += 1
        else:
            created += 1
        
        # Save to analytics DB
        obj_analytics, created_flag = BetwayOdds.objects.using('analytics').get_or_create(
            date=date,
            defaults={'matches': matches_list}
        )
        if not created_flag:
            obj_analytics.matches = matches_list
            obj_analytics.save(using='analytics')
        # Don't double-count created/updated for analytics
        
        return {'created': created, 'updated': updated}
    else:
        # Save to specific database
        obj, created_flag = BetwayOdds.objects.using(using).get_or_create(
            date=date,
            defaults={'matches': matches_list}
        )
        if not created_flag:
            obj.matches = matches_list
            obj.save(using=using)
            updated = 1
        else:
            created = 1
        
        return {'created': created, 'updated': updated}


def import_forebet_tips(date, tips_list, using=None):
    """
    Import Forebet tips data for a date.
    
    Args:
        date: Date object for the tips
        tips_list: List of tip dictionaries
        using: Database alias ('default', 'analytics', or None for both)
    
    Returns:
        dict with 'created' and 'updated' counts
    """
    if not tips_list:
        return {'created': 0, 'updated': 0}
    
    if not isinstance(tips_list, list):
        raise ValueError("tips_list must be a list")
    
    created = 0
    updated = 0
    
    if using is None:
        # Save to both databases
        obj_default, created_flag = ForebetTip.objects.using('default').get_or_create(
            date=date,
            defaults={'tips': tips_list}
        )
        if not created_flag:
            obj_default.tips = tips_list
            obj_default.save(using='default')
            updated += 1
        else:
            created += 1
        obj_analytics, created_analytics = ForebetTip.objects.using('analytics').get_or_create(
            date=date,
            defaults={'tips': tips_list}
        )
        if not created_analytics:
            obj_analytics.tips = tips_list
            obj_analytics.save(using='analytics')
        return {'created': created, 'updated': updated}
    
    obj, created_flag = ForebetTip.objects.using(using).get_or_create(
        date=date,
        defaults={'tips': tips_list}
    )
    if not created_flag:
        obj.tips = tips_list
        obj.save(using=using)
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_forebet_results(date, results_list, using=None):
    """
    Import Forebet results data for a date.
    
    Args:
        date: Date object for the results
        results_list: List of result dictionaries
        using: Database alias ('default', 'analytics', or None for both)
    
    Returns:
        dict with 'created' and 'updated' counts
    """
    if not results_list:
        return {'created': 0, 'updated': 0}
    
    if not isinstance(results_list, list):
        raise ValueError("results_list must be a list")
    
    created = 0
    updated = 0
    
    if using is None:
        # Save to both databases
        obj_default, created_flag = ForebetResult.objects.using('default').get_or_create(
            date=date,
            defaults={'results': results_list}
        )
        if not created_flag:
            obj_default.results = results_list
            obj_default.save(using='default')
            updated += 1
        else:
            created += 1
        obj_analytics, created_analytics = ForebetResult.objects.using('analytics').get_or_create(
            date=date,
            defaults={'results': results_list}
        )
        if not created_analytics:
            obj_analytics.results = results_list
            obj_analytics.save(using='analytics')
        return {'created': created, 'updated': updated}
    
    obj, created_flag = ForebetResult.objects.using(using).get_or_create(
        date=date,
        defaults={'results': results_list}
    )
    if not created_flag:
        obj.results = results_list
        obj.save(using=using)
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_combined_matches(date, matches_list, using=None):
    """
    Import combined matches (Betway + Forebet) data for a date.
    
    Args:
        date: Date object for the matches
        matches_list: List of combined match dictionaries
        using: Database alias ('default', 'analytics', or None for both)
    
    Returns:
        dict with 'created' and 'updated' counts
    """
    if not matches_list:
        return {'created': 0, 'updated': 0}
    
    if not isinstance(matches_list, list):
        raise ValueError("matches_list must be a list")
    
    created = 0
    updated = 0
    
    if using is None:
        # Save to both databases
        obj_default, created_flag = CombinedMatch.objects.using('default').get_or_create(
            date=date,
            defaults={'matches': matches_list}
        )
        if not created_flag:
            obj_default.matches = matches_list
            obj_default.save(using='default')
            updated += 1
        else:
            created += 1
        obj_analytics, created_analytics = CombinedMatch.objects.using('analytics').get_or_create(
            date=date,
            defaults={'matches': matches_list}
        )
        if not created_analytics:
            obj_analytics.matches = matches_list
            obj_analytics.save(using='analytics')
        return {'created': created, 'updated': updated}
    
    obj, created_flag = CombinedMatch.objects.using(using).get_or_create(
        date=date,
        defaults={'matches': matches_list}
    )
    if not created_flag:
        obj.matches = matches_list
        obj.save(using=using)
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_merged_matches(date, matches_list, using=None):
    """
    Import merged matches (tips + results) data for a date.
    
    Args:
        date: Date object for the merged matches
        matches_list: List of merged match dictionaries
        using: Database alias ('default', 'analytics', or None for both)
    
    Returns:
        dict with 'created' and 'updated' counts
    """
    if not matches_list:
        return {'created': 0, 'updated': 0}
    
    if not isinstance(matches_list, list):
        raise ValueError("matches_list must be a list")
    
    created = 0
    updated = 0
    
    if using is None:
        # Save to both databases
        obj_default, created_flag = MergedMatch.objects.using('default').get_or_create(
            date=date,
            defaults={'rows': matches_list}
        )
        if not created_flag:
            obj_default.rows = matches_list
            obj_default.save(using='default')
            updated += 1
        else:
            created += 1
        obj_analytics, created_analytics = MergedMatch.objects.using('analytics').get_or_create(
            date=date,
            defaults={'rows': matches_list}
        )
        if not created_analytics:
            obj_analytics.rows = matches_list
            obj_analytics.save(using='analytics')
        return {'created': created, 'updated': updated}
    
    obj, created_flag = MergedMatch.objects.using(using).get_or_create(
        date=date,
        defaults={'rows': matches_list}
    )
    if not created_flag:
        obj.rows = matches_list
        obj.save(using=using)
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_market_selectors(date, selections_list, using=None):
    """
    Import market selections data for a date.
    
    Args:
        date: Date object for the selections
        selections_list: List of selection dictionaries
        using: Database alias ('default', 'analytics', or None for both)
    
    Returns:
        dict with 'created' and 'updated' counts
    """
    if not selections_list:
        return {'created': 0, 'updated': 0}
    
    if not isinstance(selections_list, list):
        raise ValueError("selections_list must be a list")
    
    created = 0
    updated = 0
    
    if using is None:
        # Save to both databases
        obj_default, created_flag = MarketSelection.objects.using('default').get_or_create(
            date=date,
            defaults={'selections': selections_list}
        )
        if not created_flag:
            obj_default.selections = selections_list
            obj_default.save(using='default')
            updated += 1
        else:
            created += 1
        obj_analytics, created_analytics = MarketSelection.objects.using('analytics').get_or_create(
            date=date,
            defaults={'selections': selections_list}
        )
        if not created_analytics:
            obj_analytics.selections = selections_list
            obj_analytics.save(using='analytics')
        return {'created': created, 'updated': updated}
    
    obj, created_flag = MarketSelection.objects.using(using).get_or_create(
        date=date,
        defaults={'selections': selections_list}
    )
    if not created_flag:
        obj.selections = selections_list
        obj.save(using=using)
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_single_bets(date, bets_data, using=None):
    """
    Import single bet snapshot data for a date.
    
    Args:
        date: Date object for the bets
        bets_data: Dictionary with 'timestamp', 'total_bets', 'placed_bets', 'failed_bets', 'bets'
        using: Database alias ('default', 'analytics', or None for both)
    
    Returns:
        dict with 'created' and 'updated' counts
    """
    if not bets_data:
        return {'created': 0, 'updated': 0}
    
    if not isinstance(bets_data, dict):
        raise ValueError("bets_data must be a dictionary")
    
    snapshot = bets_data.copy()
    created = 0
    updated = 0
    
    if using is None:
        # Save to both databases
        obj_default, created_flag = SingleBetSnapshot.objects.using('default').get_or_create(
            date=date,
            defaults={'snapshot': snapshot}
        )
        if not created_flag:
            obj_default.snapshot = snapshot
            obj_default.save(using='default')
            updated += 1
        else:
            created += 1
        obj_analytics, created_analytics = SingleBetSnapshot.objects.using('analytics').get_or_create(
            date=date,
            defaults={'snapshot': snapshot}
        )
        if not created_analytics:
            obj_analytics.snapshot = snapshot
            obj_analytics.save(using='analytics')
        return {'created': created, 'updated': updated}
    
    obj, created_flag = SingleBetSnapshot.objects.using(using).get_or_create(
        date=date,
        defaults={'snapshot': snapshot}
    )
    if not created_flag:
        obj.snapshot = snapshot
        obj.save(using=using)
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}
