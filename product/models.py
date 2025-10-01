
from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
import uuid
from accounts.models import CustomUser
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from decimal import Decimal
from datetime import datetime
from django.utils.translation import gettext_lazy as _
from purchase.models import Batch


class Category(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='category_user')
    name = models.CharField(max_length=100)
    category_id = models.CharField(max_length=150, unique=True, null=True, blank=True)
    image = models.ImageField(upload_to="images/categories",null=True,blank=True)  
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(verbose_name=_("Category safe URL"), max_length=255, unique=True,null=True,blank=True)  
    is_active = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
            ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.category_id:
            self.category_id = f"CAT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("manage_shop:category_list", args=[self.slug])

    def __str__(self):
        return self.name





class Product(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='product_user')
    name = models.CharField(max_length=255)
    product_code = models.CharField(max_length=150, unique=True, null=True, blank=True)  
    sku = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')  # Updated related name
    product_type = models.CharField(max_length=50, 
        choices=[
        ('raw_materials', 'raw_materials'),
        ('finished_product', 'finished_roduct'),
        ('component','component'),
        ('BOM','BOM')
        ], 
        default='finished product')
    brand = models.CharField(max_length=255, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    UOM = models.CharField(max_length=15,null=True,blank=True)
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True )
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    manufacture_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)  
    warranty = models.DurationField(blank=True, null=True)  
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    reorder_level = models.PositiveIntegerField(default=10,null=True,blank=True)
    lead_time = models.PositiveIntegerField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    product_image= models.ImageField(upload_to='product/images',null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    product_code = models.CharField(
        verbose_name=_("Product Code"),
        max_length=20,
        unique=True,
        help_text=_("Unique product code identifier"),
        null=True,
        blank=True,
      
    )    
   
    slug = models.SlugField(max_length=255,unique=True,null=True,blank=True)
    base_selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
   
   
    image = models.ImageField(
        verbose_name=_("image"),
        help_text=_("Upload a product image"),
        upload_to="images_products/",null=True,blank=True
       
    )    
    
    video = models.FileField(
        verbose_name=_("video"),
        help_text=_("Upload a product video"),
        upload_to="product_videos/",
        null=True,
        blank=True,)   

    is_asset = models.BooleanField(default=False) 
    is_popular = models.BooleanField(default=False)
    is_hot_sale = models.BooleanField(default=False)
    is_regular = models.BooleanField(default=True)  
    is_offer = models.BooleanField(default=False)  
    likes = models.ManyToManyField(CustomUser, related_name='liked_products', blank=True)
    users_wishlist = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="user_wishlist", blank=True)
    low_stock_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("5.00"),
        help_text="Quantity below which this product is considered low in stock"
    ) 


    def save(self, *args, **kwargs):
        if not self.product_code:
            self.product_code = f"PID-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    
    def get_absolute_url(self):
        return reverse("store:product_detail", args=[self.slug])


    def __str__(self):
        return self.name


class Component(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='component_user')
    component_id = models.CharField(max_length=150, unique=True, null=True, blank=True)  
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="components")  # Updated related name
    quantity_needed = models.PositiveIntegerField()
    unit_price =models.DecimalField(max_digits=15,decimal_places=2,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.component_id:
            self.component_id = f"CID-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
         return self.name



class BOM(models.Model):
    name = models.CharField(max_length=100) 
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='bom_user') 
    bom_id = models.CharField(max_length=150, unique=True, null=True, blank=True) 
    description = models.TextField(blank=True, null=True) 
    product = models.ForeignKey(Product, related_name='bills_of_materials', on_delete=models.CASCADE)
    unit_price =models.DecimalField(max_digits=15,decimal_places=2,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True) 

    def save(self, *args, **kwargs):
        if not self.bom_id:
            self.bom_id = f"BID-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

    
class Unit(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="units")    
    serial_number = models.CharField(max_length=100, unique=True)   
    barcode = models.CharField(max_length=100, unique=True)
    barcode_image = models.ImageField(upload_to="barcodes/", null=True, blank=True)
    qr_code_image = models.ImageField(upload_to="qrcodes/", null=True, blank=True)   
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    factor = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    sold = models.BooleanField(default=False)  

    def __str__(self):
        return f"{self.batch.product.name} - {self.serial_number}"



@receiver(pre_save, sender=Batch)
def generate_batch_no(sender, instance, **kwargs):
    if not instance.batch_number:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        instance.batch_number = f"BAT-{instance.product.id}-{timestamp}"













from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from product.models import Product,Category
from accounts.models import CustomUser





class ProductType(models.Model): 
    name = models.CharField(verbose_name=_("Product Name"), help_text=_("Required"), max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Product Type")
        verbose_name_plural = _("Product Types")

    def __str__(self):
        return self.name


class ProductSpecification(models.Model): 
    product_type = models.ForeignKey(ProductType, on_delete=models.CASCADE)# RESTRICT
    name = models.CharField(verbose_name=_("Name"), help_text=_("Required"), max_length=255)

    class Meta:
        verbose_name = _("Product Specification")
        verbose_name_plural = _("Product Specifications")

    def __str__(self):
        return self.name    

from django.core.exceptions import ValidationError
import uuid

def validate_max_words(value, max_words=100):
    words = value.split()
    if len(words) > max_words:
        raise ValidationError(f"Too many words! Maximum allowed is {max_words}.")



class ProductSpecificationValue(models.Model):  
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    specification = models.ForeignKey(ProductSpecification, on_delete=models.CASCADE) #RESTRICT
    value = models.CharField(
        verbose_name=_("value"),
        help_text=_("Product specification value (maximum of 255 words"),
        max_length=255,
    )

    class Meta:
        verbose_name = _("Product Specification Value")
        verbose_name_plural = _("Product Specification Values")

    def __str__(self):
        return self.value


class ProductImage(models.Model):   
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_photo")
    image = models.ImageField(
        verbose_name=_("image"),
        help_text=_("Upload a product image"),
        upload_to="images/",
        default="images/default.png",
    )  

    alt_text = models.CharField(
        verbose_name=_("Alturnative text"),
        help_text=_("Please add alturnative text"),
        max_length=255,
        null=True,
        blank=True,
    )
    is_feature = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")


class ProductVideo(models.Model): 
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_Video")
    video = models.FileField(
        verbose_name=_("video"),
        help_text=_("Upload a product video"),
        upload_to="videos/",
        null=True,
        blank=True,)

    alt_text = models.CharField(
        verbose_name=_("Alturnative text"),
        help_text=_("Please add alturnative text"),
        max_length=255,
        null=True,
        blank=True,
    )
    is_feature = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Product Video")
        verbose_name_plural = _("Product Videos")





class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    rating = models.IntegerField()
    image_one = models.ImageField(upload_to='review_images/', blank=True, null=True)
    image_two = models.ImageField(upload_to='review_images/', blank=True, null=True)
    image_three = models.ImageField(upload_to='review_images/', blank=True, null=True)
    image_four = models.ImageField(upload_to='review_images/', blank=True, null=True)






class CompanyReview(models.Model):
    DELIVERY_QUALITY_CHOICES = (
        ('', 'Select an option'), 
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    )

    PAYMENT_QUALITY_CHOICES = (
         ('', 'Select an option'), 
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    )

    COMMUNICATION_QUALITY_CHOICES = (
         ('', 'Select an option'), 
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    )

    PRODUCT_QUALITY_CHOICES = (
         ('', 'Select an option'), 
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    )

    delivery_quality = models.IntegerField(choices=DELIVERY_QUALITY_CHOICES)
    payment_quality = models.IntegerField(choices=PAYMENT_QUALITY_CHOICES)
    communication_quality = models.IntegerField(choices=COMMUNICATION_QUALITY_CHOICES)
    product_quality = models.IntegerField(choices=PRODUCT_QUALITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    review_text = models.TextField(blank='', null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name="product_company_review")




class AudioModel(models.Model):       
    success_audio = models.FileField(upload_to='audio/', blank=True, null=True)  
    failure_audio = models.FileField(upload_to='audio/', blank=True, null=True)

    welcome_message = models.FileField(upload_to='audio/', blank=True, null=True)  
    account_create_success = models.FileField(upload_to='audio/', blank=True, null=True)
    request_for_logged_in = models.FileField(upload_to='audio/', blank=True, null=True)  
    logged_in_success = models.FileField(upload_to='audio/', blank=True, null=True)
    forget_password = models.FileField(upload_to='audio/', blank=True, null=True)  
    order_placed_success = models.FileField(upload_to='audio/', blank=True, null=True)
    hold_on_message = models.FileField(upload_to='audio/', blank=True, null=True)