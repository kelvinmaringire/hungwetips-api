"""
Serializers for the betting_engine app.
Handles serialization of matches, odds, tips, results, and betting data.
"""
from rest_framework import serializers
from .models import (
    Match, BetwayOdds, ForebetTip, ForebetResult,
    CombinedMatch, MarketSelection, SingleBetSnapshot
)


class MatchSerializer(serializers.ModelSerializer):
    """Serializer for Match model."""
    
    class Meta:
        model = Match
        fields = (
            'id', 'date', 'time', 'home_team', 'away_team',
            'country', 'league_name', 'forebet_match_id',
            'game_url', 'game_link', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class BetwayOddsSerializer(serializers.ModelSerializer):
    """Serializer for BetwayOdds model."""
    match = MatchSerializer(read_only=True)
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = BetwayOdds
        fields = (
            'id', 'match', 'match_id', 'date', 'odds_data',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ForebetTipSerializer(serializers.ModelSerializer):
    """Serializer for ForebetTip model."""
    match = MatchSerializer(read_only=True)
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = ForebetTip
        fields = (
            'id', 'forebet_match_id', 'match', 'match_id', 'date',
            'country', 'league_name', 'home_team', 'away_team',
            'game_link', 'preview_link', 'preview_html',
            'prob_1', 'prob_x', 'prob_2', 'pred',
            'home_pred_score', 'away_pred_score', 'avg_goals', 'kelly',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ForebetResultSerializer(serializers.ModelSerializer):
    """Serializer for ForebetResult model."""
    
    class Meta:
        model = ForebetResult
        fields = (
            'id', 'forebet_match_id', 'date',
            'home_correct_score', 'away_correct_score',
            'home_ht_score', 'away_ht_score',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class CombinedMatchSerializer(serializers.ModelSerializer):
    """Serializer for CombinedMatch model."""
    match = MatchSerializer(read_only=True)
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = CombinedMatch
        fields = (
            'id', 'match', 'match_id', 'date', 'match_confidence',
            'payload', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class MarketSelectionSerializer(serializers.ModelSerializer):
    """Serializer for MarketSelection model."""
    match = MatchSerializer(read_only=True)
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = MarketSelection
        fields = (
            'id', 'match', 'match_id', 'date',
            'home_over_bet', 'away_over_bet', 'home_draw_bet',
            'away_draw_bet', 'over_1_5_bet', 'extra_data',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SingleBetSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for SingleBetSnapshot model."""
    
    class Meta:
        model = SingleBetSnapshot
        fields = (
            'id', 'date', 'timestamp', 'total_bets',
            'placed_bets', 'failed_bets', 'bets',
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
