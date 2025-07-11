
from django.urls import path
from .import views


app_name = 'medical_records'

urlpatterns = [
 path('medical-records/',views.medical_record_list, name='medical_record_list'),
path('records/<int:record_id>/progress/', views.medical_record_progress_detail, name='medical_record_progress_detail'),
path('add_medical_record_progress/<int:record_id>/', views.add_medical_record_progress, name='add_medical_record_progress'),
path('progress/<int:progress_id>/edit/', views.edit_medical_record_progress, name='edit_medical_record_progress'),

path(
    'medical-record/<int:record_id>/lab-test-requests/', views.grouped_lab_test_requests_view,
    name='grouped_lab_test_requests'),




]
