
from django.urls import path
from .import views


app_name = 'workspace'


urlpatterns = [

path('doctor_workspace/', views.doctor_dashboard, name='doctor_dashboard'),  
path('staff_workspace/', views.staff_dashboard, name='staff_dashboard'),  
path('management_dashboard/', views.management_dashboard, name='management_dashboard'),  
path('appointment_list/', views.appointment_list, name='appointment_list'),

]
