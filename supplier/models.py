
from django.db import models
from core.models import Location
import uuid
from simple_history.models import HistoricalRecords
from django.contrib.auth.models import User
from django.apps import apps
from accounts.models import CustomUser


class Supplier(models.Model):
    name = models.CharField(max_length=255,null=True, blank=True)
    logo = models.ImageField(upload_to='company_logo/',blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='supplier_user')
    supplier_id = models.CharField(max_length=150, null=True, blank=True)
    contact_person = models.CharField(max_length=255,null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    
    def save(self, *args, **kwargs):
        if not self.supplier_id:
            self.supplier_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Location(models.Model):
    supplier = models.ForeignKey(Supplier, related_name='supplier_locations', on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=255,null=True, blank=True)   
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='supplier_location_user')
    location_id = models.CharField(max_length=150, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100,null=True, blank=True)
    state = models.CharField(max_length=100,null=True, blank=True)
    country = models.CharField(max_length=100,null=True, blank=True)
    postal_code = models.CharField(max_length=20,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 

    def save(self, *args, **kwargs):
        if not self.location_id:
            self.location_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.city}, {self.state}, {self.country})"



class SupplierPerformance(models.Model):
    purchase_order = models.ForeignKey('purchase.PurchaseOrder', related_name='sale_transaction_inv', null=True, blank=True, on_delete=models.CASCADE)   
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE,related_name='supplier_performance',null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='supplier_performance_location_purchases', null=True, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='supplier_performance_user')
    date = models.DateField(null=True, blank=True)    
    total_value = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    delivery_rating= models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], blank=True, null=True)  # 1 to 5 rating
    quality_rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], blank=True, null=True)  # 1 to 5 rating
    on_time_delivery = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], blank=True, null=True)  # 1 to 5 rating
    feedback = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def get_purchase_order(self):
        PurchaseOrder = apps.get_model('purchase', 'PurchaseOrder')
        return PurchaseOrder.objects.get(id=self.purchase_order.id) if self.purchase_order.id else None
  


    def __str__(self):
        return f"supplier name:{self.supplier.name} Purchase Order={self.purchase_order}"
