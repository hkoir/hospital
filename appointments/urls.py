
from django.urls import path
from .import views


app_name = 'appointments'

urlpatterns = [
path('create_doctor_timeslots/', views.create_doctor_timeslots, name='create_doctor_timeslots'),  
   
path('update_doctor_timeslots/<int:id>/', views.create_doctor_timeslots, name='update_doctor_timeslots'),    
path('delete_doctor_timeslots/<int:id>/', views.create_doctor_timeslots, name='delete_doctor_timeslots'),  


path("available_doctors/", views.available_doctors, name="available_doctors"),
path('doctors/<int:doctor_id>/available-slots/', views.view_available_slots, name='view_available_slots'),
path('get-timeslots/', views.get_timeslots, name='get_timeslots'),
path("book-slot/", views.book_slot, name="book_slot"),
path("general_appointment/", views.general_appointment, name="general_appointment"),

path("appointments/get-doctors/", views.get_doctors_by_specialization, name="get-doctors"),
path('specialization/<int:specialization_id>/', views.specialization_detail, name='specialization_detail'),

path("appointment_list/", views.appointment_list, name="appointment_list"),
path("cancel-appointment/", views.cancel_appointment, name="cancel_appointment"),
path("booking_confirmation_paymentt/<int:appointment_id>/", views.booking_confirmation_payment, name="booking_confirmation_payment"),
path('doctors/', views.doctor_list, name='doctor_list'),

path('add_medicine_labtest_to_invoice/<int:appointment_id>/', views.add_medicine_labtest_to_invoice, name='add_medicine_labtest_to_invoice'),



]
