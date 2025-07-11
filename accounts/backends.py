from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django_tenants.utils import get_tenant_model
from django.core.exceptions import PermissionDenied
from clients.models import Client
User = get_user_model()


class TenantAuthenticationBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is None:
            return None

        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            return None

        try:
            user = User.objects.get(username=username, tenant=tenant)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        

        
# class TenantAuthenticationBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, tenant=None, **kwargs):
#         if request is None or tenant is None:
#             return None

#         try:
#             tenant_obj = Client.objects.get(schema_name=tenant)  # 🔥 Get Tenant Object
#             user = User.objects.get(username=username, tenant=tenant_obj)  # 🔥 Pass the Object
#             if user.check_password(password):
#                 return user
#         except (User.DoesNotExist, Client.DoesNotExist):
#             return None
