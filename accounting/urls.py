
from django.urls import path
from .import views


app_name = 'accounting' 

urlpatterns = [
    path('fiscal-years/', views.fiscalyear_list, name='fiscalyear_list'),
    path('fiscal-years/new/', views.fiscalyear_create, name='fiscalyear_create'),

    path('accounts/', views.account_list, name='account_list'),
    path('accounts/new/', views.account_create, name='account_create'),

    path('journal-entries/', views.journalentry_list, name='journalentry_list'),
    path('journal-entries/new/', views.journalentry_create, name='journalentry_create'),
    path('journal-entries/<int:pk>/', views.journalentry_detail, name='journalentry_detail'),

    path('balance-sheet/', views.balance_sheet_view, name='balance_sheet'),
    path("ledger/<int:account_id>/", views.ledger_view, name="ledger"), 
    path("trial-balance/", views.trial_balance_view, name="trial_balance"), 
    path('profit-loss/', views.profit_loss_view, name='profit_loss'),

    path('balance-sheet-quarterly/', views.balance_sheet_quarterly, name='balance_sheet_quarterly'),
     path('profit-loss-quarterly/', views.profit_loss_quarterly, name='profit_loss_quarterly'),

   
]