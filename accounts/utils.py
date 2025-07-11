

from django.shortcuts import redirect
from django.contrib import messages
from django_tenants.utils import get_public_schema_name


def tenant_only_view(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.tenant.schema_name == get_public_schema_name():
            messages.warning(request, "This page is not available on the public site.")
            return redirect('clients:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
