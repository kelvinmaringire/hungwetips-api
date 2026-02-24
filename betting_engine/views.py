"""
API views for betting_engine endpoints.
Handles CRUD operations and data import for matches, odds, tips, results, and betting data.
"""
import json
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.dateparse import parse_date

from .models import (
    BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot, MergedMatch,
    BetSettlementSnapshot, MarketSelectorMLRun,
)
from .serializers import (
    BetwayOddsSerializer, ForebetTipSerializer,
    ForebetResultSerializer, CombinedMatchSerializer, MarketSelectionSerializer,
    SingleBetSnapshotSerializer, MergedMatchSerializer,
    BetSettlementSnapshotSerializer, MarketSelectorMLRunSerializer,
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


# BetwayOdds Views
class BetwayOddsListView(generics.ListAPIView):
    """List Betway odds with filtering."""
    serializer_class = BetwayOddsSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = BetwayOdds.objects.all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        return queryset


class BetwayOddsDetailView(generics.RetrieveAPIView):
    """Retrieve a single BetwayOdds record."""
    queryset = BetwayOdds.objects.all()
    serializer_class = BetwayOddsSerializer
    permission_classes = [permissions.AllowAny]


# ForebetTip Views
class ForebetTipListView(generics.ListAPIView):
    """List Forebet tips with filtering."""
    serializer_class = ForebetTipSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = ForebetTip.objects.all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        return queryset


class ForebetTipDetailView(generics.RetrieveAPIView):
    """Retrieve a single ForebetTip record."""
    queryset = ForebetTip.objects.all()
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
        queryset = CombinedMatch.objects.all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        return queryset


class CombinedMatchDetailView(generics.RetrieveAPIView):
    """Retrieve a single CombinedMatch record."""
    queryset = CombinedMatch.objects.all()
    serializer_class = CombinedMatchSerializer
    permission_classes = [permissions.AllowAny]


# MarketSelection Views
class MarketSelectionListView(generics.ListAPIView):
    """List market selections with filtering."""
    serializer_class = MarketSelectionSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = MarketSelection.objects.all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        return queryset


class MarketSelectionDetailView(generics.RetrieveAPIView):
    """Retrieve a single MarketSelection record."""
    queryset = MarketSelection.objects.all()
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


# MergedMatch Views
class MergedMatchListView(generics.ListAPIView):
    """List merged matches with filtering."""
    serializer_class = MergedMatchSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = MergedMatch.objects.all()
        
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        
        return queryset


class MergedMatchDetailView(generics.RetrieveAPIView):
    """Retrieve a single MergedMatch record."""
    queryset = MergedMatch.objects.all()
    serializer_class = MergedMatchSerializer
    permission_classes = [permissions.AllowAny]


# BetSettlementSnapshot Views
class BetSettlementSnapshotListView(generics.ListAPIView):
    """List bet settlement snapshots with filtering."""
    serializer_class = BetSettlementSnapshotSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = BetSettlementSnapshot.objects.all()
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        return queryset


class BetSettlementSnapshotDetailView(generics.RetrieveAPIView):
    """Retrieve a single BetSettlementSnapshot record."""
    queryset = BetSettlementSnapshot.objects.all()
    serializer_class = BetSettlementSnapshotSerializer
    permission_classes = [permissions.AllowAny]


# MarketSelectorMLRun Views
class MarketSelectorMLRunListView(generics.ListAPIView):
    """List market selector ML runs with filtering."""
    serializer_class = MarketSelectorMLRunSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = MarketSelectorMLRun.objects.all()
        date_str = self.request.query_params.get('date', None)
        if date_str:
            date = parse_date(date_str)
            if date:
                queryset = queryset.filter(date=date)
        return queryset


class MarketSelectorMLRunDetailView(generics.RetrieveAPIView):
    """Retrieve a single MarketSelectorMLRun record."""
    queryset = MarketSelectorMLRun.objects.all()
    serializer_class = MarketSelectorMLRunSerializer
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
