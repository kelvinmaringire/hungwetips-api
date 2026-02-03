"""
API views for betting_engine endpoints.
Handles CRUD operations and data import for matches, odds, tips, results, and betting data.
"""
import json
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils.dateparse import parse_date

from .models import (
    Match, BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot
)
from .serializers import (
    MatchSerializer, BetwayOddsSerializer, ForebetTipSerializer,
    ForebetResultSerializer, CombinedMatchSerializer, MarketSelectionSerializer,
    SingleBetSnapshotSerializer,
    BetwayOddsUploadSerializer, ForebetTipsUploadSerializer,
    ForebetResultsUploadSerializer, CombinedMatchUploadSerializer,
    MergedMatchUploadSerializer, MarketSelectorsUploadSerializer,
    SingleBetsUploadSerializer
)
from .importers import (
    import_betway_odds, import_forebet_tips, import_forebet_results,
    import_combined_matches, import_merged_matches, import_market_selectors,
    import_single_bets
)


# Match Views
class MatchListView(generics.ListAPIView):
    """List matches with filtering by date, league, team."""
    serializer_class = MatchSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Match.objects.all()
        
        # Filter by date
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        # Filter by country
        country = self.request.query_params.get('country', None)
        if country:
            queryset = queryset.filter(country__icontains=country)
        
        # Filter by league
        league = self.request.query_params.get('league', None)
        if league:
            queryset = queryset.filter(league_name__icontains=league)
        
        # Filter by team (home or away)
        team = self.request.query_params.get('team', None)
        if team:
            queryset = queryset.filter(
                Q(home_team__icontains=team) | Q(away_team__icontains=team)
            )
        
        # Filter by forebet_match_id
        forebet_match_id = self.request.query_params.get('forebet_match_id', None)
        if forebet_match_id:
            try:
                queryset = queryset.filter(forebet_match_id=int(forebet_match_id))
            except ValueError:
                pass
        
        return queryset


class MatchDetailView(generics.RetrieveAPIView):
    """Retrieve a single match."""
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [permissions.AllowAny]


# BetwayOdds Views
class BetwayOddsListView(generics.ListAPIView):
    """List Betway odds with filtering."""
    serializer_class = BetwayOddsSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = BetwayOdds.objects.select_related('match').all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        match_id = self.request.query_params.get('match_id', None)
        if match_id:
            queryset = queryset.filter(match_id=match_id)
        
        return queryset


class BetwayOddsDetailView(generics.RetrieveAPIView):
    """Retrieve a single BetwayOdds record."""
    queryset = BetwayOdds.objects.select_related('match').all()
    serializer_class = BetwayOddsSerializer
    permission_classes = [permissions.AllowAny]


# ForebetTip Views
class ForebetTipListView(generics.ListAPIView):
    """List Forebet tips with filtering."""
    serializer_class = ForebetTipSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = ForebetTip.objects.select_related('match').all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        forebet_match_id = self.request.query_params.get('forebet_match_id', None)
        if forebet_match_id:
            try:
                queryset = queryset.filter(forebet_match_id=int(forebet_match_id))
            except ValueError:
                pass
        
        return queryset


class ForebetTipDetailView(generics.RetrieveAPIView):
    """Retrieve a single ForebetTip record."""
    queryset = ForebetTip.objects.select_related('match').all()
    serializer_class = ForebetTipSerializer
    permission_classes = [permissions.AllowAny]


# ForebetResult Views
class ForebetResultListView(generics.ListAPIView):
    """List Forebet results with filtering."""
    serializer_class = ForebetResultSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = ForebetResult.objects.all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        forebet_match_id = self.request.query_params.get('forebet_match_id', None)
        if forebet_match_id:
            try:
                queryset = queryset.filter(forebet_match_id=int(forebet_match_id))
            except ValueError:
                pass
        
        return queryset


class ForebetResultDetailView(generics.RetrieveAPIView):
    """Retrieve a single ForebetResult record."""
    queryset = ForebetResult.objects.all()
    serializer_class = ForebetResultSerializer
    permission_classes = [permissions.AllowAny]


# CombinedMatch Views
class CombinedMatchListView(generics.ListAPIView):
    """List combined matches with filtering."""
    serializer_class = CombinedMatchSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = CombinedMatch.objects.select_related('match').all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        match_id = self.request.query_params.get('match_id', None)
        if match_id:
            queryset = queryset.filter(match_id=match_id)
        
        return queryset


class CombinedMatchDetailView(generics.RetrieveAPIView):
    """Retrieve a single CombinedMatch record."""
    queryset = CombinedMatch.objects.select_related('match').all()
    serializer_class = CombinedMatchSerializer
    permission_classes = [permissions.AllowAny]


# MarketSelection Views
class MarketSelectionListView(generics.ListAPIView):
    """List market selections with filtering."""
    serializer_class = MarketSelectionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = MarketSelection.objects.select_related('match').all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        match_id = self.request.query_params.get('match_id', None)
        if match_id:
            queryset = queryset.filter(match_id=match_id)
        
        # Filter by bet flags
        home_over = self.request.query_params.get('home_over_bet', None)
        if home_over is not None:
            queryset = queryset.filter(home_over_bet=home_over.lower() == 'true')
        
        away_over = self.request.query_params.get('away_over_bet', None)
        if away_over is not None:
            queryset = queryset.filter(away_over_bet=away_over.lower() == 'true')
        
        over_1_5 = self.request.query_params.get('over_1_5_bet', None)
        if over_1_5 is not None:
            queryset = queryset.filter(over_1_5_bet=over_1_5.lower() == 'true')
        
        return queryset


class MarketSelectionDetailView(generics.RetrieveAPIView):
    """Retrieve a single MarketSelection record."""
    queryset = MarketSelection.objects.select_related('match').all()
    serializer_class = MarketSelectionSerializer
    permission_classes = [permissions.AllowAny]


# SingleBetSnapshot Views
class SingleBetSnapshotListView(generics.ListAPIView):
    """List single bet snapshots with filtering."""
    serializer_class = SingleBetSnapshotSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = SingleBetSnapshot.objects.all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        return queryset


class SingleBetSnapshotDetailView(generics.RetrieveAPIView):
    """Retrieve a single SingleBetSnapshot record."""
    queryset = SingleBetSnapshot.objects.all()
    serializer_class = SingleBetSnapshotSerializer
    permission_classes = [permissions.AllowAny]


# Import/Upload Views
class BetwayOddsImportView(APIView):
    """Import Betway odds data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BetwayOddsUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        data = serializer.validated_data.get('data')
        file = serializer.validated_data.get('file')
        
        if file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    return Response(
                        {'error': 'File must contain a JSON array.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not data:
            return Response(
                {'error': 'No data provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = import_betway_odds(date, data)
            return Response({
                'message': 'Betway odds imported successfully.',
                'created': result['created'],
                'updated': result['updated']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ForebetTipsImportView(APIView):
    """Import Forebet tips data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ForebetTipsUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        data = serializer.validated_data.get('data')
        file = serializer.validated_data.get('file')
        
        if file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    return Response(
                        {'error': 'File must contain a JSON array.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not data:
            return Response(
                {'error': 'No data provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = import_forebet_tips(date, data)
            return Response({
                'message': 'Forebet tips imported successfully.',
                'created': result['created'],
                'updated': result['updated']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ForebetResultsImportView(APIView):
    """Import Forebet results data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ForebetResultsUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        data = serializer.validated_data.get('data')
        file = serializer.validated_data.get('file')
        
        if file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    return Response(
                        {'error': 'File must contain a JSON array.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not data:
            return Response(
                {'error': 'No data provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = import_forebet_results(date, data)
            return Response({
                'message': 'Forebet results imported successfully.',
                'created': result['created'],
                'updated': result['updated']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CombinedMatchImportView(APIView):
    """Import combined match data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CombinedMatchUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        data = serializer.validated_data.get('data')
        file = serializer.validated_data.get('file')
        
        if file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    return Response(
                        {'error': 'File must contain a JSON array.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not data:
            return Response(
                {'error': 'No data provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = import_combined_matches(date, data)
            return Response({
                'message': 'Combined matches imported successfully.',
                'created': result['created'],
                'updated': result['updated']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MergedMatchImportView(APIView):
    """Import merged match data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = MergedMatchUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        data = serializer.validated_data.get('data')
        file = serializer.validated_data.get('file')
        
        if file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    return Response(
                        {'error': 'File must contain a JSON array.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not data:
            return Response(
                {'error': 'No data provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = import_merged_matches(date, data)
            return Response({
                'message': 'Merged matches imported successfully.',
                'created': result['created'],
                'updated': result['updated']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MarketSelectorsImportView(APIView):
    """Import market selectors data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = MarketSelectorsUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        data = serializer.validated_data.get('data')
        file = serializer.validated_data.get('file')
        
        if file:
            try:
                data = json.load(file)
                if not isinstance(data, list):
                    return Response(
                        {'error': 'File must contain a JSON array.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not data:
            return Response(
                {'error': 'No data provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = import_market_selectors(date, data)
            return Response({
                'message': 'Market selectors imported successfully.',
                'created': result['created'],
                'updated': result['updated']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SingleBetsImportView(APIView):
    """Import single bets snapshot data."""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = SingleBetsUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        date = serializer.validated_data['date']
        data = serializer.validated_data.get('data')
        file = serializer.validated_data.get('file')
        
        if file:
            try:
                data = json.load(file)
                if not isinstance(data, dict):
                    return Response(
                        {'error': 'File must contain a JSON object.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if not data:
            return Response(
                {'error': 'No data provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = import_single_bets(date, data)
            return Response({
                'message': 'Single bets imported successfully.',
                'created': result['created'],
                'updated': result['updated']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {'error': f'Import failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
