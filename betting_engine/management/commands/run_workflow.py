from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path


class Command(BaseCommand):
    help = "Run complete betting workflow: scrape, match, merge, train (optional), predict, and automate betting"

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-training',
            action='store_true',
            help='Skip model training step (use existing models)',
            default=False,
        )
        parser.add_argument(
            '--skip-betting',
            action='store_true',
            help='Skip automated betting step',
            default=False,
        )
        parser.add_argument(
            '--skip-merge',
            action='store_true',
            help='Skip merging yesterday results step',
            default=False,
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYY-MM-DD format (defaults to tomorrow)',
            default=None,
        )
        parser.add_argument(
            '--stop-on-error',
            action='store_true',
            help='Stop workflow on first error (default: continue and report)',
            default=False,
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🚀 HungweTips Complete Workflow"))
        self.stdout.write("=" * 70)
        
        # Determine date
        if options['date']:
            try:
                date_obj = datetime.strptime(options['date'], '%Y-%m-%d')
                date_str = options['date']
            except ValueError:
                raise CommandError(f"Invalid date format: {options['date']}. Use YYYY-MM-DD format.")
        else:
            SAST = timezone(timedelta(hours=2))
            today_sast = datetime.now(SAST)
            tomorrow_sast = today_sast + timedelta(days=1)
            date_str = tomorrow_sast.strftime('%Y-%m-%d')
        
        self.stdout.write(f"\n📅 Target Date: {date_str}")
        self.stdout.write(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Define workflow steps
        steps = [
            {
                'name': 'Step 1: Scrape Forebet Tips',
                'command': 'scrape_forebet',
                'args': {},
                'required': True,
            },
            {
                'name': 'Step 2: Scrape Betway Odds',
                'command': 'scrape_betway',
                'args': {},
                'required': True,
            },
            {
                'name': 'Step 3: Match Betway with Forebet',
                'command': 'match_betway_forebet',
                'args': {'date': date_str},
                'required': True,
            },
            {
                'name': 'Step 4: Merge Yesterday Results',
                'command': 'merge_yesterday_results',
                'args': {},
                'required': not options['skip_merge'],
                'skip': options['skip_merge'],
            },
            {
                'name': 'Step 5: Train ML Models (Optional)',
                'command': 'train_model',
                'args': {'model': 'all'},
                'required': False,
                'skip': options['skip_training'],
            },
            {
                'name': 'Step 6: Make Predictions (Trains automatically if Step 5 skipped)',
                'command': 'predict_matches',
                # If Step 5 ran, skip training in Step 6 to avoid double training
                # If Step 5 was skipped, Step 6 will train automatically (default behavior)
                'args': {'date': date_str, 'model': 'all', 'no_train': not options['skip_training']},
                'required': True,
            },
            {
                'name': 'Step 7: Automate Betting',
                'command': 'automate_betting',
                'args': {'date': date_str},
                'required': False,
                'skip': options['skip_betting'],
            },
        ]
        
        # Track progress
        completed_steps = []
        failed_steps = []
        skipped_steps = []
        
        # Execute each step
        for i, step in enumerate(steps, 1):
            step_num = f"[{i}/{len(steps)}]"
            
            # Check if step should be skipped
            if step.get('skip', False):
                self.stdout.write(f"\n{step_num} ⏭️  SKIPPED: {step['name']}")
                skipped_steps.append(step['name'])
                continue
            
            # Execute step
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write(f"{step_num} 🔄 {step['name']}")
            self.stdout.write("=" * 70)
            
            try:
                start_time = datetime.now()
                
                # Call the command
                call_command(step['command'], **step['args'])
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                self.stdout.write(self.style.SUCCESS(
                    f"\n✓ {step['name']} completed successfully ({duration:.1f}s)"
                ))
                completed_steps.append(step['name'])
                
            except CommandError as e:
                error_msg = str(e)
                self.stdout.write(self.style.ERROR(f"\n✗ {step['name']} FAILED"))
                self.stdout.write(self.style.ERROR(f"  Error: {error_msg}"))
                
                failed_steps.append({
                    'name': step['name'],
                    'error': error_msg,
                    'step_number': i
                })
                
                if step.get('required', False):
                    self.stdout.write(self.style.WARNING(
                        f"\n⚠️  This step is REQUIRED. Workflow cannot continue."
                    ))
                    if options['stop_on_error']:
                        break
                else:
                    self.stdout.write(self.style.WARNING(
                        f"\n⚠️  This step is optional. Continuing workflow..."
                    ))
                    
            except Exception as e:
                error_msg = str(e)
                self.stdout.write(self.style.ERROR(f"\n✗ {step['name']} FAILED"))
                self.stdout.write(self.style.ERROR(f"  Unexpected error: {error_msg}"))
                
                failed_steps.append({
                    'name': step['name'],
                    'error': error_msg,
                    'step_number': i
                })
                
                if step.get('required', False):
                    self.stdout.write(self.style.WARNING(
                        f"\n⚠️  This step is REQUIRED. Workflow cannot continue."
                    ))
                    if options['stop_on_error']:
                        break
        
        # Final summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("📊 WORKFLOW SUMMARY")
        self.stdout.write("=" * 70)
        
        self.stdout.write(f"\n✅ Completed: {len(completed_steps)}/{len(steps)}")
        for step in completed_steps:
            self.stdout.write(f"   ✓ {step}")
        
        if skipped_steps:
            self.stdout.write(f"\n⏭️  Skipped: {len(skipped_steps)}")
            for step in skipped_steps:
                self.stdout.write(f"   ⏭️  {step}")
        
        if failed_steps:
            self.stdout.write(f"\n❌ Failed: {len(failed_steps)}")
            for step_info in failed_steps:
                self.stdout.write(f"   ✗ {step_info['name']} (Step {step_info['step_number']})")
                self.stdout.write(f"     Error: {step_info['error']}")
        
        # Overall status
        self.stdout.write("\n" + "=" * 70)
        if not failed_steps:
            self.stdout.write(self.style.SUCCESS("🎉 WORKFLOW COMPLETED SUCCESSFULLY!"))
            self.stdout.write("=" * 70)
        else:
            required_failed = [s for s in failed_steps if any(
                step['name'] == s['name'] and step.get('required', False) 
                for step in steps
            )]
            
            if required_failed:
                self.stdout.write(self.style.ERROR("❌ WORKFLOW FAILED"))
                self.stdout.write(self.style.ERROR("Required steps failed. Please fix errors and retry."))
                self.stdout.write("=" * 70)
                sys.exit(1)
            else:
                self.stdout.write(self.style.WARNING("⚠️  WORKFLOW COMPLETED WITH WARNINGS"))
                self.stdout.write(self.style.WARNING("Some optional steps failed, but workflow completed."))
                self.stdout.write("=" * 70)
        
        self.stdout.write(f"\n⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

