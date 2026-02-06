# hungwetips-api

## SQLite Analysis Database

A SQLite database (`hungwetips_analysis.db`) is automatically maintained at the project root for data analysis in Jupyter notebooks. This database contains the same betting data as the main PostgreSQL database, synchronized automatically when data is imported.

### Usage in Jupyter

You can access the SQLite database directly from Jupyter notebooks:

```python
import sqlite3
import pandas as pd

# Connect to the analysis database
conn = sqlite3.connect('hungwetips_analysis.db')

# Query data
df = pd.read_sql_query("""
    SELECT * FROM betting_engine_match 
    WHERE date >= date('now', '-7 days')
    ORDER BY date DESC
""", conn)

conn.close()
```

Alternatively, use Django's ORM in Jupyter:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hungwetips.settings.dev')
django.setup()

from betting_engine.models import Match, BetwayOdds, ForebetTip

# Query using the analytics database
matches = Match.objects.using('analytics').filter(date__gte='2026-01-01')
```

### Database Schema

The analysis database contains the following tables:
- `betting_engine_match` - Match information
- `betting_engine_betwayodds` - Betway odds data
- `betting_engine_forebettip` - Forebet predictions
- `betting_engine_forebetresult` - Match results
- `betting_engine_combinedmatch` - Combined match data
- `betting_engine_marketselection` - Market selection flags
- `betting_engine_singlebetsnapshot` - Betting snapshots

All data is automatically synchronized when services save data (both JSON files and databases are updated).

