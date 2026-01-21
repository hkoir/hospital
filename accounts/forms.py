
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.conf import settings

import pkg_resources
from django.contrib.auth.models import User, Permission
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import (AuthenticationForm, PasswordResetForm,SetPasswordForm)
from.models import UserProfile,Client

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from.models import CustomUser



class PublicUserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email") # Add profile picture field



class PublicUserLoginForm(AuthenticationForm):
    pass  




class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'tenant']

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance').user if 'instance' in kwargs else None
        if user:    
            tenant = user.user_profile.tenant if user.user_profile else None
            kwargs['initial'] = kwargs.get('initial', {})
            kwargs['initial']['tenant'] = tenant
        super(UserProfileForm, self).__init__(*args, **kwargs)



class CustomLoginForm2(AuthenticationForm):
    tenant = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tenant'}),
        label="Tenant",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # This ensures username & password are set correctly
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})


class CustomLoginForm(AuthenticationForm):
    tenant = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tenant'}),
        label="Tenant",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Phone, Email, or Username"
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Phone, Email, or Username'
        })

        self.fields['password'].label = "Password"
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })



from.models import CustomUser

class TenantUserRegistrationForm2(UserCreationForm):
    profile_picture = forms.ImageField(required=False)
    
    class Meta:
        model = CustomUser
        fields = ['role','username', 'email', 'password1', 'password2', 'profile_picture']  

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)  # Store tenant in the form instance
        super().__init__(*args, **kwargs)

        # Optional Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        return user



class TenantUserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(required=False)
        
    class Meta:
        model = CustomUser
        fields = ['role','username', 'email', 'phone_number','password1', 'password2', 'photo_id']  

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)  # Store tenant in the form instance
        super().__init__(*args, **kwargs)

        # Optional Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        return user
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("Phone number already exists.")
        return phone



    
class PartnerJobSeekerRegistrationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False)
    user_type = forms.ChoiceField(
        choices=[
            ('register-as_business-parner', 'Register as business partners'),
            ('register-as-job-seeker', 'Register as job seeker')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['user_type', 'username', 'email', 'password1', 'password2', 'profile_picture']  # ❌ Removed 'tenant'

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)  # Store tenant in the form instance
        super().__init__(*args, **kwargs)

        # Optional Bootstrap classes
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        return user


class PublicRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'photo_id', 'tenant']

    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)  
        super().__init__(*args, **kwargs)
    
        if self.tenant:
           
            self.fields['tenant'].initial = self.tenant  
            self.fields['tenant'].widget = forms.HiddenInput()  

            self.fields['tenant_name'] = forms.CharField(
                initial=self.tenant.name, 
                required=False, 
                widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'})
            )

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.tenant:
            user.tenant = self.tenant 
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user



class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class CustomUserCreationForm(UserCreationForm):
    address = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=20, required=False)
    country = forms.CharField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    profile_picture = forms.ImageField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'address', 'city', 'state', 'postal_code', 'country', 'phone_number','profile_picture']


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']




class PwdResetForm(PasswordResetForm):
    email = forms.EmailField(max_length=254, widget=forms.TextInput(
        attrs={'class': 'form-control mb-3', 'placeholder': 'Email', 'id': 'form-email'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        u = CustomUser.objects.filter(email=email)
        if not u:
            raise forms.ValidationError(
                'Unfortunatley we can not find that email address')
        return email



class PwdResetConfirmForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='New password', widget=forms.PasswordInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'New Password', 'id': 'form-newpass'}))
    new_password2 = forms.CharField(
        label='Repeat password', widget=forms.PasswordInput(
            attrs={'class': 'form-control mb-3', 'placeholder': 'New Password', 'id': 'form-new-pass2'}))




MODEL_CHOICES = [
    ('purchase.PurchaseRequestOrder', 'Purchase Request Order'),
    ('purchase.PurchaseOrder', 'Purchase Order'),
    ('sales.SaleRequestOrder', 'Sales Request Order'),    
    ('sales.SaleOrder', 'Sales Order'),   
    ('manufacture.MaterialsRequestOrder', 'Production Materials Request Order'),  
    ('officemanagement.StationaryPurchaseOrder', 'Stationary Purchase Order'), 
]


class AssignPermissionsForm(forms.Form):       
    model_name = forms.ChoiceField(
        choices=MODEL_CHOICES,  
        label="Select Model"
    )
    # user = forms.ModelChoiceField(queryset=User.objects.all(), label="Select User",required=False)
    email = forms.EmailField(label="Enter User's Email Address")
    permissions = forms.MultipleChoiceField(
        choices=
        [
        ('can_request', 'Can Request'),
        ('can_review', 'Can Review'),
        ('can_approve', 'Can Approve')
        ],
        widget=forms.CheckboxSelectMultiple,
        label="Assign Permissions"
    )

    def clean(self):
        cleaned_data = super().clean()
        model_name = cleaned_data.get('model_name')
        permission_codename = cleaned_data.get('permission_codename')

        if model_name and permission_codename:
            app_label, model_label = model_name.split('.')
            model = apps.get_model(app_label, model_label)            

            try:
                content_type = ContentType.objects.get_for_model(model)
                permission = Permission.objects.get(codename=permission_codename, content_type=content_type)
            except Permission.DoesNotExist:
                raise forms.ValidationError(f"Permission '{permission_codename}' does not exist for the selected model.")
            
        return cleaned_data



class UserGroupForm(forms.Form):
    username = forms.CharField(max_length=100, label="Username")
    email = forms.EmailField(label="Enter User's Email Address")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), label="Select Group", required=False)
    new_group_name = forms.CharField(max_length=100, label="New Group Name", required=False)

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get("group")
        new_group_name = cleaned_data.get("new_group_name")

        if not group and not new_group_name:
            raise forms.ValidationError("You must either select an existing group or provide a new group name.")
        
        return cleaned_data



class AssignPermissionsToGroupForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.all(), label="Select Group")
    model_name = forms.ChoiceField(choices=MODEL_CHOICES, label="Select Model", widget=forms.Select(attrs={'id': 'model-select'}))

    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),  # Initially empty until model is selected
        widget=forms.CheckboxSelectMultiple(attrs={'id': 'permissions-select'}),
        label="Select Permissions",
        required=False
    )

    def __init__(self, *args, **kwargs):
        model_name = kwargs.get('initial', {}).get('model_name', None)
        super().__init__(*args, **kwargs)
        if model_name:
            model_class = apps.get_model(*model_name.split('.'))
            content_type = ContentType.objects.get_for_model(model_class)
            self.fields['permissions'].queryset = Permission.objects.filter(content_type=content_type)


