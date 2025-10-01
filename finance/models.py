
from django.db import models
from accounts.models import CustomUser
from django.utils import timezone
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from dateutil.relativedelta import relativedelta
import uuid





class PurchaseInvoice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='purchase_invoice_user')
    purchase_shipment = models.ForeignKey('logistics.PurchaseShipment', related_name='shipment_invoices', on_delete=models.CASCADE, null=True, blank=True)
    invoice_number = models.CharField(max_length=150, unique=True, blank=True, null=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20, null=True, blank=True,
        choices=[
            ('SUBMITTED', 'Submitted'),
            ('FULLY_PAID', 'Fully Paid'),
            ('PARTIALLY_PAID', 'Partially Paid'),
            ('CANCELLED', 'Cancelled')
        ]
    )
    
    AIT_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    AIT_type = models.CharField(max_length=50, choices=[('inclusive', 'inclusive'), ('exclusive', 'exclusive')], null=True, blank=True)
    VAT_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    VAT_type = models.CharField(max_length=50, choices=[('inclusive', 'inclusive'), ('exclusive', 'exclusive')], null=True, blank=True)
    issued_date = models.DateTimeField(null=True, blank=True)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    net_due_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # Added for calculation
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_tax_amounts(self):
        base_amount = Decimal(self.amount_due or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        vat_rate = Decimal(self.VAT_rate or 0) / 100
        ait_rate = Decimal(self.AIT_rate or 0) / 100

        if self.AIT_type == 'inclusive':
            self.ait_amount = (base_amount - (base_amount / (1 + ait_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            base_amount -= self.ait_amount  # Adjust base for VAT calculation
        else:
            self.ait_amount = (base_amount * ait_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  

        if self.VAT_type == 'inclusive':
            self.vat_amount = (base_amount - (base_amount / (1 + vat_rate))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            base_amount -= self.vat_amount  # Adjust base after VAT extraction
        else:
            self.vat_amount = (base_amount * vat_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if self.VAT_type == 'exclusive':
            base_amount += self.vat_amount
        if self.AIT_type == 'exclusive':
            base_amount += self.ait_amount
        self.net_due_amount = base_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
   
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"PINV-{uuid.uuid4().hex[:8].upper()}"
        self.calculate_tax_amounts()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} - VAT: {self.vat_amount} - AIT: {self.ait_amount} - Net Due: {self.net_due_amount}"
    
    @property
    def total_paid_amount(self):
        return self.purchase_payment_invoice.aggregate(Sum('amount'))['amount__sum'] or 0

    @property
    def is_fully_paid(self):
        total_paid = self.purchase_payment_invoice.aggregate(Sum('amount'))['amount__sum'] or 0
        return total_paid >= self.net_due_amount
    @property
    def remaining_balance(self):
        total_paid = self.purchase_payment_invoice.aggregate(Sum('amount'))['amount__sum'] or 0
        return self.net_due_amount - total_paid



class PurchaseInvoiceAttachment(models.Model):
    purchase_invoice = models.ForeignKey(PurchaseInvoice, related_name='purchase_invoice_attachment', on_delete=models.CASCADE)
    file = models.ImageField(upload_to='purchase_invoice/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PurchasePayment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='purchase_payment_user')
    purchase_invoice = models.ForeignKey(PurchaseInvoice, related_name='purchase_payment_invoice', on_delete=models.CASCADE, null=True, blank=True) 
    payment_id =models.CharField(max_length=20, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=[
        ('CASH', 'Cash'), 
        ('CREDIT', 'Credit Card'), 
        ('BANK', 'Bank Transfer')
    ])

    status = models.CharField(max_length=20,null=True,blank=True,
            choices=[
                ('IN_PROCESS','In Process'),
                ('FULLY_PAID','Fully Paid'),
                 ('PARTIALLY_PAID','Partially Paid')
            ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = f"PPAYID-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment of {self.amount} for Purchase Order {self.purchase_invoice.invoice_number}"
    
    # @property
    # def is_fully_paid(self):
    #     total_invoice = self.purchase_invoice.aggregate(Sum('amount_due'))['amount_due__sum'] or Decimal(0)
    #     tolerance = Decimal('0.01')  
    #     return abs(total_invoice - self.amount) <= tolerance 
        
    @property
    def is_fully_paid(self):
        total_paid = self.purchase_invoice.purchase_payment_invoice.aggregate(Sum('amount'))['amount__sum'] or Decimal(0)
        tolerance = Decimal('0.01')  # Small tolerance for floating-point calculations
        return abs(total_paid - self.purchase_invoice.amount_due) <= tolerance

class PurchasePaymentAttachment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    purchase_invoice = models.ForeignKey(PurchaseInvoice, related_name='purchase_payment_attachment', on_delete=models.CASCADE)
    file = models.ImageField(upload_to='purchase_payment/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)










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
