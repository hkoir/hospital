from django import forms
from .models import Patient
from facilities.models import BedAssignmentHistory,Bed,Room
from .models import PatientAdmission,DischargeReport





class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = '__all__'


class DirectPatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        exclude=['patient_id','user','guardian','email']
        widgets={
            'address':forms.Textarea(attrs={
                'class':'form-control','style':'height:60px'
            }),
               'medical_history':forms.Textarea(attrs={
                'class':'form-control','style':'height:60px'
            })
        }



from facilities.models import Ward

class PatientAdmissionForm(forms.ModelForm):
    class Meta:
        model = PatientAdmission
        exclude =['status','discharge_date','admission_date','admission_code','invoice','bed_assignment_date']

        widgets={
            'reason_for_admission':forms.Textarea(attrs={
                'class':'form-control',
                'row':3,
                'style':'height:50px'
               
                })
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.fields['assigned_bed'].queryset = Bed.objects.filter(is_occupied=False)
        self.fields['assigned_room'].queryset = Room.objects.filter(is_occupied=False)
        self.fields['assigned_ward'].queryset = Ward.objects.filter(is_occupied=False)

    def clean_assigned_bed(self):
        bed = self.cleaned_data.get('assigned_bed')
        if bed and bed.is_occupied:
            raise forms.ValidationError("This bed is already occupied. Please choose another.")
        return bed
    def clean_assigned_room(self):
        room = self.cleaned_data.get('assigned_room')
        if room and room.is_occupied:
            raise forms.ValidationError("This room is already full. Please select another.")
        return room

    def clean_assigned_ward(self):
        ward = self.cleaned_data.get('assigned_ward')
        if ward and ward.is_occupied:
            raise forms.ValidationError("This ward is currently full. Please select another.")
        return ward





class BedAssignmentForm(forms.Form):
    bed = forms.ModelChoiceField(
        queryset=Bed.objects.filter(is_occupied=False),
        label="Select an available bed",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_occupied=False),
        required=False,
        label="Select an available room",
        widget=forms.Select(attrs={'class': 'form-control'})
    )




class DischargeReportForm(forms.ModelForm):
    class Meta:
        model = DischargeReport
        fields = ['summary', 'diagnosis', 'treatment_given', 'follow_up_instructions', 'additional_notes']
        widgets={
            'summary':forms.Textarea(attrs={
                'row':6,
                'style':'height:200px'
            }),

            'diagnosis':forms.Textarea(attrs={
                'row':6,
                'style':'height:200px'
            }),
            
            'treatment_given':forms.Textarea(attrs={
                'row':6,
                'style':'height:200px'
            }),
            
              'follow_up_instructions':forms.Textarea(attrs={
                'row':6,
                'style':'height:200px'
            }),
               'additional_notes':forms.Textarea(attrs={
                'row':6,
                'style':'height:200px'
            }),
            
            
        }
