
from django.urls import path
from .import views


app_name = 'finance'

urlpatterns = [

path('create_asset/', views.manage_asset, name='create_asset'),
path('update_asset/<int:id>/', views.manage_asset, name='update_asset'),
path('delete_asset/<int:id>/', views.delete_asset, name='delete_asset'),

path('create_expense/', views.manage_expense, name='create_expense'),
path('update_expense/<int:id>/', views.manage_expense, name='update_expense'),
path('delete_expense/<int:id>/', views.delete_expense, name='delete_expense'),
 
path('revenue_report/', views.revenue_report, name='revenue_report'),
path('top_expenses_head/', views.top_expenses_head, name='top_expenses_head'),
path('shareholder_dashboard/', views.shareholder_dashboard, name='shareholder_dashboard'),

]
