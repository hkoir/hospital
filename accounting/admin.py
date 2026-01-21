from django.contrib import admin
from.models import JournalEntry,JournalEntryLine,FiscalYear,Account,BankAccount

admin.site.register(Account)
admin.site.register(FiscalYear)
admin.site.register(JournalEntry)
admin.site.register(JournalEntryLine)
admin.site.register(BankAccount)
# Register your models here.
