
from django.urls import path
from .import views


app_name = 'leavemanagement'


urlpatterns = [

    path('create_attendance_policy/', views.manage_attendance_policy, name='create_attendance_policy'),
    path('update_attendance_policy/<int:id>/', views.manage_attendance_policy, name='update_attendance_policy'),
    path('delete_attendance_policy/<int:id>/', views.delete_attendance_policye, name='delete_attendance_policy'), 
    
    path('view_attendance/', views.view_attendance, name='view_attendance'),
    path('attendance_input/', views.attendance_input, name='attendance_input'),
    path('update_attendance/<int:employee_id>/', views.update_attendance, name='update_attendance'), 
   
    path('create_leave_type/', views.manage_leave_type, name='create_leave_type'),
    path('update_leave_type/<int:id>/', views.manage_leave_type, name='update_leave_type'),
    path('delete_leave_type/<int:id>/', views.delete_leave_type, name='delete_leave_type'), 

    path('apply_leave/', views.apply_leave, name='apply_leave'),
    path('leave_history/', views.leave_history, name='leave_history'),
    path('pending_leave_list/', views.pending_leave_list, name='pending_leave_list'),
    path('approve_leave/<int:leave_id>/', views.approve_leave, name='approve_leave'),  
    path('leave_summary/', views.leave_summary, name='leave_summary'),
    path('leave_dashboard/', views.leave_dashboard, name='leave_dashboard'),

    path('carry-forward-leave/', views.carry_forward_leave, name='carry_forward_leave'),
    path('update_leave_balances_for_all/', views.monthly_leave_accrual_update, name='update_leave_balances_for_all'),
    path('check_and_deduct_late_leaves/', views.check_and_deduct_late_leaves, name='check_and_deduct_late_leaves'),

 

]