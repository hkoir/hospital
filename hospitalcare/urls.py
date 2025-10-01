

from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls', namespace='accounts')),
    path("accounts/", include("django.contrib.auth.urls")), 
    path('core/',include('core.urls',namespace='core')),
    path('clients/',include('clients.urls',namespace='clients')),  
    path('leavemanagement/',include('leavemanagement.urls',namespace='leavemanagement')),
    path('billing/',include('billing.urls',namespace='billing')),  
    path('appointments/',include('appointments.urls',namespace='appointments')),  
    path('inventory/',include('inventory.urls',namespace='inventory')),  
    path('medical_records/',include('medical_records.urls',namespace='medical_records')),  
    path('patients/',include('patients.urls',namespace='patients')),  
    path('lab_tests/',include('lab_tests.urls',namespace='lab_tests')),  

    path('visitors/',include('visitors.urls',namespace='visitors')),  

    path('messaging/',include('messaging.urls',namespace='messaging')),  
    path('facilities/',include('facilities.urls',namespace='facilities')),  
    path('finance/',include('finance.urls',namespace='finance')), 
    path('accounting/',include('accounting.urls',namespace='accounting')),  
    path('purchase/',include('purchase.urls',namespace='purchase')),  
    path('logistics/',include('logistics.urls',namespace='logistics')),  
    path('supplier/',include('supplier.urls',namespace='supplier')),  
    path('product/',include('product.urls',namespace='product')),  
   
    
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
