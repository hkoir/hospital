
from django.urls import path
from .import views


app_name = 'facilities'

urlpatterns = [
     path('status/', views.ward_room_bed_status, name='ward_room_bed_status'),
   path("ajax/get-rooms/", views.get_rooms, name="get_rooms"),
  path("ajax/get-beds/", views.get_beds, name="get_beds"),
]
