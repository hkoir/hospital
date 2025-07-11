from django import forms
from .models import LeaveApplication,LeaveType,AttendanceLog,AttendanceModel,LatePolicy
from datetime import timedelta


import datetime

class AttendancePolicyForm(forms.ModelForm):
    WEEKDAY_CHOICES = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]
    weekened = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,  # Checkboxes for selection
        required=False
    )
   
    class Meta:
        model = LatePolicy
        exclude=['policy_id']
        widgets={
            'max_check_in_time':forms.TimeInput(attrs={'type':'time'}) ,
          
        }
   

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].required = False 
            
        if self.instance and self.instance.weekened:
            self.fields['weekened'].initial = self.instance.get_weekends_list()

    def clean_weekened(self):
        """Convert selected weekdays into a comma-separated string before saving."""
        return ','.join(self.cleaned_data['weekened'])
     
       

 
        





class AttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceModel
        exclude=['total_hours','user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)      
        self.fields['date'].widget = forms.DateInput(attrs={'type':'date'})   
        self.fields['check_in_time'].widget = forms.TimeInput(attrs={'type':'time'})   
        self.fields['check_out_time'].widget = forms.TimeInput(attrs={'type':'time'})   
        



class EditAttendanceForm(forms.ModelForm):
    class Meta:
        model = AttendanceModel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)      
        self.fields['date'].widget = forms.DateInput(attrs={'type':'date'})   
        self.fields['check_in_time'].widget = forms.TimeInput(attrs={'type':'time'})   
        self.fields['check_out_time'].widget = forms.TimeInput(attrs={'type':'time'})   
        
class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        exclude=['accrual_rate']

        widgets = {           
        'description':forms.Textarea(attrs={
            'class':'form-control',
            'row':2,
            'style':'height:50px'
        })
        }


class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['leave_type', 'applied_start_date', 'applied_end_date', 'applied_reason', 'attachment']
        widgets = {
            'applied_start_date': forms.DateInput(attrs={'type': 'date'}),
            'applied_end_date': forms.DateInput(attrs={'type': 'date'}),
            'applied_reason':forms.Textarea(attrs={
                'class':'form-control',
                'row':2,
                'style':'height:50px'
            })
        }


class ApprovalForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['leave_type', 'approved_start_date', 'approved_end_date','status','rejection_reason']
        widgets = {
            'approved_start_date': forms.DateInput(attrs={'type': 'date'}),
            'approved_end_date': forms.DateInput(attrs={'type': 'date'}),
            'rejection_reason':forms.Textarea(attrs={
                'class':'form-control',
                'row':2,
                'style':'height:50px'
            })
        }


from.models import Shift
class ShiftForm(forms.ModelForm):
    class Meta:
        model=Shift
        fields='__all__'
        widgets={
            'start_time':forms.TimeInput(attrs={'type':'time'}),
            'end_time':forms.TimeInput(attrs={'type':'time'})
        }