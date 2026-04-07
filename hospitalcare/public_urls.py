
from django.http import HttpResponse
from accounts.views import home
from django.urls import path, include

from django.shortcuts import render, redirect, get_object_or_404
from accounts.views import allow_cert

def public_home(request):
    return HttpResponse("BNOVA Public Page updated again 🚀")

def home(request):
    return render(request,'test.html')


urlpatterns = [
    path("allow-cert", allow_cert),  
    path("", public_home), 

    path("home/", home),
    path("public-home/", public_home),

    path("accounts/", include('accounts.urls', namespace='accounts')),
    path("clients/", include('clients.urls', namespace='clients')),   
    path("core/", include('core.urls', namespace='core')),  
]


