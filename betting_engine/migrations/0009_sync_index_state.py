# Sync Django migration state with actual DB - indexes were fixed by 0008_fix_index_names

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('betting_engine', '0008_fix_index_names'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveIndex(
                    model_name='betsettlementsnapshot',
                    name='betting_eng_date_7a8b2c_idx',
                ),
                migrations.AddIndex(
                    model_name='betsettlementsnapshot',
                    index=models.Index(fields=['date'], name='betting_eng_date_0704a9_idx'),
                ),
                migrations.RemoveIndex(
                    model_name='marketselectormlrun',
                    name='betting_eng_mlrun_date_idx',
                ),
                migrations.AddIndex(
                    model_name='marketselectormlrun',
                    index=models.Index(fields=['date'], name='betting_eng_date_cf392f_idx'),
                ),
            ],
            database_operations=[],
        ),
    ]
