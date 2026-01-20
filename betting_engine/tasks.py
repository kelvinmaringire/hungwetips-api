from celery import shared_task
from .services.betway_odds import BetwayScraper

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3})
def scrape_betway(self):
    scraper = BetwayScraper(headless=True)
    return scraper.run()
