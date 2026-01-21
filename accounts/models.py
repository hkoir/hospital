from django.contrib.auth.models import User
from django.db import models

from clients.models import Client
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from core.utils import DEPARTMENT_CHOICES,POSITION_CHOICES



class CustomUser(AbstractUser):
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='users', null=True, blank=True)   
  
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('parent', 'Parent'),
        ('staff', 'Staff'),
        ('superadmin', 'SuperAdmin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('nurse', 'Nurse'),
        ('engineer', 'Engineer'),
        ('general', 'General'),
    ]

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='General')
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='users', null=True, blank=True)

    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True, null=True, unique=False)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)   

    is_active = models.BooleanField(default=True)
    user_department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, null=True, blank=True)
    user_position = models.CharField(max_length=100, choices=POSITION_CHOICES, null=True, blank=True)

    photo_id = models.ImageField(upload_to='user_photo', null=True, blank=True)
    def __str__(self):
        return f"{self.username} - {self.tenant.name if self.tenant else 'No Tenant'}"
    




import random
from django.utils import timezone
from datetime import timedelta

PURPOSE_CHOICES = [
    ('registration', 'Registration'),
    ('forgot_password', 'Forgot Password'),
    ('change_password', 'Change Password'),
]

class PhoneOTP(models.Model):
    phone_number = models.CharField(max_length=20)
    otp = models.CharField(max_length=6)
    valid_until = models.DateTimeField() 
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='registration')

    def save(self, *args, **kwargs):     
        if not self.valid_until:
            self.valid_until = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.valid_until = timezone.now() + timedelta(minutes=5)
        self.save()

    def is_valid(self):
        return timezone.now() <= self.valid_until and not self.is_verified

    

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='user_profile', null=True, blank=True)
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='user_tenants', null=True, blank=True)

    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    



class AllowedEmailDomain(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='allowed_user_email_domains', null=True, blank=True)
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='allowed_user_tenant_domains',null=True, blank=True)
    domain = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)  
    updated_on = models.DateTimeField(auto_now=True)  

    class Meta:
        unique_together = ('tenant', 'domain')  

    def __str__(self):
        return f"{self.domain} ({self.tenant.name})"


