from django import forms
from .models import MedicalRecord,Prescription

from django.forms import formset_factory
from django import forms
from core.models import Doctor
from patients.models import Patient
from medical_records.models import PrescribedMedicine



class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ["diagnosis", "treatment_plan"]
        widgets = {
            "diagnosis": forms.Textarea(attrs={"rows": 6,'style':'width:100%', "placeholder": "diagnosis..."}),           
            "treatment_plan": forms.Textarea(attrs={"rows": 6,'style':'width:100%', "placeholder": "Treatment plan..."}),
        }

from .models import MedicalRecordProgress

class MedicalRecordProgressForm(forms.ModelForm):
    class Meta:
        model = MedicalRecordProgress
        fields = ['diagnosis', 'treatment_plan', 'remarks']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 4}),
            'treatment_plan': forms.Textarea(attrs={'rows': 4}),
            'remarks': forms.Textarea(attrs={'rows': 4}),
        }



class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = PrescribedMedicine
        exclude=['prescription','medication_category','UOM','quantity','prescription_id','appointment','patient_type']
        widgets = {
            "medication_type": forms.Select(),
            "dosage_schedule": forms.Select(),
            'dosage':forms.TextInput(attrs={
                'class':'form-control','placeholder':'example,250ml,300mg, 1tablet, 1.5 table, 1 capsule etc.'
            }),
            'medication_duration':forms.NumberInput(attrs={
                'class':'form-control','placeholder':'Enter no of days'
            }),
            "additional_instructions": forms.Textarea(attrs={"rows": 2, "placeholder": "e.g.exercise, bed rest, follow up, food etc..."}),
            "appointment": forms.Select(attrs={
                'class':'form-control'
            }),

            'medication_name': forms.Select(attrs={
                'class': 'form-control medication-name-select',
                'data-placeholder': 'Search medicine...',
                
                
            })
          
        }



PrescriptionFormSet = formset_factory(PrescriptionForm, extra=1)

class MedicalRecordFilter(forms.Form):
    doctor= forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        required=False,
        widget=forms.Select(attrs=
        {'id': 'id_doctor',
         'class':'form-control',
        
         }),
    )
   
    patient= forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        required=False,
        widget=forms.Select(attrs=
        {'id': 'id_patient',
         'class':'form-control',
         
         }),
                           
    )

    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
