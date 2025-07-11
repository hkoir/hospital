from django import forms
from .models import Doctor
from django import forms
from .models import AppointmentSlot, Doctor




class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ["name", "specialization", "start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }





class TimeSlotForm(forms.Form):
    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all(), label="Select Doctor")
    slot_duration = forms.IntegerField(label="Slot Duration (minutes)", min_value=5, max_value=120)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Start Date")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="End Date")




class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = AppointmentSlot  # Ensure this corresponds to the model you're working with
        fields = ['doctor', 'slot_duration', 'start_date', 'end_date']  # List the fields you want to include

    doctor = forms.ModelChoiceField(queryset=Doctor.objects.all(), label="Select Doctor")
    slot_duration = forms.IntegerField(label="Slot Duration (minutes)", min_value=5, max_value=120)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="Start Date")
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label="End Date")
