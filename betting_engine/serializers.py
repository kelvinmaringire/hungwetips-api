"""
Serializers for the betting_engine app.
Handles serialization of matches, odds, tips, results, and betting data.
"""
from rest_framework import serializers
from .models import (
    BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot, MergedMatch
)


class BetwayOddsSerializer(serializers.ModelSerializer):
    """Serializer for BetwayOdds model."""
    
    class Meta:
        model = BetwayOdds
        fields = (
            'id', 'date', 'matches',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ForebetTipSerializer(serializers.ModelSerializer):
    """Serializer for ForebetTip model."""
    
    class Meta:
        model = ForebetTip
        fields = (
            'id', 'date', 'tips',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ForebetResultSerializer(serializers.ModelSerializer):
    """Serializer for ForebetResult model."""
    
    class Meta:
        model = ForebetResult
        fields = (
            'id', 'date', 'results',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CombinedMatchSerializer(serializers.ModelSerializer):
    """Serializer for CombinedMatch model. Match details (time, teams, odds, etc.) live in the matches JSON list."""
    
    class Meta:
        model = CombinedMatch
        fields = (
            'id', 'date', 'matches',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class MarketSelectionSerializer(serializers.ModelSerializer):
    """Serializer for MarketSelection model."""
    
    class Meta:
        model = MarketSelection
        fields = (
            'id', 'date', 'selections',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SingleBetSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for SingleBetSnapshot model."""
    
    class Meta:
        model = SingleBetSnapshot
        fields = (
            'id', 'date', 'snapshot',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class MergedMatchSerializer(serializers.ModelSerializer):
    """Serializer for MergedMatch model."""
    
    class Meta:
        model = MergedMatch
        fields = (
            'id', 'date', 'rows',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


# Upload/Import serializers
class BetwayOddsUploadSerializer(serializers.Serializer):
    """Serializer for uploading Betway odds data."""
    date = serializers.DateField(required=True)
    data = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('data') and not attrs.get('file'):
            raise serializers.ValidationError("Either 'data' or 'file' must be provided.")
        return attrs


class ForebetTipsUploadSerializer(serializers.Serializer):
    """Serializer for uploading Forebet tips data."""
    date = serializers.DateField(required=True)
    data = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('data') and not attrs.get('file'):
            raise serializers.ValidationError("Either 'data' or 'file' must be provided.")
        return attrs


class ForebetResultsUploadSerializer(serializers.Serializer):
    """Serializer for uploading Forebet results data."""
    date = serializers.DateField(required=True)
    data = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('data') and not attrs.get('file'):
            raise serializers.ValidationError("Either 'data' or 'file' must be provided.")
        return attrs


class CombinedMatchUploadSerializer(serializers.Serializer):
    """Serializer for uploading combined match data."""
    date = serializers.DateField(required=True)
    data = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('data') and not attrs.get('file'):
            raise serializers.ValidationError("Either 'data' or 'file' must be provided.")
        return attrs


class MergedMatchUploadSerializer(serializers.Serializer):
    """Serializer for uploading merged match data."""
    date = serializers.DateField(required=True)
    data = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('data') and not attrs.get('file'):
            raise serializers.ValidationError("Either 'data' or 'file' must be provided.")
        return attrs


class MarketSelectorsUploadSerializer(serializers.Serializer):
    """Serializer for uploading market selectors data."""
    date = serializers.DateField(required=True)
    data = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('data') and not attrs.get('file'):
            raise serializers.ValidationError("Either 'data' or 'file' must be provided.")
        return attrs


class SingleBetsUploadSerializer(serializers.Serializer):
    """Serializer for uploading single bets data."""
    date = serializers.DateField(required=True)
    data = serializers.DictField(required=False)
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('data') and not attrs.get('file'):
            raise serializers.ValidationError("Either 'data' or 'file' must be provided.")
        return attrs
