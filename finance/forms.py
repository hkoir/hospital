from django import forms

from.models import AllExpenses,Asset

class AssetForm(forms.ModelForm):
     class Meta:
        model = Asset
        exclude = ['asset_code','user','current_value','last_depreciation_date']
        widgets={
            'purchase_date':forms.DateInput(attrs={
                'type':'date'
            })
        }


class ExpenseForm(forms.ModelForm):
     class Meta:
        model = AllExpenses
        exclude = ['expense_code','user','asset','depreciation_cost']
     
     