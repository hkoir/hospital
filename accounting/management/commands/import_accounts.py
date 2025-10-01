import csv
from django.core.management.base import BaseCommand
from accounting.models import Account
from clients.models import Client
from django_tenants.utils import schema_context


class Command(BaseCommand):
    help = "Import Chart of Accounts for a specific tenant from CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to accounts.csv")
        parser.add_argument(
            "--tenant_id", type=int, required=True, help="ID of the tenant (Client)"
        )

    def handle(self, *args, **kwargs):
        file_path = kwargs["csv_file"]
        tenant_id = kwargs["tenant_id"]

        try:
            tenant = Client.objects.get(id=tenant_id)
        except Client.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant with id {tenant_id} does not exist"))
            return

        self.stdout.write(f"Importing accounts for tenant: {tenant.name} ({tenant.schema_name})")
        
        # Read CSV into memory
        try:
            with open(file_path, newline="", encoding="utf-8") as csvfile:
                reader = list(csv.DictReader(csvfile))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"CSV file not found: {file_path}"))
            return

        if not reader:
            self.stdout.write(self.style.WARNING("CSV file is empty"))
            return

        with schema_context(tenant.schema_name):
            accounts_map = {}

            # First pass: create accounts without parent
            for row in reader:
                code = row.get("code", "").strip()
                name = row.get("name", "").strip()
                type_ = row.get("type", "").strip().upper()

                if not code or not name or not type_:
                    self.stdout.write(self.style.WARNING(f"Skipping invalid row: {row}"))
                    continue

                acc, created = Account.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": name,
                        "type": type_,
                        "parent": None,
                    },
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created account: {code} - {name}"))
                else:
                    self.stdout.write(self.style.NOTICE(f"Account already exists: {code} - {name}"))

                accounts_map[code] = acc

            # Second pass: assign parent accounts
            for row in reader:
                code = row.get("code", "").strip()
                parent_code = row.get("parent", "").strip()

                if parent_code:
                    parent = accounts_map.get(parent_code)
                    acc = accounts_map.get(code)

                    if acc and parent and acc.parent != parent:
                        acc.parent = parent
                        acc.save()
                        self.stdout.write(self.style.SUCCESS(f"Assigned parent {parent_code} to {code}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Chart of Accounts imported successfully for tenant {tenant.name}"))
