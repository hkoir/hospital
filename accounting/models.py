from django.db import models


class FiscalYear(models.Model):
    year_start = models.DateField()
    year_end = models.DateField()
    is_active = models.BooleanField(default=True)
    
    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()
        
    def __str__(self):
        return f"FY {self.year_start.year}-{self.year_end.year}"

    

class Account(models.Model):
    ACCOUNT_TYPES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]
    code = models.CharField(max_length=20, unique=True)  # e.g., 1001
    name = models.CharField(max_length=100)             # e.g., Cash, Sales Revenue
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.code} - {self.name}"

from accounts.models import CustomUser

class JournalEntry(models.Model):
    date = models.DateField()
    fiscal_year = models.ForeignKey(FiscalYear, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True, null=True)
    reference = models.CharField(max_length=50, blank=True, null=True)  # e.g., Invoice ID
    created_by=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_debits(self):
        return sum(line.debit for line in self.lines.all())

    def total_credits(self):
        return sum(line.credit for line in self.lines.all())

    def is_balanced(self):
        return self.total_debits() == self.total_credits()

    def __str__(self):
        return f"{self.reference} ({self.date})"


class JournalEntryLine(models.Model):
    entry = models.ForeignKey(JournalEntry, related_name="lines", on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True, null=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.account} | Dr {self.debit} / Cr {self.credit}"




class TransactionSource(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE)
    app_label = models.CharField(max_length=50)   # e.g., "sales_pos"
    object_id = models.PositiveIntegerField()     # ID of invoice/purchase/payroll




