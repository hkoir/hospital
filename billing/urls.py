
from django.urls import path
from .import views


app_name = 'billing'

urlpatterns = [

 path('invoice_detail/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
 path('get-consultation-fee/', views.get_consultation_fee, name='get_consultation_fee'),
 path('add_ipd_consultation_billl/<int:invoice_id>/', views.add_ipd_consultation_bill, name='add_ipd_consultation_bill'),
 path('get-test-fee/', views.get_test_fee, name='get_test_fee'),
 path('add_lab_test_bill/<int:invoice_id>/', views.add_lab_test_bill, name='add_lab_test_bill'),
 path('add_ward_bill/<int:invoice_id>/', views.add_ward_bill, name='add_ward_bill'),
 path('add_medicine_bill/<int:invoice_id>/', views.add_medicine_bill, name='add_medicine_bill'),
 path('add_misc_bill/<int:invoice_id>/', views.add_misc_bill, name='add_misc_bill'),
 path('ot_booking/<int:invoice_id>/', views.ot_booking, name='ot_booking'),

 path('ipd_invoices/', views.ipd_invoice_list, name='ipd_invoice_list'),
 path('opd_invoices/', views.opd_invoice_list, name='opd_invoice_list'),
 path('invoice/<int:invoice_id>/edit/', views.edit_invoice, name='edit_invoice'),
 path('invoice/<int:invoice_id>/delete/', views.delete_invoice, name='delete_invoice'),

 path('invoice/<int:invoice_id>/add-payment/', views.add_payment, name='add_payment'),
 path('finalize_invoice/<int:invoice_id>/', views.finalize_invoice, name='finalize_invoice'),
 path('ajax/get-batch-price/', views.get_batch_price, name='ajax_get_batch_price'),
path('download_invoice/<int:invoice_id>/', views.download_invoice, name='download_invoice'),

path('emergency/create/', views.emergency_visit_create, name='emergency_visit_create'),

 path('doctor-service-rates/', views.doctor_service_rate_list, name='doctor_service_rate_list'),
 path('doctor-service-rates/add/', views.doctor_service_rate_create, name='doctor_service_rate_create'),
 path('doctor_payment_summary/<int:doctor_id>/', views.doctor_payment_summary, name='doctor_payment_summary'),
path('add_doctor_payment/<int:doctor_id>/', views.add_doctor_payment, name='add_doctor_payment'),
path("ipd-followup/<int:patient_id>/<int:invoice_id>/", views.ipd_followup_booking, name="ipd_followup_booking"),


   
]
