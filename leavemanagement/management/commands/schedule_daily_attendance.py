from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json

class Command(BaseCommand):
    help = "Schedule the Daily Attendance Processing Task"

    def handle(self, *args, **kwargs):
        # Create a daily schedule at midnight
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",  # Midnight
            day_of_week="*",  # Every day
            day_of_month="*",  # Every day
            month_of_year="*",  # Every month
        )

        task_name = "Daily Attendance Processing Task"
        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                crontab=schedule,
                name=task_name,
                task="leavemanagement.tasks.daily_attendance_processing_task",  # Adjust based on your app
                kwargs=json.dumps({}),
                one_off=False,
            )
            self.stdout.write(self.style.SUCCESS("✅ Celery Beat Task Scheduled to Run Daily at Midnight!"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Task already exists!"))
