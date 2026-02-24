"""Train ML models for market selector filter from MergedMatch data."""
from django.core.management.base import BaseCommand

from betting_engine.services.market_selector_ml import MarketSelectorML


class Command(BaseCommand):
    help = "Train ML models for market selector filter from MergedMatch data"

    def handle(self, *args, **options):
        self.stdout.write("Training market selector ML models...")
        ml = MarketSelectorML()
        metrics = ml.train_models()

        if 'error' in metrics:
            self.stdout.write(self.style.ERROR(metrics['error']))
            return

        self.stdout.write(self.style.SUCCESS("\nTraining complete"))
        for bt, m in metrics.items():
            self.stdout.write(f"  {bt}: {m.get('samples', 0)} samples", ending='')
            if m.get('skipped'):
                self.stdout.write(f" - {m.get('reason', 'skipped')}")
            elif 'accuracy' in m:
                self.stdout.write(f" - accuracy: {m['accuracy']:.2%}")
            else:
                self.stdout.write("")
