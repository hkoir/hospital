
from django.http import HttpResponse
from accounts.views import home
from django.urls import path, include

from django.shortcuts import render, redirect, get_object_or_404

def public_home(request):
    return HttpResponse("BNOVA Public Page 🚀")

def home(request):
    return render(request,'test.html')


urlpatterns = [
    path("", public_home),  # 👈 THIS LINE FIXES EVERYTHING

    path("home/", home),
    path("public-home/", public_home),

    path("accounts/", include('accounts.urls', namespace='accounts')),
    path("clients/", include('clients.urls', namespace='clients')),   
    path("core/", include('core.urls', namespace='core')),  
]


