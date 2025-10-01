
from django.urls import path
from .import views


app_name = 'product'


urlpatterns = [

    path('', views.product_dashboard, name='product_dashboard'),
    path('create_category/', views.manage_category, name='create_category'),
    path('update_category/<int:id>/', views.manage_category, name='update_category'),
    path('delete_category/<int:id>/', views.delete_category, name='delete_category'),

    path('create_product/', views.manage_product, name='create_product'),
    path('update_product/<int:id>/', views.manage_product, name='update_product'),
    path('delete_product/<int:id>/', views.delete_product, name='delete_product'),
    path('product_data/<int:product_id>/', views.product_data, name='product_data'),

    path('print_unit_labels/<int:batch_id>/', views.print_unit_labels, name='print_unit_labels'),
  
]
