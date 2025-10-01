from django import forms
from django.forms import inlineformset_factory
from .models import FiscalYear, Account, JournalEntry, JournalEntryLine

class FiscalYearForm(forms.ModelForm):
    class Meta:
        model = FiscalYear
        fields = ['year_start', 'year_end', 'is_active']

        widgets={
            'year_start':forms.DateInput(attrs={'type':"date"}),
            'year_end':forms.DateInput(attrs={'type':'date'})
        }

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'name', 'type', 'parent']




class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['date', 'description', 'reference','fiscal_year']
        widgets={
            'date':forms.DateInput(attrs={'type':"date"}),
            'description':forms.TextInput(attrs={
                'style':'height:50px',
                'class':'form-control'
            })
         
        }

from django.db.models import Q

class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'description', 'debit', 'credit']





JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=2,
    can_delete=True
)
