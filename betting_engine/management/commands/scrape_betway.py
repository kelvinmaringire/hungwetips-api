from django.core.management.base import BaseCommand
from betting_engine.services.betway_odds import BetwayScraper

class Command(BaseCommand):
    help = "Scrape Betway odds"

    def handle(self, *args, **options):
        scraper = BetwayScraper()
        html = scraper.run()

        self.stdout.write(self.style.SUCCESS("Scraping completed"))
