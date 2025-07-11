from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        x = 3
        y = 3
        result = x + y
        self.stdout.write(f"Sum: {result}")  # Django's recommended way to print in commands
