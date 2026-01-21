
from django.urls import path
from .import views
from .views import (
    ExternalLabVisitListView,

)

app_name = 'lab_tests'

urlpatterns = [

    path("labtest-category/add/", views.LabtestCategoryCreateView.as_view(), name="labtest_category_add"),
    path("labtest-category/<int:pk>/edit/", views.LabtestCategoryUpdateView.as_view(), name="labtest_category_edit"),
    path("labtest_catelogue/add/", views.LabtestCatelogueCreateView.as_view(), name="labtest_catelogue_add"),
    path("labtest_catelogue/<int:pk>/edit/", views.LabtestCatelogueUpdateView.as_view(), name="labtest_catelogue_edit"),

   path('lab_test_search/', views.lab_test_search, name='lab_test_search'), 
   path('create_lab_test_result_order/<int:medical_record_id>/', views.create_lab_test_result_order, name='create_lab_test_result_order'),
   path('add_lab_test_result/<int:result_order_id>/', views.add_lab_test_result, name='add_lab_test_result'),
   path('lab_test_order_list/', views.lab_test_order_list, name='lab_test_order_list'),
   path('download_test_report/<int:result_order_id>/', views.download_test_report, name='download_test_report'),
   path("lab-test/print/<int:order_id>/", views.print_lab_test_order, name="print_lab_test_order"),

   path('create_lab_test_result_with_items/<int:medical_record_id>/<int:appointment_id>/', views.create_lab_test_result_with_items, name='create_lab_test_result_with_items'),
   path('external-lab-visit/create/', views.create_external_lab_visit, name='create_external_lab_visit'),
   path('external-lab-visit/<int:pk>/', views.external_lab_visit_detail, name='external_lab_visit_detail'),
   path('External-visits/', ExternalLabVisitListView.as_view(), name='external_lab_visit_list'),

    path('lab_test_status_list/', views.lab_test_status_list, name='lab_test_status_list'),
    path('lab_test_deliveries/', views.pending_lab_test_deliveries, name='pending_lab_test_deliveries'),
    path('deliver_lab_test/<int:pk>/', views.deliver_lab_tests, name='deliver_lab_tests'),

    path("all-request-oders/", views.all_request_order_list, name="all_request_order_list"),
    path("request-order/<int:request_id>/items/",views.request_order_items,name="request_order_items"),
    path("sample-collect/<int:request_item_id>/items/",views.collect_sample,name="collect_sample"),
    path("print_sample_label/<int:sample_id>/items/",views.print_sample_label,name="print_sample_label"),
    path("sample_list/",views.sample_list,name="sample_list"),
    path("request_sample_list/<int:request_id>/",views.request_sample_list,name="request_sample_list"),
 
    path("mark_sample_receive/<int:sample_id>/",views.mark_sample_receive,name="mark_sample_receive"),
    path("mark_sample_processing/<int:sample_id>/",views.mark_sample_processing,name="mark_sample_processing"),
    path("mark_sample_completed/<int:sample_id>/",views.mark_sample_receive,name="mark_sample_completed"),

    path("final_report/<int:order_id>/", views.final_lab_report, name="final_lab_report"),


]
