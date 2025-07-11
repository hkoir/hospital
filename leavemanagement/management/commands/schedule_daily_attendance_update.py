from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json
from datetime import timedelta

class Command(BaseCommand):
    help = "Schedule the Daily Attendance Update Task for Every Day at Midnight"

    def handle(self, *args, **kwargs):
        # Schedule for every day at midnight (00:00)
        schedule_daily_update, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",  # Midnight
            day_of_week="*",  # Every day of the week
            day_of_month="*",  # Every day of the month
            month_of_year="*",  # Every month
        )

        task_name = "Daily Attendance Update Task (Midnight)"
        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                crontab=schedule_daily_update,
                name=task_name,
                task="leavemanagement.tasks.daily_attendance_update_task",  # The actual Celery task
                kwargs=json.dumps({}),  # Pass any extra arguments if needed
                one_off=False,  # Ensures it runs daily at midnight
            )
            self.stdout.write(self.style.SUCCESS("✅ Celery Beat Task Scheduled for Daily Attendance Update at Midnight!"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Task already exists!"))
