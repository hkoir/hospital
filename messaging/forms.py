from django import forms
from.models import ManagementMessage



class ManagementMessageForm(forms.ModelForm):
    class Meta:
        model = ManagementMessage
        exclude=['user']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'columns': 6,
                'placeholder': 'Enter your message here'
            })
        }
