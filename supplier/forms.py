from django import forms
from.models import SupplierPerformance

from.models import Supplier,Location



class AddSupplierForm(forms.ModelForm):   
    class Meta:
        model = Supplier
        exclude = ['supplier_id','user','history']




class AddLocationForm(forms.ModelForm):
   
    address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 3, 
                'style': 'height: 30px;', 
            }
        )
    )
    class Meta:
        model=Location
        exclude = ['location_id','history','created_at','updated_at','user']



class UpdateLocationForm(forms.ModelForm):
    address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 3, 
                'style': 'height: 30px;', 
            }
        )
    )
    class Meta:
        model=Location
        exclude = ['location_id','history','created_at','updated_at','user']




class SupplierPerformanceForm(forms.ModelForm):
    feedback = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 3,
                'style': 'height: 40px;', 
            }
        )
    )
    class Meta:
        model = SupplierPerformance
        exclude = ['user','created_at','updated_at','history']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),            
        }
