# from django.core.management.base import BaseCommand
# from background_task.models import Task
# from base.tasks import fetch_news_task

# class Command(BaseCommand):
#     help = "Schedule the hourly news fetch task"

#     def handle(self, *args, **options):
#         # Clear old scheduled version
#         Task.objects.filter(task_name="fetch_news_task").delete()

#         # Schedule the new hourly run
#         fetch_news_task(repeat=3600)

#         self.stdout.write(self.style.SUCCESS("News fetch task scheduled to run every hour"))


from django.core.management.base import BaseCommand
from background_task.models import Task
from base.tasks import fetch_news_task
from django.utils import timezone


class Command(BaseCommand):
    help = "Schedule the hourly news fetch task"

    def add_arguments(self, parser):
        """Add optional command arguments"""
        parser.add_argument(
            '--interval',
            type=int,
            default=3600,
            help='Interval in seconds between fetches (default: 3600 = 1 hour)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing scheduled tasks before scheduling new one'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        clear_all = options['clear']
        
        if clear_all:
            # Clear ALL scheduled tasks
            count = Task.objects.all().count()
            Task.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} scheduled task(s)")
            )
        else:
            # Clear only news fetch tasks
            count = Task.objects.filter(
                task_name__contains="fetch_news_task"
            ).count()
            Task.objects.filter(
                task_name__contains="fetch_news_task"
            ).delete()
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} news fetch task(s)")
            )

        # Schedule the new task
        fetch_news_task(repeat=interval, repeat_until=None)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ News fetch task scheduled successfully!\n"
                f"  • Interval: Every {interval} seconds ({interval//3600} hour(s))\n"
                f"  • Next run: Immediately (when process_tasks runs)\n"
                f"\nTo start the background worker, run:\n"
                f"  python manage.py process_tasks"
            )
        )
