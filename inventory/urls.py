
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


]   
