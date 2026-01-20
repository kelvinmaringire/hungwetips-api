from django.core.management.base import BaseCommand
from betting_engine.services.forebet_tips import ForebetScraper

class Command(BaseCommand):
    help = "Scrape Forebet tips"

    def handle(self, *args, **options):
        scraper = ForebetScraper()
        scraper.run()

        self.stdout.write(self.style.SUCCESS("Scraping completed"))

