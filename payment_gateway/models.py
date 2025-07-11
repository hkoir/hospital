from django.db import models

from clients.models import Client



class PaymentSystem(models.Model):
    PAYMENT_METHODS = (
        ('bKash', 'bKash'),
        ('Rocket', 'Rocket'),
        ('CreditCard', 'CreditCard'),
        ('PayPal', 'PayPal'),
        
    )    
    method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    name = models.CharField(max_length=255)  
    base_url = models.URLField(blank=True, null=True)
  

    def __str__(self):
        return self.name
    


class TenantPaymentConfig(models.Model):
    tenant = models.OneToOneField(Client, on_delete=models.CASCADE)
    payment_system = models.ForeignKey(PaymentSystem, on_delete=models.CASCADE)    
    api_key = models.CharField(max_length=255, blank=True, null=True) 
    merchant_id = models.CharField(max_length=255, blank=True, null=True)
    payment_redirect_url = models.URLField(blank=True, null=True)
    client_id = models.CharField(max_length=255, blank=True, null=True)  
    client_secret = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"Payment config for {self.tenant.name} using {self.payment_system.name}"




