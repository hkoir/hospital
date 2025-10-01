from django.db import models
from django.utils import timezone
from.utils import MEDICINE_CATEGORY_CHOICES

from accounts.models import CustomUser
import uuid

from medical_records.models import MedicalRecord
from core.models import Doctor
from django.utils.translation import gettext_lazy as _

from product.models import Product,Category,Unit,ProductType
from purchase.models import Batch
from purchase.models import PurchaseOrder


class Medicine(models.Model):
    name = models.CharField(null=True,blank=True,max_length=100)

class Warehouse(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True, blank=True,related_name='inv_warehouse_user')
    name = models.CharField(max_length=100)
    warehouse_id = models.CharField(max_length=150, unique=True, null=True, blank=True)  
    address = models.CharField(max_length=255, blank=True, null=True)
    city=models.CharField(max_length=100,null=True,blank=True)
    description = models.TextField(blank=True, null=True)
    reorder_level = models.PositiveIntegerField(default=10,null=True,blank=True)
    lead_time = models.PositiveIntegerField(null=True,blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.warehouse_id:
            self.warehouse_id = f"WH-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f" {self.name} "



class Location(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True, blank=True,related_name='inv_location_user')
    location_id = models.CharField(max_length=150, unique=True, null=True, blank=True)     
    warehouse = models.ForeignKey(Warehouse, related_name='locations', on_delete=models.CASCADE)  
    address= models.TextField(null=True,blank=True)  
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        if not self.location_id:
            self.location_id = f"LOCID-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Shelf(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="warehouse_shelves",null=True,blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="warehouse_location_shelves",null=True,blank=True)
    code = models.CharField(max_length=50,blank=True, null=True) 
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True) 

    class Meta:
        unique_together = ("warehouse", "code")

    def __str__(self):
        return f"{self.warehouse.name} - {self.code}"

        


class Inventory(models.Model):
    inventory_id = models.CharField(max_length=30,null=True,blank=True) 
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inv_inventory_user'
    )
    batch = models.ForeignKey(Batch,on_delete=models.CASCADE,related_name='batch_inventory',null=True,blank=True)
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='warehouse_inventory'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='location_inventory'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_inventories',
        null=True,
        blank=True
    )
    quantity = models.IntegerField(default=0,null=True,blank=True) 
    reorder_level = models.PositiveIntegerField(default=10,null=True,blank=True)
    remarks = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.inventory_id:
            self.inventory_id= f"INVID-{uuid.uuid4().hex[:8].upper()}"
     
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.warehouse}--{self.location}--{self.product.name}--{self.quantity}"




class InventoryTransaction(models.Model):  
    inventory_transaction=models.ForeignKey(Inventory,on_delete=models.CASCADE,null=True, blank=True,related_name='inventory_transaction') 
    transaction_id = models.CharField(max_length=30,null=True,blank=True)    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='inv_inventory_transaction_user')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_inventory_transaction',null=True, blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='batch_inventory_transaction',null=True, blank=True)  # NEW
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE,null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE,null=True, blank=True)
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='purchase_transactions', null=True, blank=True, on_delete=models.CASCADE)
   
    transaction_type = models.CharField(
    max_length=20,
    choices=[
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),       
        ('RETURN', 'RETURN'),   
        ('TRANSFER_OUT', 'Transfer Out'),
        ('TRANSFER_IN', 'Transfer In'),
        ('EXISTING_ITEM_IN', 'Existing items'),        
        ('SCRAPPED_OUT', 'Scrapped out'),
        ('SCRAPPED_IN','Scrapped in')
    ],
    null=True, blank=True
    )    
    quantity = models.PositiveIntegerField(null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)       
    remarks = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id= f"INVTID-{uuid.uuid4().hex[:8].upper()}"
     
        super().save(*args, **kwargs)   

    def __str__(self):       
        return f"{self.transaction_id}-{self.transaction_type}-{self.product}-{self.quantity}"







class MedicineSaleOnly(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,blank=True, null=True)
    doctor_ref= models.CharField(max_length=255, blank=True, null=True)      
    doctor = models.ForeignKey(Doctor,on_delete=models.CASCADE,null=True,blank=True,related_name='medicine_only_doctors')
    prescription_file = models.FileField(upload_to='medicine_only_prescriptions/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=50, 
        choices=[('Pending', 'Pending'), ('Delivered', 'Delivered')],
        default='Pending'
    )

    invoice = models.OneToOneField('billing.BillingInvoice', on_delete=models.CASCADE,related_name="medicine_only_invoices",null=True,blank=True)
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE,related_name="medicine_only_medical_records",null=True,blank=True)
    total_amount = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Medicine sale to: ({self.status})"



    
class MedicineSaleItem(models.Model):
    medicine_sale_only = models.ForeignKey(MedicineSaleOnly, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Product, on_delete=models.CASCADE,null=True,blank=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.batch.sale_price
        super().save(*args, **kwargs)

    @property
    def unit_price(self):
        return self.batch.sale_price
    
    @property
    def total_price(self):
        return self.quantity * self.batch.sale_price


