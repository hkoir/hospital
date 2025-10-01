from django.contrib import admin

# Register your models here.
from django.contrib import admin

from .models import (   
    Product,
    Category,
    Component,
    BOM,
    ProductImage,
    ProductSpecification,
    ProductSpecificationValue,
    ProductType,
    ProductVideo,
    Review,
    CompanyReview,
    Unit
   
)

admin.site.register(Category)
admin.site.register(Component)
admin.site.register(BOM)
admin.site.register(Unit)





class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    inlines = [
        ProductSpecificationInline,
      
    ]


class ProductImageInline(admin.TabularInline):
    model = ProductImage



class ProductSpecificationValueInline(admin.TabularInline):
    model = ProductSpecificationValue

class ProductVideoInline(admin.TabularInline):
    model = ProductVideo

class ProductReviewInline(admin.TabularInline):
    model = Review



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = ["name", "slug","brand",]
    list_filter = ["name","brand","product_code","is_popular","is_hot_sale","is_regular"]
    list_display = ["name","brand","product_code","is_popular","is_hot_sale","is_regular"]
    inlines = [
        ProductSpecificationValueInline,
        ProductImageInline,
        ProductVideoInline,
        ProductReviewInline,
    ]




@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'delivery_quality', 'payment_quality', 'communication_quality', 'product_quality','review_text')