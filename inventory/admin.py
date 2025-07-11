from django.contrib import admin

from.models import Medicine,Warehouse,Location,ProductType,ProductCategory,Product,Inventory,InventoryTransaction,Batch
from.models import MedicineSaleOnly,MedicineSaleItem


admin.site.register(Medicine)
admin.site.register(Warehouse)
admin.site.register(Location)
admin.site.register(ProductType)
admin.site.register(ProductCategory)
admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(InventoryTransaction)
admin.site.register(Batch)

admin.site.register(MedicineSaleOnly)
admin.site.register(MedicineSaleItem)
