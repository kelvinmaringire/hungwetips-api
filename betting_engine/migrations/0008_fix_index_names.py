# Generated manually - safe migration for index renames when source indexes may not exist

from django.db import migrations


def fix_indexes(apps, schema_editor):
    """Rename indexes if they exist; create new ones if old don't exist."""
    from django.db import connection

    with connection.cursor() as cursor:
        # BetSettlementSnapshot: betting_eng_date_7a8b2c_idx -> betting_eng_date_0704a9_idx
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'betting_engine_betsettlementsnapshot'
            LIMIT 1
        """)
        if cursor.fetchone():
            cursor.execute("""
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'betting_eng_date_7a8b2c_idx'
                LIMIT 1
            """)
            if cursor.fetchone():
                cursor.execute('ALTER INDEX IF EXISTS betting_eng_date_7a8b2c_idx RENAME TO betting_eng_date_0704a9_idx')
            else:
                cursor.execute("""
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'betting_engine_betsettlementsnapshot'
                    AND indexname = 'betting_eng_date_0704a9_idx'
                    LIMIT 1
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS betting_eng_date_0704a9_idx
                        ON betting_engine_betsettlementsnapshot (date)
                    """)

        # MarketSelectorMLRun: betting_eng_mlrun_date_idx -> betting_eng_date_cf392f_idx
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'betting_engine_marketselectormlrun'
            LIMIT 1
        """)
        if cursor.fetchone():
            cursor.execute("""
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'betting_eng_mlrun_date_idx'
                LIMIT 1
            """)
            if cursor.fetchone():
                cursor.execute('ALTER INDEX IF EXISTS betting_eng_mlrun_date_idx RENAME TO betting_eng_date_cf392f_idx')
            else:
                cursor.execute("""
                    SELECT 1 FROM pg_indexes
                    WHERE tablename = 'betting_engine_marketselectormlrun'
                    AND indexname = 'betting_eng_date_cf392f_idx'
                    LIMIT 1
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS betting_eng_date_cf392f_idx
                        ON betting_engine_marketselectormlrun (date)
                    """)


def reverse_fix_indexes(apps, schema_editor):
    """Reverse: rename back if new indexes exist."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM pg_indexes WHERE indexname = 'betting_eng_date_0704a9_idx' LIMIT 1
        """)
        if cursor.fetchone():
            cursor.execute('ALTER INDEX IF EXISTS betting_eng_date_0704a9_idx RENAME TO betting_eng_date_7a8b2c_idx')

        cursor.execute("""
            SELECT 1 FROM pg_indexes WHERE indexname = 'betting_eng_date_cf392f_idx' LIMIT 1
        """)
        if cursor.fetchone():
            cursor.execute('ALTER INDEX IF EXISTS betting_eng_date_cf392f_idx RENAME TO betting_eng_mlrun_date_idx')


class Migration(migrations.Migration):

    dependencies = [
        ('betting_engine', '0007_add_market_selector_ml_run'),
    ]

    operations = [
        migrations.RunPython(fix_indexes, reverse_fix_indexes),
    ]
