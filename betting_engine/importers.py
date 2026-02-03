"""
Import logic for betting data.
Handles parsing JSON and creating/updating database models.
"""
import json
from datetime import datetime, date
from typing import List, Dict, Optional
from django.db import transaction
from django.utils.dateparse import parse_date

from .models import (
    Match, BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot
)


def get_or_create_match(match_data: Dict, date: date) -> Match:
    """
    Get or create a Match instance.
    Tries to match by forebet_match_id first, then by (date, home_team, away_team).
    """
    forebet_match_id = match_data.get('forebet_match_id') or match_data.get('match_id')
    
    if forebet_match_id:
        match, created = Match.objects.get_or_create(
            forebet_match_id=forebet_match_id,
            defaults={
                'date': date,
                'time': match_data.get('time'),
                'home_team': match_data.get('home_team', ''),
                'away_team': match_data.get('away_team', ''),
                'country': match_data.get('country') or match_data.get('forebet_country'),
                'league_name': match_data.get('league_name') or match_data.get('forebet_league_name'),
                'game_url': match_data.get('game_url'),
                'game_link': match_data.get('game_link') or match_data.get('forebet_game_link'),
            }
        )
        if not created:
            # Update fields if match exists
            match.date = date
            if match_data.get('time'):
                match.time = match_data.get('time')
            if match_data.get('game_url'):
                match.game_url = match_data.get('game_url')
            if match_data.get('game_link') or match_data.get('forebet_game_link'):
                match.game_link = match_data.get('game_link') or match_data.get('forebet_game_link')
            match.save()
        return match
    
    # Try to find by teams and date
    home_team = match_data.get('home_team', '')
    away_team = match_data.get('away_team', '')
    
    if home_team and away_team:
        match, created = Match.objects.get_or_create(
            date=date,
            home_team=home_team,
            away_team=away_team,
            defaults={
                'time': match_data.get('time'),
                'country': match_data.get('country') or match_data.get('forebet_country'),
                'league_name': match_data.get('league_name') or match_data.get('forebet_league_name'),
                'game_url': match_data.get('game_url'),
                'game_link': match_data.get('game_link') or match_data.get('forebet_game_link'),
            }
        )
        if not created:
            # Update fields
            if match_data.get('time'):
                match.time = match_data.get('time')
            if match_data.get('game_url'):
                match.game_url = match_data.get('game_url')
            if match_data.get('game_link') or match_data.get('forebet_game_link'):
                match.game_link = match_data.get('game_link') or match_data.get('forebet_game_link')
            match.save()
        return match
    
    raise ValueError(f"Cannot create match: missing required fields (home_team, away_team, or forebet_match_id)")


@transaction.atomic
def import_betway_odds(date: date, data: List[Dict]) -> Dict[str, int]:
    """Import Betway odds data."""
    created_count = 0
    updated_count = 0
    
    for item in data:
        match = get_or_create_match(item, date)
        
        # Prepare odds_data (all fields except match identifying fields)
        odds_data = {k: v for k, v in item.items() 
                    if k not in ['home_team', 'away_team', 'date', 'time', 'game_url', 
                                'country', 'league_name', 'forebet_match_id', 'match_id']}
        
        betway_odds, created = BetwayOdds.objects.update_or_create(
            match=match,
            date=date,
            defaults={'odds_data': odds_data}
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    return {'created': created_count, 'updated': updated_count}


@transaction.atomic
def import_forebet_tips(date: date, data: List[Dict]) -> Dict[str, int]:
    """Import Forebet tips data."""
    created_count = 0
    updated_count = 0
    
    for item in data:
        match_id = item.get('match_id')
        if not match_id:
            continue
        
        # Try to find existing match
        match = None
        try:
            match = Match.objects.get(forebet_match_id=match_id)
        except Match.DoesNotExist:
            # Create match if doesn't exist
            match = Match.objects.create(
                forebet_match_id=match_id,
                date=date,
                time=item.get('time'),
                home_team=item.get('home_team', ''),
                away_team=item.get('away_team', ''),
                country=item.get('country'),
                league_name=item.get('league_name'),
                game_link=item.get('game_link'),
            )
        
        tip, created = ForebetTip.objects.update_or_create(
            forebet_match_id=match_id,
            date=date,
            defaults={
                'match': match,
                'country': item.get('country'),
                'league_name': item.get('league_name'),
                'home_team': item.get('home_team', ''),
                'away_team': item.get('away_team', ''),
                'game_link': item.get('game_link'),
                'preview_link': item.get('preview_link'),
                'preview_html': item.get('preview_html'),
                'prob_1': item.get('prob_1'),
                'prob_x': item.get('prob_x'),
                'prob_2': item.get('prob_2'),
                'pred': item.get('pred'),
                'home_pred_score': item.get('home_pred_score'),
                'away_pred_score': item.get('away_pred_score'),
                'avg_goals': item.get('avg_goals'),
                'kelly': item.get('kelly'),
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    return {'created': created_count, 'updated': updated_count}


@transaction.atomic
def import_forebet_results(date: date, data: List[Dict]) -> Dict[str, int]:
    """Import Forebet results data."""
    created_count = 0
    updated_count = 0
    
    for item in data:
        match_id = item.get('match_id')
        if not match_id:
            continue
        
        result, created = ForebetResult.objects.update_or_create(
            forebet_match_id=match_id,
            date=date,
            defaults={
                'home_correct_score': item.get('home_correct_score'),
                'away_correct_score': item.get('away_correct_score'),
                'home_ht_score': item.get('home_ht_score'),
                'away_ht_score': item.get('away_ht_score'),
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    return {'created': created_count, 'updated': updated_count}


@transaction.atomic
def import_combined_matches(date: date, data: List[Dict]) -> Dict[str, int]:
    """Import combined match data."""
    created_count = 0
    updated_count = 0
    
    for item in data:
        match = get_or_create_match(item, date)
        
        match_confidence = item.get('match_confidence')
        
        combined_match, created = CombinedMatch.objects.update_or_create(
            match=match,
            date=date,
            defaults={
                'match_confidence': match_confidence,
                'payload': item,  # Store full payload
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    return {'created': created_count, 'updated': updated_count}


@transaction.atomic
def import_merged_matches(date: date, data: List[Dict]) -> Dict[str, int]:
    """Import merged match data (combined + results)."""
    # Merged is similar to combined but may have result fields
    # We'll treat it as combined_match with result data
    created_count = 0
    updated_count = 0
    
    for item in data:
        match = get_or_create_match(item, date)
        
        match_confidence = item.get('match_confidence')
        
        combined_match, created = CombinedMatch.objects.update_or_create(
            match=match,
            date=date,
            defaults={
                'match_confidence': match_confidence,
                'payload': item,  # Store full merged payload
            }
        )
        
        # Also update/create result if scores are present
        match_id = item.get('forebet_match_id') or item.get('match_id')
        if match_id and (item.get('home_correct_score') is not None or item.get('away_correct_score') is not None):
            ForebetResult.objects.update_or_create(
                forebet_match_id=match_id,
                date=date,
                defaults={
                    'home_correct_score': item.get('home_correct_score'),
                    'away_correct_score': item.get('away_correct_score'),
                    'home_ht_score': item.get('home_ht_score'),
                    'away_ht_score': item.get('away_ht_score'),
                }
            )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    return {'created': created_count, 'updated': updated_count}


@transaction.atomic
def import_market_selectors(date: date, data: List[Dict]) -> Dict[str, int]:
    """Import market selector data."""
    created_count = 0
    updated_count = 0
    
    for item in data:
        match = get_or_create_match(item, date)
        
        market_selection, created = MarketSelection.objects.update_or_create(
            match=match,
            date=date,
            defaults={
                'home_over_bet': item.get('home_over_bet', False),
                'away_over_bet': item.get('away_over_bet', False),
                'home_draw_bet': item.get('home_draw_bet', False),
                'away_draw_bet': item.get('away_draw_bet', False),
                'over_1_5_bet': item.get('over_1_5_bet', False),
                'extra_data': {k: v for k, v in item.items() 
                              if k not in ['home_team', 'away_team', 'date', 'time', 'game_url',
                                          'home_over_bet', 'away_over_bet', 'home_draw_bet',
                                          'away_draw_bet', 'over_1_5_bet', 'forebet_match_id', 'match_id']},
            }
        )
        
        if created:
            created_count += 1
        else:
            updated_count += 1
    
    return {'created': created_count, 'updated': updated_count}


@transaction.atomic
def import_single_bets(date: date, data: Dict) -> Dict[str, int]:
    """Import single bets snapshot data."""
    timestamp_str = data.get('timestamp')
    if timestamp_str:
        if isinstance(timestamp_str, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        else:
            timestamp = timestamp_str
    else:
        timestamp = datetime.now()
    
    snapshot, created = SingleBetSnapshot.objects.update_or_create(
        date=date,
        defaults={
            'timestamp': timestamp,
            'total_bets': data.get('total_bets', 0),
            'placed_bets': data.get('placed_bets', 0),
            'failed_bets': data.get('failed_bets', 0),
            'bets': data.get('bets', []),
        }
    )
    
    return {'created': 1 if created else 0, 'updated': 0 if created else 1}
