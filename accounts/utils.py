

from django.shortcuts import redirect
from django.contrib import messages
from django_tenants.utils import get_public_schema_name

import requests
from django.core.exceptions import ObjectDoesNotExist
import requests
from accounts.models import PhoneOTP
from clients.models import GlobalSMSConfig, TenantSMSConfig




def send_sms(tenant=None, phone_number=None, message=""):  
    config = None
  
    if tenant:
        config = TenantSMSConfig.objects.filter(tenant=tenant).first()

    if not config:
        config = GlobalSMSConfig.objects.first()

    if not config:
        raise Exception("No SMS configuration found.")

    params = {
        "api_key": config.api_key,
        "type": "text",
        "number": phone_number,
        "senderid": config.sender_id or "DefaultSID",
        "message": message,
    }

    try:
        response = requests.get(config.api_url, params=params)
        print("SMS Provider Response:", response.text)     
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise Exception(f"SMS sending failed: {str(e)}")





def tenant_only_view(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.tenant.schema_name == get_public_schema_name():
            messages.warning(request, "This page is not available on the public site.")
            return redirect('clients:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
