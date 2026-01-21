
from django.urls import path
from .import views


app_name = 'inventory'



urlpatterns = [
path("warehouse/add/", views.WarehouseCreateView.as_view(), name="warehouse_add"),
path("warehouse/<int:pk>/edit/", views.WarehouseUpdateView.as_view(), name="warehouse_edit"),
path("location/add/", views.WarehouseLocationCreateView.as_view(), name="location_add"),
path("location/<int:pk>/edit/", views.WarehouseLocationUpdateView.as_view(), name="location_edit"),
path("product-type/add/", views.ProductTypeCreateView.as_view(), name="product_type_add"),
path("product-type/<int:pk>/edit/", views.ProductTypeUpdateView.as_view(), name="product_type_edit"),


path('', views.product_dashboard, name='product_dashboard'),
path('product_list/', views.product_list, name='product_list'),
path('create_product/', views.manage_product, name='create_product'),
path('update_product/<int:id>/', views.manage_product, name='update_product'),
path('delete_product/<int:id>/', views.delete_product, name='delete_product'),
path('product_data/<int:product_id>/', views.product_data, name='product_data'),

path('create_category/', views.manage_category, name='create_category'),
path('update_category/<int:id>/', views.manage_category, name='update_category'),
path('delete_category/<int:id>/', views.delete_category, name='delete_category'),

path('create_batch/', views.manage_batch, name='create_batch'),
path('update_batch/<int:id>/', views.manage_batch, name='update_batch'),
path('delete_batch/<int:id>/', views.delete_batch, name='delete_batch'),
    
path('create_inventory_transaction/', views.create_inventory_transaction, name='inventory_transaction_view'),  
path('inventory_dashboard/', views.inventory_dashboard, name='inventory_dashboard'), 

path('create_medicine_sale_only/', views.create_medicine_sale_only,name='create_medicine_sale_only'), 
path("invoice/medicine-sale/<int:invoice_id>/print/",views.medicine_sale_invoice_print,name="medicine_sale_invoice_print"),
path('pending_medicine_deliveries/', views.pending_medicine_deliveries,name='pending_medicine_deliveries'), 
path('deliver_invoice_medicines/<int:invoice_id>/', views.deliver_invoice_medicines,name='deliver_invoice_medicines'), 



path('create_warehouse/', views.manage_warehouse, name='create_warehouse'),
path('update_warehouse/<int:id>/', views.manage_warehouse, name='update_warehouse'),
path('delete_warehouse/<int:id>/', views.delete_warehouse, name='delete_warehouse'),
path('create_location/', views.manage_location, name='create_location'),
path('update_location/<int:id>/', views.manage_location, name='update_location'),
path('delete_location/<int:id>/', views.delete_location, name='delete_location'),
path('get_locations/', views.get_locations, name='get_locations'), 

path('complete_quality_control/<int:qc_id>/', views.complete_quality_control, name='complete_quality_control'),    

 path('ajax/medicines/<int:category_id>/', views.get_medicines, name='ajax_get_medicines'),
 path('ajax/batches/<int:product_id>/', views.get_batches, name='ajax_get_batches'),


]   
