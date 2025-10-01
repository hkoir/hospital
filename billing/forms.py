
from django import forms
from facilities.models import OTBooking
from .models import MedicineBill,MiscellaneousBill,OTBill,WardBill,EmergencyVisit
from .models import ConsultationBill,LabTestBill,BillingInvoice,Payment,DoctorServiceRate


class ConsultationBillForm(forms.ModelForm):
    class Meta:
        model = ConsultationBill
        exclude = ['status']


class LabTestBillForm(forms.ModelForm):
    class Meta:
        model = LabTestBill
        exclude = ['status','invoice']



class BillingInvoiceForm(forms.ModelForm):
    class Meta:
        model = BillingInvoice
        exclude = ['status','invoice_id','invoice_type']  # Add other editable fields if needed




class WardBillForm(forms.ModelForm):
    class Meta:
        model = WardBill
        fields = ['ward', 'bed', 'room', 'patient_admission']
        widgets = {
            'ward': forms.Select(attrs={'class': 'form-control'}),
            'bed': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'patient_admission': forms.Select(attrs={'class': 'form-control'}),
        }

   
    



class MedicineBillForm(forms.ModelForm):
    class Meta:
        model = MedicineBill
        fields = ['patient_type','medicine', 'quantity', 'price_per_unit']
        widgets = {
            'medicine': forms.Select(attrs={
                'class': 'form-control medicine-name-select',
                'id': 'id_medicine',   # will be prefixed by formset
            }),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'id': 'id_price_per_unit',  # will be prefixed

            }),

           
        }



class MiscBillForm(forms.ModelForm):
    class Meta:
        model = MiscellaneousBill
        fields = ['service_name', 'amount']
        widgets = {
            'service_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }




class OTBookingForm(forms.ModelForm):
    procedure = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = OTBooking
        fields = ['operation_theatre', 'patient', 'surgeon', 'booked_start', 'booked_end', 'procedure','surgery_type','notes']
        widgets = {
            'operation_theatre': forms.Select(attrs={'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'surgeon': forms.Select(attrs={'class': 'form-control'}),
            'booked_start': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'booked_end': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
               'style':'height:30px; width:100%'
                }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  
        raw_types = DoctorServiceRate.objects.values_list('service_type', flat=True)
        unique_normalized = {}
        
        for stype in raw_types:
            if stype:
                normalized = stype.strip().lower()
                if normalized not in unique_normalized:
                    unique_normalized[normalized] = stype.strip()

        # Set deduplicated and clean choices
        self.fields['procedure'].choices = [
            (val, val) for val in unique_normalized.values()
        ]



    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('booked_start')
        end = cleaned_data.get('booked_end')
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data





class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount_paid', 'payment_method', 'payment_type', 'remarks']
        widgets = {
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'invoice': forms.Select(attrs={'class': 'form-control'}),
            'patient_type': forms.Select(attrs={'class': 'form-control'}),
        }



        
from.models import DoctorPayment

class DoctorPaymentForm(forms.ModelForm):
    class Meta:
        model = DoctorPayment
        fields = ['total_paid_amount','payment_method','remarks']
        widgets = {
            'Total_paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),          
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
           
        }



class CommonFilterForm(forms.Form):
    INVOICE_TYPE = [
         ('', ''),
        ('OPD', 'Outpatient'),
        ('IPD', 'Inpatient'),
        ('Emergency', 'Emergency'),
        ('External-Lab-Test', 'External Lab test'),
    ]
    entity_id = forms.CharField(required=False)
    phone_number = forms.CharField(required=False)
    email = forms.CharField(required=False)
    name = forms.CharField(required=False)
    patient_id = forms.CharField(required=False)
    service_type = forms.ChoiceField(choices=INVOICE_TYPE,required=False)




class EmergencyVisitForm(forms.ModelForm):
    class Meta:
        model = EmergencyVisit
        fields = ['patient', 'chief_complaint', 'triage_level', 'treated_by']
        widgets = {
            'chief_complaint': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'triage_level': forms.Select(attrs={'class': 'form-control'}),
            'treated_by': forms.Select(attrs={'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
        }



from .models import DoctorServiceRate

class DoctorServiceRateForm(forms.ModelForm):
    class Meta:
        model = DoctorServiceRate
        fields = ['doctor', 'service_type', 'rate']
        widgets = {
            'service_type': forms.Select(attrs={'class': 'form-select'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
        }
