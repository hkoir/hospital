
from django.urls import path
from .import views


app_name = 'inventory'



urlpatterns = [
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
    
path('inventory_transaction_view/', views.inventory_transaction_view, name='inventory_transaction_view'),  
path('inventory_dashboard/', views.inventory_dashboard, name='inventory_dashboard'), 

path('create_medicine_sale_only/', views.create_medicine_sale_only,name='create_medicine_sale_only'), 
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

]   
