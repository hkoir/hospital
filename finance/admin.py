from django.contrib import admin
from.models import PurchaseInvoice,PurchasePayment
from.models import PurchaseInvoiceAttachment,PurchasePaymentAttachment
from.models import Asset,AllExpenses,AssetDepreciationRecord

admin.site.register(Asset)
admin.site.register(AllExpenses)
admin.site.register(AssetDepreciationRecord)


admin.site.register(PurchaseInvoice)
admin.site.register(PurchasePayment)


admin.site.register(PurchaseInvoiceAttachment)
admin.site.register(PurchasePaymentAttachment)

