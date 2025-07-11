
from django.db import models
from accounts.models import CustomUser
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
import uuid




class Asset(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    asset_code = models.CharField(max_length=30, unique=True, blank=True)
    name = models.CharField(max_length=50)
    value = models.DecimalField(max_digits=20, decimal_places=2)   
    purchase_date = models.DateField(null=True, blank=True)
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # % per year
    current_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    last_depreciation_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):       
        if not self.asset_code:
            year = self.purchase_date.year if self.purchase_date else timezone.now().year
            count = Asset.objects.filter(purchase_date__year=year).count() + 1
            self.asset_code = f"AS{str(year)[-2:]}{count:06d}"

        if self.pk:
            previous = Asset.objects.get(pk=self.pk)
            if self.value != previous.value:
                self.current_value = self.value
        else:
            self.current_value = self.value

        super().save(*args, **kwargs)


    def apply_asset_depreciation(self):
        today = timezone.now().date()

        # Apply if last_depreciation_date is None (never depreciated)
        if self.last_depreciation_date is None or self.last_depreciation_date < today - relativedelta(months=1):
            if self.depreciation_rate:
                rate = self.depreciation_rate / Decimal('100.0')
                depreciation_amount = self.current_value * rate

                previous_value = self.current_value
                self.current_value -= depreciation_amount
                self.last_depreciation_date = today

                # Create expense record
                AllExpenses.objects.create(
                    user=self.user,
                    expense_head="Asset Depreciation",
                    amount=depreciation_amount,
                )

                # Save depreciation record
                AssetDepreciationRecord.objects.create(
                    asset=self,
                    depreciation_amount=depreciation_amount,
                    previous_value=previous_value,
                    new_value=self.current_value,
                    notes="Automated monthly depreciation"
                )

                self.save()
                return depreciation_amount
            else:
                return None  # No depreciation rate set
        else:
            return None  # Already depreciated this month

    def __str__(self):
        return f"{self.asset_code} - {self.name}"
    


    
class AssetDepreciationRecord(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='depreciation_records')
    depreciation_amount = models.DecimalField(max_digits=20, decimal_places=2,null=True,blank=True)
    previous_value = models.DecimalField(max_digits=20, decimal_places=2,null=True,blank=True)
    new_value = models.DecimalField(max_digits=20, decimal_places=2,null=True,blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {self.created_at} - Depreciation: {self.depreciation_amount}"



class AllExpenses(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    expense_code = models.CharField(max_length=30, unique=True, blank=True)
    expense_head = models.CharField(max_length=50, null=True, blank=True)   
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.expense_code:
            unique_part = uuid.uuid4().hex[:8].upper()
            self.expense_code = f"EX{unique_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.expense_code} - {self.expense_head}"
