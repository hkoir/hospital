from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json


class Command(BaseCommand):
    help = "Schedule daily subscription renewal checks"
    def handle(self, *args, **kwargs):
        schedule_daily, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",  # Midnight
            day_of_month="*",  # Every day
            month_of_year="*",  # Every month
            day_of_week="*",  # Any day of the week
        )

        task_name = "Daily Subscription Renewal Check"  

        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                crontab=schedule_daily,
                name=task_name,
                task="clients.tasks.check_and_renew_subscriptions",  
                kwargs=json.dumps({}),  
                one_off=False,  # Runs daily
            )
            self.stdout.write(self.style.SUCCESS("✅ Celery Beat Task Scheduled to run daily at Midnight!"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Task already exists!"))


# python manage.py schedule_carry_forward

# Restart Celery Beat
# After adding the periodic task, restart Celery Beat to load the new schedule.
# celery -A dscm beat --detach