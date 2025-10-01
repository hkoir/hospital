from django.contrib import admin
from.models import JournalEntry,JournalEntryLine,FiscalYear


admin.site.register(FiscalYear)
admin.site.register(JournalEntry)
admin.site.register(JournalEntryLine)
# Register your models here.
