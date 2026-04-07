
from django.http import HttpResponse
from accounts.views import home
from django.urls import path, include

from django.shortcuts import render, redirect, get_object_or_404

def public_home(request):
    return HttpResponse("BNOVA Public Page 🚀")

def home(request):
    return render(request,'test.html')


urlpatterns = [
    path("home/",home),
    path("public-home/", public_home),
    path("clients/", include('clients.urls', namespace='clients')),
    path("", include('accounts.urls', namespace='accounts')),
    path("core/", include('core.urls', namespace='core')),  

   
]


