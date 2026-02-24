from django.core.management.base import BaseCommand
from betting_engine.services.betway_automation import BetwayAutomation

class Command(BaseCommand):
    help = "Automate Betway betting with ML-based filtering"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date string in YYYY-MM-DD format (default: today)',
        )
        parser.add_argument(
            '--no-headless',
            action='store_true',
            help='Show the browser window (headed mode)',
        )

    def handle(self, *args, **options):
        date_str = options.get('date')
        headless = not options.get('no_headless', False)
        scraper = BetwayAutomation(headless=headless)
        result = scraper.run(date_str=date_str)

        if result:
            self.stdout.write(self.style.SUCCESS("Betting automation completed"))
        else:
            self.stdout.write(self.style.ERROR("Betting automation failed"))
