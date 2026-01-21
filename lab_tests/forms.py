from django import forms

from .models import LabTestResult, LabTestResultOrder,LabTest,LabTestCatalog
from django.forms import modelformset_factory
from django.core.validators import MaxLengthValidator


from .models import LabTestCategory,LabTestCatalog


class LabtestCategoryForm(forms.ModelForm):
    class Meta:
        model = LabTestCategory
        fields = [ 'name', 'service_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3,'style':'height:40px',"class": "form-control w-100"}),
        }

class LabtestCatelogueForm(forms.ModelForm):
    class Meta:
        model = LabTestCatalog
        fields = ['category', 'test_name', 'price','description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3,'style':'height:40px',"class": "form-control w-100"}),
            
        }



        
class LabTestForm(forms.Form):
    lab_tests = forms.ModelMultipleChoiceField(
        queryset=LabTestCatalog.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Lab Tests"
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lab_tests'].queryset = LabTestCatalog.objects.all()


from .models import LabSampleCollection

class LabSampleCollectionForm(forms.ModelForm):
    class Meta:
        model = LabSampleCollection
        fields = ['sample_type', 'notes']
        widgets = {           
             'notes': forms.Textarea(attrs={
                  'rows': 3, 
                  'style': 'width: 100%; height:50px',             

                 }),
		 'sample_type': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
    


class LabTestResultOrderForm(forms.ModelForm):
    class Meta:
        model = LabTestResultOrder
        exclude = ['recorded_at', 'updated_at','status','lab_test_result_oder_code','qr_code']
        widgets = {
           'summary_report': forms.Textarea(attrs={'rows': 6, 'style': 'width: 100%;'})

        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)      
        self.fields['medical_record'].widget.attrs['readonly'] = True
        self.fields['lab_test_request'].widget.attrs['readonly'] = True






class LabTestResultForm(forms.ModelForm):
    class Meta:
        model = LabTestResult
        exclude = ['result_order','prescription', 'recorded_at', 'updated_at','remarks','status','patient_type']
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
        exclude = ['status','medical_record','invoice','lab_test_request']
        widgets = {
            'lab_tests': forms.CheckboxSelectMultiple,
            'notes':forms.Textarea(attrs={
                'style':'height:60px'
            })
        }

