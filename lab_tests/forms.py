from django import forms

from .models import LabTestResult, LabTestResultOrder,LabTest,LabTestCatalog
from django.forms import modelformset_factory
from django.core.validators import MaxLengthValidator




        
class LabTestForm(forms.Form):
    lab_tests = forms.ModelMultipleChoiceField(
        queryset=LabTestCatalog.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Lab Tests"
    )





class LabTestResultOrderForm(forms.ModelForm):
    class Meta:
        model = LabTestResultOrder
        exclude = ['recorded_at', 'updated_at','status','lab_test_result_oder_code']
        widgets = {
           'summary_report': forms.Textarea(attrs={'rows': 6, 'style': 'width: 100%;'})
          
        }





class LabTestResultForm(forms.ModelForm):
    class Meta:
        model = LabTestResult
        exclude = ['result_order', 'recorded_at', 'updated_at','remarks','status','patient_type']
        widgets = {           
             'findings': forms.Textarea(attrs={
                  'rows': 5, 
                  'style': 'width: 100%;',
                  'maxlength': 100,
                  'placeholder': 'Max 100 characters'
                 })
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['findings'].validators.append(MaxLengthValidator(150))

LabTestResultFormSet = modelformset_factory(
    LabTestResult, form=LabTestResultForm, extra=1, can_delete=True
)




from medical_records.models import MedicalRecord

class LabTestFilter(forms.Form):
   medical_record= forms.ModelChoiceField(
        queryset=MedicalRecord.objects.all(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_medical_record','class':'form-control'}),
    )






   #=================== externl lab test ====================================

from .models import ExternalLabVisit
from patients.models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__' # adjust fields



class ExternalLabVisitForm(forms.ModelForm):
    class Meta:
        model = ExternalLabVisit
        exclude = ['status','medical_record','invoice']
        widgets = {
            'lab_tests': forms.CheckboxSelectMultiple,
            'notes':forms.Textarea(attrs={
                'style':'height:60px'
            })
        }

