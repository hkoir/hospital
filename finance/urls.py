
from django.urls import path
from .import views


app_name = 'finance'

urlpatterns = [

path('create_asset/', views.manage_asset, name='create_asset'),
path('update_asset/<int:id>/', views.manage_asset, name='update_asset'),
path('delete_asset/<int:id>/', views.delete_asset, name='delete_asset'),

path('create_expense/', views.manage_expense, name='create_expense'),
path('update_expense/<int:id>/', views.manage_expense, name='update_expense'),
path('delete_expense/<int:id>/', views.delete_expense, name='delete_expense'),
 
path('revenue_report/', views.revenue_report, name='revenue_report'),
path('top_expenses_head/', views.top_expenses_head, name='top_expenses_head'),
path('shareholder_dashboard/', views.shareholder_dashboard, name='shareholder_dashboard'),


path('create_purchase_invoice/<int:order_id>/', views.create_purchase_invoice, name='create_purchase_invoice'),
path('create_purchase_payment/<int:invoice_id>/', views.create_purchase_payment, name='create_purchase_payment'),
path('purchase_invoice_list/', views.purchase_invoice_list, name='purchase_invoice_list'),
path('purchase_invoice_detail/<int:invoice_id>/', views.purchase_invoice_detail, name='purchase_invoice_detail'),
path('download_purchase_invoice/<int:purchase_order_id>/', views.download_purchase_invoice, name='download_purchase_invoice'),
path('add_purchase_invoice_attachement/<int:invoice_id>/', views.add_purchase_invoice_attachment, name='add_purchase_invoice_attachment'),
path('add_purchase_payment_attachement/<int:invoice_id>/', views.add_purchase_payment_attachment, name='add_purchase_payment_attachment'),

path('money_receipt/', views.money_receipt, name='money_receipt'),


]
