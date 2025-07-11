from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Tenant,Subscription

from django import forms
from .models import DemoRequest




class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = ['name', 'email', 'company', 'job_title', 'company_size', 'phone_number', 'message']  
        widgets={
            'message':forms.Textarea(attrs={
                'class':'form-control',
                'row':2,
                'style':'height:100px'
            })
        }


class TenantApplicationForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'subdomain','email','phone_number', 'address','logo']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
           
        }




import re
from datetime import datetime

class CreditCardPaymentForm(forms.Form):
    CARD_BRAND_CHOICES = [
        ('Visa', 'Visa'),
        ('MasterCard', 'MasterCard'),
        ('Amex', 'American Express'),
        ('Discover', 'Discover'),
    ]

    card_number = forms.CharField(
        max_length=19,  # Allow for different card lengths
        label="Card Number",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your card number', 'class': 'form-control'}),
    )
    
    expiry_date = forms.CharField(
        max_length=5,
        label="Expiry Date (MM/YY)",
        widget=forms.TextInput(attrs={'placeholder': 'MM/YY', 'class': 'form-control'}),
    )

    cvv = forms.CharField(
        max_length=4,  # Allow 4 digits for Amex
        label="CVV",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter CVV', 'class': 'form-control'}),
    )

    card_brand = forms.ChoiceField(
        choices=CARD_BRAND_CHOICES,
        label="Card Brand",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number'].replace(" ", "")  # Remove spaces
        if not card_number.isdigit() or not (13 <= len(card_number) <= 19):
            raise forms.ValidationError("Invalid card number. Must be 13-19 digits.")
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data['expiry_date'].strip()
        if not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", expiry_date):
            raise forms.ValidationError("Invalid expiry date format. Use MM/YY.")

        month, year = map(int, expiry_date.split('/'))
        current_year = int(datetime.now().strftime("%y"))
        current_month = int(datetime.now().strftime("%m"))

        if year < current_year or (year == current_year and month < current_month):
            raise forms.ValidationError("Card has expired.")

        return expiry_date

    def clean_cvv(self):
        cvv = self.cleaned_data['cvv'].strip()
        card_brand = self.cleaned_data.get('card_brand')

        if not cvv.isdigit():
            raise forms.ValidationError("Invalid CVV. Must be numeric.")

        if card_brand == 'Amex' and len(cvv) != 4:
            raise forms.ValidationError("American Express CVV must be 4 digits.")
        elif card_brand != 'Amex' and len(cvv) != 3:
            raise forms.ValidationError("CVV must be 3 digits.")

        return cvv
