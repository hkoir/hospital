
from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, schema_context
from finance.models import Asset

class Command(BaseCommand):
    help = 'Apply depreciation to all assets for all tenants'

    def handle(self, *args, **kwargs):
        TenantModel = get_tenant_model()
        tenants = TenantModel.objects.exclude(schema_name='public')

        for tenant in tenants:
            self.stdout.write(f"\n--- Processing tenant: {tenant.schema_name} ---")

            with schema_context(tenant.schema_name):
                assets = Asset.objects.all()
                if not assets.exists():
                    self.stdout.write("No assets found for this tenant.")
                    continue

                for asset in assets:
                    self.stdout.write(f"Checking asset: {asset.asset_code} (current value: {asset.current_value})")
                    depreciation = asset.apply_asset_depreciation()
                    if depreciation:
                        self.stdout.write(
                            f"✅ Applied depreciation: -{depreciation:.2f}, "
                            f"new value: {asset.current_value:.2f}"
                        )
                    else:
                        self.stdout.write("⚠ No depreciation applied (maybe already updated this month or no rate set).")

        self.stdout.write("\nFinished processing all tenants.")
