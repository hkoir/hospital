from django.db import models
from django.conf import settings


class BankAccount(models.Model):  
    ACCOUNT_TYPE_CHOICES = (
        ('CASH', 'Cash'),
        ('BANK', 'Bank'),
        ('MOBILE', 'Mobile Payment'),
    )

    name = models.CharField(max_length=100, help_text="Bank or account name")
    account_number = models.CharField(max_length=50, blank=True, null=True, help_text="Bank account number if applicable")
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='BANK')
    bank_name = models.CharField(max_length=100, blank=True, null=True, help_text="Bank name for bank accounts")
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, default='BDT', help_text="Currency of the account")
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

    def deposit(self, amount):
        self.balance += amount
        self.save(update_fields=['balance'])

    def withdraw(self, amount):   
        if amount > self.balance:
            raise ValueError("Insufficient funds in account")
        self.balance -= amount
        self.save(update_fields=['balance'])



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
    account = models.ForeignKey(Account, on_delete=models.PROTECT,related_name="journal_entries")
    description = models.CharField(max_length=255, blank=True, null=True)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.account} | Dr {self.debit} / Cr {self.credit}"




class TransactionSource(models.Model):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE)
    app_label = models.CharField(max_length=50)   # e.g., "sales_pos"
    object_id = models.PositiveIntegerField()     # ID of invoice/purchase/payroll




