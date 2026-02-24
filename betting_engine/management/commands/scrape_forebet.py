from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from betting_engine.services.forebet_tips import ForebetScraper


class Command(BaseCommand):
    help = "Scrape Forebet tips"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date for tips in YYYY-MM-DD (defaults to tomorrow). Use same date as workflow for alignment.',
            default=None,
        )

    def handle(self, *args, **options):
        tips_date = None
        if options.get('date'):
            try:
                dt = datetime.strptime(options['date'], '%Y-%m-%d')
                tips_date = dt.date()
            except ValueError:
                raise CommandError(f"Invalid date format: {options['date']}. Use YYYY-MM-DD.")

        scraper = ForebetScraper(tips_date=tips_date)
        scraper.run()

        self.stdout.write(self.style.SUCCESS("Scraping completed"))

