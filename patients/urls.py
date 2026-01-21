
from django.urls import path
from .import views


app_name = 'patients'


urlpatterns = [
path('patient-create/', views.PatientCreateView.as_view(), name='patient_create'),
path('delete/<int:pk>/', views.PatientDeleteView.as_view(), name='patient_delete'),

path('patient_details_with_id/<int:pk>/', views.patients_details_with_id, name='patient_details_with_id'),
path('patient_details/', views.patients_details, name='patients_details'), 
path("search_patients/", views.search_patients, name="search_patients"),
path("search_doctors/", views.search_doctors, name="search_doctors"),

path("medicine-search/", views.medicine_search, name="medicine_search"),
path('doctor_consultation/<int:appointment_id>/', views.doctor_consultation, name='doctor_consultation'),  
path('prescription/print/<int:prescription_id>/', views.print_prescription, name='print_prescription'),
path('patient_medical_records/<int:patient_id>/', views.patient_medical_records, name='patient_medical_records'),

path('ipd_doctor_consultation/<int:appointment_id>/', views.ipd_doctor_consultation, name='ipd_doctor_consultation'),  
path('download_prescription/<int:medical_record_id>/', views.download_prescription, name='download_prescription'),
path('download__ipd_prescription/<int:prescription_id>/', views.download_ipd_prescription, name='download_ipd_prescription'), 
path('download_ipd_lab_test/<int:lab_request_id>/', views.download_ipd_lab_test, name='download_ipd_lab_test'),    

path('medical-record/<int:record_id>/prescriptions/', views.medical_record_prescriptions_view, name='medical_record_prescriptions'),


path('patient_admission_create/', views.patient_admission_create, name='patient_admission_create'),  
path('patient_admission_detail/<int:admission_id>/', views.patient_admission_detail, name='patient_admission_detail'),  
path('patient_emergency_detail/<int:emergency_id>/', views.patient_admission_detail, name='patient_emergency_detail'),
path('patient_admission_list/', views.patient_admission_list, name='patient_admission_list'),  
path('discharge_patient/<int:admission_id>/', views.discharge_patient, name='discharge_patient'),  

path('convert_emergency_to_admission/<int:emergency_id>/', views.convert_emergency_to_admission, name='convert_emergency_to_admission'),  
path('patient_admission_update/<int:admission_id>/', views.patient_admission_update, name='patient_admission_update'),  



path('approve_discharge_emergency/<int:emergency_id>/', views.approve_discharge, name='approve_discharge_emergency'),  
path('approve_discharge_admission/<int:admission_id>/', views.approve_discharge, name='approve_discharge_admission'),  
path('admission/<int:admission_id>/admission_id/', views.create_discharge_report, name='create_discharge_report'),
path('create_emergency_discharge_report/<int:visit_id>/', views.create_emergency_discharge_report, name='create_emergency_discharge_report'),

path('generate_discharge_pdf/<int:discharge_report_id>/', views.generate_discharge_pdf, name='generate_discharge_pdf'),
path('patient_list/', views.patient_list, name='patient_list'),
path('patient_update/<int:pk>/', views.PatientUpdateView.as_view(), name='patient_update'),
path('patient_id_card/<int:pk>/', views.patient_id_card, name='patient_id_card'),

path('change_bed/<int:admission_id>/', views.change_bed, name='change_bed'),  
path('change_emergency_bed/<int:emergency_id>/', views.change_bed, name='change_emergency_bed'),  
path('assign_bed/invoice/<int:invoice_id>/', views.assign_bed, name='assign_bed_invoice'),
path('assign_bed/visit/<int:visit_id>/', views.assign_bed, name='assign_bed_visit'),


path('patient_history/<int:invoice_id>/', views.patient_history, name='patient_history')

]
