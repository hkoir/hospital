from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json

class Command(BaseCommand):
    help = "Schedule paid plan"

    def handle(self, *args, **kwargs):
        schedule_new_year, created = CrontabSchedule.objects.get_or_create(
            minute="0",
            hour="0",  # Midnight
            day_of_week="*",  # Any day of the week
            day_of_month="*",  # Runs on 1st day of the month
            month_of_year="*",  # Runs in January
        )

        task_name = "Carry Forward Leave Task (January 1st)"  
        if not PeriodicTask.objects.filter(name=task_name).exists():
            PeriodicTask.objects.create(
                crontab=schedule_new_year,
                name=task_name,
                task="clients.tasks.check_trial_expiry",  
                kwargs=json.dumps({}),  
                one_off=False, 
            )
            self.stdout.write(self.style.SUCCESS("✅ Celery Beat Task Scheduled for January 1st at Midnight!"))
        else:
            self.stdout.write(self.style.WARNING("⚠ Task already exists!"))



# python manage.py schedule_carry_forward

# Restart Celery Beat
# After adding the periodic task, restart Celery Beat to load the new schedule.
# celery -A dscm beat --detach