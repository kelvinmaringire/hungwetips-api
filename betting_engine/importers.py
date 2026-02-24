"""
Import functions for betting data.
Saves data to the default PostgreSQL database.
"""
from datetime import datetime
from .models import (
    BetwayOdds, ForebetTip, ForebetResult, CombinedMatch,
    MarketSelection, SingleBetSnapshot, MergedMatch, BetSettlementSnapshot,
    MarketSelectorMLRun,
)


def import_betway_odds(date, matches_list, using=None):
    """
    Import Betway odds data for a date.

    Args:
        date: Date object for the matches
        matches_list: List of match dictionaries with odds data
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if not matches_list:
        return {'created': 0, 'updated': 0}

    if not isinstance(matches_list, list):
        raise ValueError("matches_list must be a list")

    obj, created_flag = BetwayOdds.objects.get_or_create(
        date=date,
        defaults={'matches': matches_list}
    )
    if not created_flag:
        obj.matches = matches_list
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_forebet_tips(date, tips_list, using=None):
    """
    Import Forebet tips data for a date.

    Args:
        date: Date object for the tips
        tips_list: List of tip dictionaries
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if not tips_list:
        return {'created': 0, 'updated': 0}

    if not isinstance(tips_list, list):
        raise ValueError("tips_list must be a list")

    obj, created_flag = ForebetTip.objects.get_or_create(
        date=date,
        defaults={'tips': tips_list}
    )
    if not created_flag:
        obj.tips = tips_list
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_forebet_results(date, results_list, using=None):
    """
    Import Forebet results data for a date.

    Args:
        date: Date object for the results
        results_list: List of result dictionaries
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if not results_list:
        return {'created': 0, 'updated': 0}

    if not isinstance(results_list, list):
        raise ValueError("results_list must be a list")

    obj, created_flag = ForebetResult.objects.get_or_create(
        date=date,
        defaults={'results': results_list}
    )
    if not created_flag:
        obj.results = results_list
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_combined_matches(date, matches_list, using=None):
    """
    Import combined matches (Betway + Forebet) data for a date.

    Args:
        date: Date object for the matches
        matches_list: List of combined match dictionaries
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if not matches_list:
        return {'created': 0, 'updated': 0}

    if not isinstance(matches_list, list):
        raise ValueError("matches_list must be a list")

    obj, created_flag = CombinedMatch.objects.get_or_create(
        date=date,
        defaults={'matches': matches_list}
    )
    if not created_flag:
        obj.matches = matches_list
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_merged_matches(date, matches_list, using=None):
    """
    Import merged matches (tips + results) data for a date.

    Args:
        date: Date object for the merged matches
        matches_list: List of merged match dictionaries
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if not matches_list:
        return {'created': 0, 'updated': 0}

    if not isinstance(matches_list, list):
        raise ValueError("matches_list must be a list")

    obj, created_flag = MergedMatch.objects.get_or_create(
        date=date,
        defaults={'rows': matches_list}
    )
    if not created_flag:
        obj.rows = matches_list
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_market_selectors(date, selections_list, using=None):
    """
    Import market selections data for a date.

    Args:
        date: Date object for the selections
        selections_list: List of selection dictionaries
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if not selections_list:
        return {'created': 0, 'updated': 0}

    if not isinstance(selections_list, list):
        raise ValueError("selections_list must be a list")

    obj, created_flag = MarketSelection.objects.get_or_create(
        date=date,
        defaults={'selections': selections_list}
    )
    if not created_flag:
        obj.selections = selections_list
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_single_bets(date, bets_data, using=None):
    """
    Import single bet snapshot data for a date.

    Args:
        date: Date object for the bets
        bets_data: Dictionary with 'timestamp', 'total_bets', 'placed_bets', 'failed_bets', 'bets'
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if not bets_data:
        return {'created': 0, 'updated': 0}

    if not isinstance(bets_data, dict):
        raise ValueError("bets_data must be a dictionary")

    snapshot = bets_data.copy()
    obj, created_flag = SingleBetSnapshot.objects.get_or_create(
        date=date,
        defaults={'snapshot': snapshot}
    )
    if not created_flag:
        obj.snapshot = snapshot
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_bet_settlements(date, settlements_list, using=None):
    """
    Import bet settlement data for a date.

    Args:
        date: Date object for the settlements
        settlements_list: List of settlement dictionaries (merged bet+result)
        using: Database alias (ignored; always uses 'default')

    Returns:
        dict with 'created' and 'updated' counts
    """
    if settlements_list is None:
        settlements_list = []

    if not isinstance(settlements_list, list):
        raise ValueError("settlements_list must be a list")

    obj, created_flag = BetSettlementSnapshot.objects.get_or_create(
        date=date,
        defaults={'settlements': settlements_list}
    )
    if not created_flag:
        obj.settlements = settlements_list
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}


def import_market_selector_ml_run(date, data_dict, using=None):
    """
    Import market selector ML run data for a date.

    Args:
        date: Date object for the run
        data_dict: Dict with selected_bets, rejected_bets, metrics
        using: Database alias (ignored)

    Returns:
        dict with 'created' and 'updated' counts
    """
    if data_dict is None:
        data_dict = {}

    if not isinstance(data_dict, dict):
        raise ValueError("data_dict must be a dict")

    obj, created_flag = MarketSelectorMLRun.objects.get_or_create(
        date=date,
        defaults={'data': data_dict}
    )
    if not created_flag:
        obj.data = data_dict
        obj.save()
        return {'created': 0, 'updated': 1}
    return {'created': 1, 'updated': 0}
