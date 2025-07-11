
from django.urls import path
from .import views


app_name = 'patients'


urlpatterns = [
path('patient_details/', views.patients_details, name='patients_details'),  
path('doctor_consultation/<int:appointment_id>/', views.doctor_consultation, name='doctor_consultation'),  

path('ipd_doctor_consultation/<int:medical_record_id>/', views.ipd_doctor_consultation, name='ipd_doctor_consultation'),  
path('download_prescription/<int:medical_record_id>/', views.download_prescription, name='download_prescription'),
path('download__ipd_prescription/<int:prescription_id>/', views.download_ipd_prescription, name='download_ipd_prescription'), 
path('download_ipd_lab_test/<int:lab_request_id>/', views.download_ipd_lab_test, name='download_ipd_lab_test'),    

path('medical-record/<int:record_id>/prescriptions/', views.medical_record_prescriptions_view, name='medical_record_prescriptions'),


path('patient_admission_create/', views.patient_admission_create, name='patient_admission_create'),  
path('patient_admission_detail/<int:admission_id>/', views.patient_admission_detail, name='patient_admission_detail'),  
path('patient_admission_list/', views.patient_admission_list, name='patient_admission_list'),  
path('change_bed/<int:admission_id>/', views.change_bed, name='change_bed'),  
path('discharge_patient/<int:admission_id>/', views.discharge_patient, name='discharge_patient'),  
path('admission/<int:admission_id>/admission_id/', views.create_discharge_report, name='create_discharge_report'),
path('generate_discharge_pdf/<int:discharge_report_id>/', views.generate_discharge_pdf, name='generate_discharge_pdf'),
path('patient_list/', views.patient_list, name='patient_list'),



]
