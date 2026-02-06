# Generated migration for BetwayOdds refactor to JSON storage

from django.db import migrations, models


def migrate_data_to_json(apps, schema_editor):
    """Migrate existing BetwayOdds rows to new JSON structure."""
    BetwayOdds = apps.get_model('betting_engine', 'BetwayOdds')
    
    # Group existing rows by date
    from collections import defaultdict
    by_date = defaultdict(list)
    
    db_alias = schema_editor.connection.alias
    
    for row in BetwayOdds.objects.using(db_alias).all():
        match_data = {
            'time': getattr(row, 'time', None),
            'home_team': getattr(row, 'home_team', ''),
            'away_team': getattr(row, 'away_team', ''),
            'game_url': getattr(row, 'game_url', None),
            'home_win': getattr(row, 'home_win', None),
            'draw': getattr(row, 'draw', None),
            'away_win': getattr(row, 'away_win', None),
            'home_draw_no_bet': getattr(row, 'home_draw_no_bet', None),
            'away_draw_no_bet': getattr(row, 'away_draw_no_bet', None),
            'home_draw_odds': getattr(row, 'home_draw_odds', None),
            'away_draw_odds': getattr(row, 'away_draw_odds', None),
            'home_away_odds': getattr(row, 'home_away_odds', None),
            'total_over_1_5': getattr(row, 'total_over_1_5', None),
            'total_under_3_5': getattr(row, 'total_under_3_5', None),
            'BTTS_yes': getattr(row, 'BTTS_yes', None),
            'BTTS_no': getattr(row, 'BTTS_no', None),
            'home_team_over_0_5': getattr(row, 'home_team_over_0_5', None),
            'away_team_over_0_5': getattr(row, 'away_team_over_0_5', None),
        }
        # Add extra_data if it exists and has content
        if hasattr(row, 'extra_data') and getattr(row, 'extra_data', None):
            extra = getattr(row, 'extra_data', {})
            if isinstance(extra, dict):
                match_data.update(extra)
        
        by_date[row.date].append(match_data)
    
    # Delete all old rows
    BetwayOdds.objects.using(db_alias).all().delete()
    
    # Create new rows (one per date) with matches JSON
    for date, matches_list in by_date.items():
        BetwayOdds.objects.using(db_alias).create(date=date, matches=matches_list)


def reverse_migration(apps, schema_editor):
    """Reverse migration - expand JSON back to individual rows."""
    BetwayOdds = apps.get_model('betting_engine', 'BetwayOdds')
    
    # This is a destructive reverse - we'd need the old model structure
    # For now, just clear the data
    BetwayOdds.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('betting_engine', '0002_remove_forebettip_match_alter_betwayodds_options_and_more'),
    ]

    operations = [
        # Step 1: Add new matches field
        migrations.AddField(
            model_name='betwayodds',
            name='matches',
            field=models.JSONField(default=list),
        ),
        # Step 2: Migrate data
        migrations.RunPython(migrate_data_to_json, reverse_migration),
        # Step 3: Drop unique_together and index BEFORE removing fields
        # (Django needs the field names to exist to drop the constraints)
        migrations.AlterUniqueTogether(
            name='betwayodds',
            unique_together=set(),
        ),
        migrations.RemoveIndex(
            model_name='betwayodds',
            name='betting_eng_date_6f7f11_idx',
        ),
        # Step 4: Remove old fields
        migrations.RemoveField(
            model_name='betwayodds',
            name='time',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='home_team',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='away_team',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='game_url',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='home_win',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='draw',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='away_win',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='home_draw_no_bet',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='away_draw_no_bet',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='home_draw_odds',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='away_draw_odds',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='home_away_odds',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='total_over_1_5',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='total_under_3_5',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='BTTS_yes',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='BTTS_no',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='home_team_over_0_5',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='away_team_over_0_5',
        ),
        migrations.RemoveField(
            model_name='betwayodds',
            name='extra_data',
        ),
        # Step 5: Update Meta and add unique on date
        migrations.AlterModelOptions(
            name='betwayodds',
            options={'ordering': ['-date']},
        ),
        migrations.AlterField(
            model_name='betwayodds',
            name='date',
            field=models.DateField(db_index=True, unique=True),
        ),
    ]
