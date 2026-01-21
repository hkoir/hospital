from django import forms
from .models import Patient
from facilities.models import BedAssignmentHistory,Bed,Room
from .models import PatientAdmission,DischargeReport






class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'referral_source', 'patient_id', 'user', 'guardian', 'name', 'email', 'phone',
            'date_of_birth', 'gender', 'address', 'emergency_contact', 'medical_history', 'patient_photo'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medical_history': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Select, forms.DateInput, forms.Textarea)):
                field.widget.attrs.update({'class': 'form-control'})

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
        exclude =['status','discharge_date','discharge_approved','admission_date','admission_code','invoice','bed_assignment_date']

        widgets={
            'reason_for_admission':forms.Textarea(attrs={
                'class':'form-control',
                'row':3,
                'style':'height:50px'

                }),
            'assigned_ward': forms.Select(attrs={'id': 'ward', 'class': 'form-select'}),
            'assigned_room': forms.Select(attrs={'id': 'room', 'class': 'form-select'}),
            'assigned_bed': forms.Select(attrs={'id': 'bed', 'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_ward'].queryset = Ward.objects.filter(ward_rooms__is_occupied=False).distinct()

        if 'assigned_ward' in self.data:
            try:
                ward_id = int(self.data.get('assigned_ward'))
                self.fields['assigned_room'].queryset = Room.objects.filter(ward_id=ward_id)
            except (ValueError, TypeError):
                self.fields['assigned_room'].queryset = Room.objects.none()
        else:
            self.fields['assigned_room'].queryset = Room.objects.none()

        if 'assigned_room' in self.data:
            try:
                room_id = int(self.data.get('assigned_room'))
                self.fields['assigned_bed'].queryset = Bed.objects.filter(room_id=room_id, is_occupied=False)
            except (ValueError, TypeError):
                self.fields['assigned_bed'].queryset = Bed.objects.none()
        else:
            self.fields['assigned_bed'].queryset = Bed.objects.none()



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
        exclude = ['patient_admission','patient_emergency','doctor','invoice','created_at']
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
             'follow_up_date':forms.DateInput(attrs={'type':'date'})


        }



