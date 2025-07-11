from django.db import models
from django_tenants.models import TenantMixin, DomainMixin
from django.contrib.auth.models import AbstractUser,User
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.utils.timezone import now



app_name='clients'



class Client(TenantMixin):
    name = models.CharField(max_length=100) 
    registered_tenant = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass


  
class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        (1, '30 days free trial'),
        (6, '6 Months'),
        (12, '1 Year'),
        (24, '2 Years'),
        (36, '3 Years'),
        (48, '4 Years'),
        (60, '5 Years'),
    ]

    duration = models.PositiveIntegerField(choices=DURATION_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    base_users = models.PositiveIntegerField(default=5)  
    price_per_user = models.DecimalField(max_digits=40, decimal_places=2, blank=True, null=True)
    price_per_request = models.DecimalField(max_digits=40, decimal_places=4, blank=True, null=True)    
    description = models.TextField(blank=True, null=True)  
    features = models.TextField()  

    def calculate_total_cost(self, total_users):   
        extra_users = max(0, total_users - self.base_users)  
        extra_cost = extra_users * (self.price_per_user or 0) * (self.duration // 12)  
        return self.price + extra_cost  

    def __str__(self):
        return f"{self.get_duration_display()} - ${self.price}"



class Tenant(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True, related_name='tenant_user')
    tenant = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='tenant', null=True, blank=True)  # Maps to Client
    name = models.CharField(max_length=100)
    max_users = models.PositiveIntegerField(default=5) 
    subdomain = models.CharField(max_length=100, unique=True,help_text='subdomain could be your company name or any name you prefer')  
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='tenant_lgo',blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True) 
    is_trial_used = models.BooleanField(default=False) 
    created_on = models.DateTimeField(auto_now_add=True)  
    updated_on = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.name} ({self.subdomain})"



from dateutil.relativedelta import relativedelta

class Subscription(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='subscription')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField(auto_now_add=True)
    expiration_date = models.DateField(null=True, blank=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)  
    is_renewal = models.BooleanField(default=False) 
    is_expired = models.BooleanField(default=False) 
    is_trial = models.BooleanField(default=False) 
    status_choices = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='active')
    approved_on = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)  
    updated_on = models.DateTimeField(auto_now=True)  

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            self.is_expired = self.expiration_date < timezone.now().date()

        if not self.next_billing_date:
            self.next_billing_date = now() + relativedelta(months=self.subscription_plan.duration)
        super().save(*args, **kwargs)



    def renew_subscription(self, new_plan):
        self.subscription_plan = new_plan
        self.start_date = timezone.now().date()
        self.expiration_date = timezone.now().date() + timedelta(days=new_plan.duration * 30)  # Assuming 30 days per month
        self.status = 'active'
        self.save()

    def has_expired(self):
        return self.next_billing_date and self.next_billing_date < now()
    
    def check_trial(self):
        return self.subscription_plan and self.subscription_plan.duration == 1  


    def __str__(self):
        return f"{self.tenant} - {self.subscription_plan} - Next Billing: {self.next_billing_date}"

    class Meta:
        ordering = ['-created_on']



class UserRequestLog(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=now)
    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"


class BillingRecord(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    billing_date = models.DateField(default=timezone.now)
    total_users = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)  
    updated_on = models.DateTimeField(auto_now=True) 



class TenantInfo(models.Model):
    name = models.CharField(max_length=100)
    content = models.TextField() 
    def __str__(self):
        return self.name



class PaymentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_profile")
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="tenant_payment_profile",blank=True, null=True)
    payment_token = models.CharField(max_length=255, unique=True)  # Token from payment gateway
    card_last4 = models.CharField(max_length=4, blank=True, null=True)  # Last 4 digits
    card_brand = models.CharField(max_length=50,
                                  
    choices=[
        ('VISA','Visa'),
        ('MASTER-CARD','Master card'),
         ('AMEX','American Express')
        ], blank=True, null=True)  
    
    cvv=models.CharField(max_length=3,null=True,blank=True)
    expiry_date = models.CharField(max_length=5, blank=True, null=True) 
    
    card_expiry_month = models.IntegerField(blank=True, null=True)  # Expiry month
    card_expiry_year = models.IntegerField(blank=True, null=True)  # Expiry year



class DemoRequest(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    company = models.CharField(max_length=255, blank=True, null=True) 
    job_title = models.CharField(max_length=255, blank=True, null=True)  
    company_size = models.CharField(max_length=255, blank=True, null=True)  
    phone_number = models.CharField(max_length=20, blank=True, null=True)  
    message = models.TextField(blank=True, null=True)  
    requested_at = models.DateTimeField(auto_now_add=True) 
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),  
    ], default='pending')    

    assigned_to = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='demo_requests') # Assign to sales rep
    created_on = models.DateTimeField(auto_now_add=True)  
    updated_on = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.name} - {self.email}"

    class Meta:
        verbose_name = "Demo Request"
        verbose_name_plural = "Demo Requests"
        ordering = ['-requested_at']  










class TenantSMSConfig(models.Model):
    tenant = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="sms_config")
    provider_name = models.CharField(max_length=100,blank=True, null=True) 
    api_key = models.CharField(max_length=255,blank=True, null=True)
    api_url = models.URLField(blank=True, null=True) 
    sender_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.provider_name} config for {self.tenant.name}"



class GlobalSMSConfig(models.Model):
    provider_name = models.CharField(max_length=100,blank=True, null=True)
    api_key = models.CharField(max_length=255,blank=True, null=True)
    api_url = models.URLField(blank=True, null=True)
    sender_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Global SMS config ({self.provider_name})"
