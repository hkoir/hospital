
from django.urls import path
from .import views


app_name = 'visitors'

urlpatterns = [

path("visitor_landing_page/", views.visitor_landing_page, name="visitor_landing_page"),
path("available_doctors/", views.available_doctors, name="available_doctors"),
path('doctors/<int:doctor_id>/available-slots/', views.view_available_slots, name='view_available_slots'),
path('get-timeslots/', views.get_timeslots, name='get_timeslots'),
path("book-slot/", views.book_slot, name="book_slot"),
path("appointments/get-doctors/", views.get_doctors_by_specialization, name="get-doctors"),
path('specialization/<int:specialization_id>/', views.specialization_detail, name='specialization_detail'),
path("appointment_list/", views.appointment_list, name="appointment_list"),
path("cancel-appointment/", views.cancel_appointment, name="cancel_appointment"),
path('view_notices/', views.view_notices, name='view_notices'),   
path('patient_admission_list/', views.patient_admission_list, name='patient_admission_list'), 

path('ipd_invoice_list/', views.ipd_invoice_list, name='ipd_invoice_list'),
path('opd_invoice_list/', views.opd_invoice_list, name='opd_invoice_list'),
path('finalize_invoice/<int:invoice_id>/', views.finalize_invoice, name='finalize_invoice'),
path('download_invoice/<int:invoice_id>/', views.download_invoice, name='download_invoice'),

path('generate_discharge_pdf/<int:discharge_report_id>/', views.generate_discharge_pdf, name='generate_discharge_pdf'),  
   
]
