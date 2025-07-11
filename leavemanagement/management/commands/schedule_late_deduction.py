from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json

class Command(BaseCommand):
    help = "Schedule the Late Deduction Task to run daily at 11:59 PM"

    def handle(self, *args, **kwargs):
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute="59",
            hour="23",  # 11:59 PM
            day_of_week="*",  # Every day
            day_of_month="*",  # Every day of the month
            month_of_year="*",  # Every month
        )

        task_name = "Daily Late Deduction Task"
        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                crontab=schedule,
                name=task_name,
                task="leavemanagement.tasks.check_and_deduct_late_leaves_task",
                kwargs=json.dumps({}),
                one_off=False,
            )

        self.stdout.write(self.style.SUCCESS("✅ Celery Beat Task Scheduled for Late Deduction at 11:59 PM!"))
