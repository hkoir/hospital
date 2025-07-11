
from django.urls import path
from .import views
from .views import (
    ExternalLabVisitListView,

)

app_name = 'lab_tests'

urlpatterns = [

   path('lab_test_search/', views.lab_test_search, name='lab_test_search'), 
   path('create_lab_test_result_order/<int:medical_record_id>/', views.create_lab_test_result_order, name='create_lab_test_result_order'),
   path('add_lab_test_result/<int:result_order_id>/', views.add_lab_test_result, name='add_lab_test_result'),
   path('lab_test_order_list/', views.lab_test_order_list, name='lab_test_order_list'),
   path('download_test_report/<int:result_order_id>/', views.download_test_report, name='download_test_report'),

   path('create_lab_test_result_with_items/<int:medical_record_id>/', views.create_lab_test_result_with_items, name='create_lab_test_result_with_items'),
   path('external-lab-visit/create/', views.create_external_lab_visit, name='create_external_lab_visit'),
   path('external-lab-visit/<int:pk>/', views.external_lab_visit_detail, name='external_lab_visit_detail'),
   path('External-visits/', ExternalLabVisitListView.as_view(), name='external_lab_visit_list'),

    path('lab_test_status_list/', views.lab_test_status_list, name='lab_test_status_list'),
    path('lab_test_deliveries/', views.pending_lab_test_deliveries, name='pending_lab_test_deliveries'),
    path('deliver_lab_test/<int:pk>/', views.deliver_lab_tests, name='deliver_lab_tests'),


]
