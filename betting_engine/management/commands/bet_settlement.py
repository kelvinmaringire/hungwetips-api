from django.core.management.base import BaseCommand, CommandError
from betting_engine.services.bet_settlement import BetSettlement
from datetime import datetime, timedelta, timezone


class Command(BaseCommand):
    help = "Settle yesterday's bets: merge SingleBetSnapshot with MergedMatch to determine won/lost"

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYY-MM-DD format (defaults to yesterday)',
            default=None,
        )

    def handle(self, *args, **options):
        if options['date']:
            try:
                date_obj = datetime.strptime(options['date'], '%Y-%m-%d')
                date_str = options['date']
            except ValueError:
                raise CommandError(f"Invalid date format: {options['date']}. Use YYYY-MM-DD format.")
        else:
            SAST = timezone(timedelta(hours=2))
            today_sast = datetime.now(SAST)
            yesterday_sast = today_sast - timedelta(days=1)
            date_str = yesterday_sast.strftime('%Y-%m-%d')
            date_obj = yesterday_sast

        self.stdout.write(f"Settling bets for date: {date_str}")

        try:
            settlement = BetSettlement()
            settlement.settle_and_save(date_str)

            settlements = settlement.settle(date_str)
            total = len(settlements)
            won = sum(1 for s in settlements if s.get('settlement_status') == 'won')
            lost = sum(1 for s in settlements if s.get('settlement_status') == 'lost')
            pending = sum(1 for s in settlements if s.get('settlement_status') == 'pending')

            self.stdout.write(self.style.SUCCESS("\nBet settlement completed successfully!"))
            self.stdout.write("\n=== SUMMARY ===")
            self.stdout.write(f"Total settled bets: {total}")
            self.stdout.write(f"Won: {won}")
            self.stdout.write(f"Lost: {lost}")
            self.stdout.write(f"Pending (no result): {pending}")
            self.stdout.write(f"Output saved to: database")

            if settlements:
                sample = next((s for s in settlements if s.get('settlement_status') in ('won', 'lost')), settlements[0])
                self.stdout.write("\n=== SAMPLE SETTLEMENT ===")
                self.stdout.write(f"Match: {sample.get('home_team')} vs {sample.get('away_team')}")
                self.stdout.write(f"Bet: {sample.get('team')} ({sample.get('bet_type')}) @ {sample.get('odds')}")
                self.stdout.write(f"Result: {sample.get('home_correct_score')}-{sample.get('away_correct_score')}")
                self.stdout.write(f"Status: {sample.get('settlement_status')}")

        except Exception as e:
            raise CommandError(f"Error during bet settlement: {str(e)}")
