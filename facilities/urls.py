
from django.urls import path
from .import views


app_name = 'facilities'

urlpatterns = [
     path('status/', views.ward_room_bed_status, name='ward_room_bed_status'),
 
]
