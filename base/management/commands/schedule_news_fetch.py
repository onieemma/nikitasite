from django.core.management.base import BaseCommand
from background_task.models import Task
from base.tasks import fetch_news_task

class Command(BaseCommand):
    help = "Schedule the hourly news fetch task"

    def handle(self, *args, **options):
        # Clear old scheduled version
        Task.objects.filter(task_name="fetch_news_task").delete()

        # Schedule the new hourly run
        fetch_news_task(repeat=3600)

        self.stdout.write(self.style.SUCCESS("News fetch task scheduled to run every hour"))
