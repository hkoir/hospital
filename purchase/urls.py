
from django.urls import path
from .import views


app_name = 'purchase'

urlpatterns = [    

  path('create_batch/', views.manage_batch, name='create_batch'),
  path('update_batch/<int:id>/', views.manage_batch, name='update_batch'),
  path('delete_batch/<int:id>/', views.delete_batch, name='delete_batch'),  
  path("batches/<int:batch_id>/generate-codes/", views.generate_batch_codes, name="generate_batch_codes"),

  path('purchase_dashboard/', views.purchase_dashboard, name='purchase_dashboard'),

  path('rfq/<int:request_order_id>/create/', views.create_rfq, name='create_rfq'),
  path('rfq/<int:pk>/', views.rfq_detail, name='rfq_detail'),
  path('rfqs/', views.rfq_list, name='rfq_list'),
  path("rfq/<int:pk>/send/", views.send_rfq, name="send_rfq"),

  path('supplier-quotation/<int:pk>/create/', views.create_supplier_quotation, name='create_supplier_quotation'),
  path('supplier-quotation/<int:pk>/', views.supplier_quotation_detail, name='supplier_quotation_detail'),
  path('supplier-quotations/', views.supplier_quotation_list, name='supplier_quotation_list'),
  path('supplier_quotation_comparison/<int:rfq_id>/', views.supplier_quotation_comparison, name='supplier_quotation_comparison'),
  path("supplier-quotation/<int:pk>/send/", views.send_supplier_quotation, name="send_supplier_quotation"),
 
  path("supplier-quotation/<int:pk>/approve/", views.approve_supplier_quotation, name="approve_supplier_quotation"),
  path("supplier-quotation/<int:pk>/reject/", views.reject_supplier_quotation, name="reject_supplier_quotation"),


  path('supplier-quotation/<int:quotation_id>/convert/', views.convert_quotation_to_po,name='convert_supplier_quotation'),
  path('add_batch_details/<int:po_id>/', views.add_batch_details,name='add_batch_details'),
  path('batch_list/', views.batch_list,name='batch_list'),



    
  path('create_purchase_request/', views.create_purchase_request, name='create_purchase_request'),
  path('cconfirm_purchase_request/', views.confirm_purchase_request, name='confirm_purchase_request'),
  path('purchase_request_order_list/', views.purchase_request_order_list, name='purchase_request_order_list'),
  path('purchase_request_items/<int:order_id>/', views.purchase_request_items, name='purchase_request_items'),
 
  #path('create_purchase_order/', views.create_purchase_order, name='create_purchase_order'),

  path('create_purchase_order/<int:request_id>/', views.create_purchase_order, name='create_purchase_order'),
  path('confirm_purchase_order/', views.confirm_purchase_order, name='confirm_purchase_order'),
  path('purchase_order_list/', views.purchase_order_list, name='purchase_order_list'),
  path('purchase_order_items/<int:order_id>/', views.purchase_order_items, name='purchase_order_items'),

  path('qc_dashboard/', views.qc_dashboard, name='qc_dashboard'),
  path('qc_dashboard/<int:purchase_order_id>/', views.qc_dashboard, name='qc_dashboard_with_order'), 
  path('qc_inspect_item/<int:item_id>/', views.qc_inspect_item, name='qc_inspect_item'),

  path('purchase_order_item/', views.purchase_order_item, name='purchase_order_item'),
  path('purchase_order_item_dispatch/<str:order_id>/', views.purchase_order_item_dispatch, name='purchase_order_item_dispatch'),
  path('update_purchase_order_status/<int:order_id>/', views.update_purchase_order_status, name='update_purchase_order_status'),
 
  path('process-order/<int:order_id>/', views.process_purchase_order, name='process_purchase_order'),
  path('process-request-order/<int:order_id>/', views.process_purchase_request, name='process_purchase_request'),




]
