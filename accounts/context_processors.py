
from .models import UserProfile
from django.db.utils import ProgrammingError
from django_tenants.utils import get_tenant
from clients.models import Tenant
from patients.models import Patient
from core.models import Doctor,Employee
from django.db.models import Q  
from messaging.models import Notification



def user_info(request):
    profile_picture_url = None
    student = None
    teacher = None
    employee = None
    school_logo_url = 'Unknown'
    school_name = 'None'
    tenant_photo_url = None

    if request.user.is_authenticated:
        try:
            current_client = get_tenant(request)
   
            if current_client.schema_name == 'public':
                return {
                    'user_info': request.user.username,
                    'profile_picture_url': profile_picture_url,
                    'school_logo_url': school_logo_url,
                    'school_name': school_name,
                }
           
            doctor = Doctor.objects.filter(user=request.user).first()
            employee = Employee.objects.filter(user=request.user).first()
            user_profile = UserProfile.objects.filter(user=request.user).first()

            current_client = get_tenant(request)

            tenant_instance = Tenant.objects.filter(tenant=current_client).first()
            if tenant_instance and tenant_instance.logo:
                tenant_photo_url = tenant_instance.logo.url
                tenant_name = tenant_instance.name

            if user_profile and user_profile.profile_picture:
                profile_picture_url = user_profile.profile_picture.url

          
            elif doctor:
                school_logo_url = doctor.company.logo.url
                school_name = doctor.company.name
            elif employee:
                school_logo_url = employee.company.logo.url
                school_name = employee.company.name
            elif tenant_photo_url:
                school_logo_url = tenant_photo_url
                school_name = tenant_name

        except ProgrammingError:
            pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error in user_info context processor: {e}")

    return {
        'user_info': request.user.username if request.user.is_authenticated else None,
        'profile_picture_url': profile_picture_url,
        'school_logo_url': school_logo_url,
        'school_name': school_name,
    }




def tenant_schema(request):
    schema_name = getattr(request.tenant, 'schema_name', 'public')
    return {'schema_name': schema_name}



def unread_notifications(request):  
    current_client = get_tenant(request)   
    if current_client.schema_name == 'public':
       return {'unread_notifications': []}
    
    if not request.user.is_authenticated:
        return {'unread_notifications': []}

    notifications = Notification.objects.filter(is_read=False)

    filters = Q(user=request.user)

    if request.user.role == "patient":
        patient = Patient.objects.filter(user=request.user).first()
        if patient:
            filters |= Q(patient=patient)

    elif request.user.role == "doctor":
        doctor = Doctor.objects.filter(user=request.user).first()
        if doctor:
            filters |= Q(doctor=doctor)

    notifications = notifications.filter(filters)
    return {'unread_notifications': notifications}
