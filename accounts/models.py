from django.contrib.auth.models import User
from django.db import models

from clients.models import Client
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from core.utils import DEPARTMENT_CHOICES,POSITION_CHOICES



class CustomUser(AbstractUser):
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='users', null=True, blank=True)   
  
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
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

    user_department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, null=True, blank=True)
    user_position = models.CharField(max_length=100, choices=POSITION_CHOICES, null=True, blank=True)

    photo_id = models.ImageField(upload_to='user_photo', null=True, blank=True)
    def __str__(self):
        return f"{self.username} - {self.tenant.name if self.tenant else 'No Tenant'}"
    
    

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


