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

    def handle(self, *args, **options):
        date_str = options.get('date')
        scraper = BetwayAutomation()
        result = scraper.run(date_str=date_str)

        if result:
            self.stdout.write(self.style.SUCCESS("Betting automation completed"))
        else:
            self.stdout.write(self.style.ERROR("Betting automation failed"))
