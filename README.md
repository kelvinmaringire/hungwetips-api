# hungwetips-api

Backend API for HungweTips betting data and automation.

### Usage in Jupyter

You can query the PostgreSQL database from Jupyter notebooks using Django's ORM:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hungwetips.settings.dev')
django.setup()

from betting_engine.models import BetwayOdds, ForebetTip, ForebetResult, CombinedMatch

# Query data
matches = CombinedMatch.objects.filter(date__gte='2026-01-01')
```
