from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json

class Command(BaseCommand):
    help = "Schedule the Monthly Leave Accrual Task for the last day of every month"

    def handle(self, *args, **kwargs):
        # Schedule for the last day of every month at midnight
        schedule_monthly_accrual, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",  # Midnight
            day_of_week="*",  # Any day of the week
            day_of_month="L",  # 'L' means last day of the month
            month_of_year="*",  # Every month
        )

        task_name = "Monthly Leave Accrual Task (Last Day of Month)"
        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                crontab=schedule_monthly_accrual,
                name=task_name,
                task="leavemanagement.tasks.monthly_leave_accrual_update_task",  # Ensure this is correct
                kwargs=json.dumps({}),  # Pass any extra arguments if needed
                one_off=False,  # Ensures it runs every month on the last day
            )
            self.stdout.write(self.style.SUCCESS("✅ Celery Beat Task Scheduled for the Last Day of Every Month!"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Task already exists!"))



# python manage.py schedule_monthly_accrual

# Restart Celery Beat
# After adding the periodic task, restart Celery Beat to load the new schedule.
# celery -A dscm beat --detach