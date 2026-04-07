
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse,JsonResponse
from django.db.models import Q

from .forms import UserRegistrationForm,CustomLoginForm,CustomUserCreationForm,ProfilePictureForm
from.models import UserProfile



from django.db import connection
from .forms import TenantUserRegistrationForm

from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db import transaction
from clients.models import Client,SubscriptionPlan

from .forms import AssignPermissionsForm
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.apps import apps
from django.http import JsonResponse
from django.contrib.auth.models import User, Group
from .forms import UserGroupForm
from .forms import AssignPermissionsToGroupForm
from django.core.paginator import Paginator

from django.contrib.auth.models import Group

from django_tenants.utils import schema_context

from .tokens import account_activation_token
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from.models import CustomUser
from django.core.mail import send_mail

from.forms import PartnerJobSeekerRegistrationForm

from clients.models import Subscription
from django.utils import timezone
from django_tenants.utils import get_public_schema_name

from.models import AllowedEmailDomain 
from clients.models import Tenant

from django.contrib.auth import get_user_model
User = get_user_model()




ROOT_DOMAIN = "ecare.support"
from clients.models import Domain

def allow_cert(request):
    domain = request.GET.get("domain")

    if not domain:
        return HttpResponse("Missing domain", status=400)

    domain = domain.lower().strip()

    with schema_context('public'):
        if domain == ROOT_DOMAIN or domain == f"www.{ROOT_DOMAIN}":
            return HttpResponse("OK")

        if domain.endswith("." + ROOT_DOMAIN):
            return HttpResponse("OK")

        if Domain.objects.filter(domain=domain, is_verified=True).exists():
            return HttpResponse("OK")

    return HttpResponse("Not allowed", status=403)

def home(request):
    return render(request,'accounts/home.html')


def send_tenant_email(email, username, password, subdomain):
    subject = "Your Credentials for login"
    message = (
        f"Welcome to our platform!\n\n"
        f"Your account has been created successfully.\n\n"
        f"Username: {username}\n"
        f"Password: {password}\n"
        f"Subdomain: {subdomain}\n"
        f"Login URL: http://{subdomain}.localhost:8000\n\n"
        f"Thank you for using our service!"
    )
    send_mail(subject, message, 'your-email@example.com', [email])






def register_view2(request):   
    current_tenant = None
    current_schema = None

    if hasattr(connection, 'tenant') and connection.tenant:
        current_tenant = connection.tenant
        current_schema = connection.tenant.schema_name   

    if request.method == 'POST':
        registerForm = TenantUserRegistrationForm(request.POST, request.FILES, tenant=current_tenant)

        if registerForm.is_valid():
            with transaction.atomic():  
                user = registerForm.save(commit=False)
                user.email = registerForm.cleaned_data['email']
                email_domain = user.email.split('@')[-1] if '@' in user.email else ''
                user.set_password(registerForm.cleaned_data['password1'])

                if CustomUser.objects.filter(email=user.email).exists():
                    messages.error(request, "This email is already registered.")
                    return render(request, 'accounts/registration/register.html', {'form': registerForm})

                user.is_active = False
                user.tenant = current_tenant
                user.save()

                current_site = get_current_site(request)
                subdomain = current_schema if current_schema != 'public' else ''
                domain = current_site.domain  # e.g., "localhost"

                subject = 'Activate your Account'
                message = render_to_string('accounts/registration/account_activation_email.html', {
                    'user': user,
                    'domain': domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'subdomain': subdomain
                })
                user.email_user(subject=subject, message=message)

                tenant_instance = Client.objects.filter(schema_name=current_tenant.schema_name).first() if current_tenant else None
                UserProfile.objects.create(
                    user=user,
                    tenant=tenant_instance,
                    profile_picture=registerForm.cleaned_data.get('profile_picture'),
                )

                messages.info(request, "Please check your email to activate your account.")
                return render(request, 'accounts/registration/register_email_confirm.html', {'form': registerForm})  
    else:
        registerForm = TenantUserRegistrationForm(tenant=current_tenant)    
    return render(request, 'accounts/registration/register.html', {'form': registerForm})





def register_view(request):
    current_tenant = getattr(connection, 'tenant', None)
    current_schema = current_tenant.schema_name if current_tenant else None

    if request.method == 'POST':
        registerForm = TenantUserRegistrationForm(
            request.POST,
            request.FILES,
            tenant=current_tenant
        )

        if registerForm.is_valid():
            with transaction.atomic():

                user = registerForm.save(commit=False)
                email = (registerForm.cleaned_data.get('email') or "").strip()
                phone = (registerForm.cleaned_data.get('phone_number') or "").strip()
                role = registerForm.cleaned_data['role']
                if role in ['employee', 'corporate-user']:
                    messages.warning(request, 'Please select customer or job seeker role')
                    return redirect('accounts:register')

                user.email = email
                user.phone_number = phone
                user.is_active = False
                user.role = role
                user.tenant = current_tenant
                user.set_password(registerForm.cleaned_data['password1'])
                user.save()

                if not email and not phone:
                    messages.error(request, "You must provide either email or phone number.")
                    user.delete()
                    return render(request, "accounts/registration/register.html", {"form": registerForm})
    
                if phone:
                    try:
                        return send_otp(request, phone)  
                    except Exception as e:
                        messages.error(request, f"Failed to send OTP: {e}")
                        user.delete()
                        return render(request, "accounts/registration/register.html", {"form": registerForm})
     
                if email:
                    try:
                        current_site = get_current_site(request)
                        domain = current_site.domain

                        message = render_to_string(
                            "accounts/registration/account_activation_email.html",
                            {
                                "user": user,
                                "domain": domain,
                                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                                "token": account_activation_token.make_token(user),
                                "subdomain": current_schema if current_schema != "public" else "",
                            }
                        )

                        user.email_user("Activate Your Account", message)
                        messages.info(request, "Please check your email to activate your account.")
                        return render(request, "accounts/registration/register_email_confirm.html")

                    except Exception as e:
                        messages.error(request, f"Email sending failed: {e}")
                        user.delete()
                        return render(request, "accounts/registration/register.html", {"form": registerForm})
    else:
        registerForm = TenantUserRegistrationForm(tenant=current_tenant)
    return render(request, "accounts/registration/register.html", {"form": registerForm})

from django.core.exceptions import ValidationError








def register_patient(request):
    current_tenant = getattr(connection, 'tenant', None)
    current_schema = current_tenant.schema_name if current_tenant else None

    if request.method == 'POST':
        registerForm = TenantUserRegistrationForm(
            request.POST,
            request.FILES,
            tenant=current_tenant
        )

        if registerForm.is_valid():
            with transaction.atomic():

                user = registerForm.save(commit=False)
                email = (registerForm.cleaned_data.get('email') or "").strip()
                phone = (registerForm.cleaned_data.get('phone_number') or "").strip()

                role = registerForm.cleaned_data['role']
                if role not in ['general', 'patient']:
                    messages.warning(request, 'Please select customer or job seeker role')
                    return redirect('accounts:register_patient')

                user.email = email
                user.phone_number = phone
                user.is_active = False
                user.role = role
                user.tenant = current_tenant
                user.set_password(registerForm.cleaned_data['password1'])
                user.save()

                if not email and not phone:
                    messages.error(request, "You must provide either email or phone number.")
                    user.delete()
                    return render(request, "accounts/registration/register.html", {"form": registerForm})
    
                if phone:
                    try:
                        return send_otp(request, phone)  
                    except Exception as e:
                        messages.error(request, f"Failed to send OTP: {e}")
                        user.delete()
                        return render(request, "accounts/registration/register.html", {"form": registerForm})
     
                if email:
                    try:
                        current_site = get_current_site(request)
                        domain = current_site.domain

                        message = render_to_string(
                            "accounts/registration/account_activation_email.html",
                            {
                                "user": user,
                                "domain": domain,
                                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                                "token": account_activation_token.make_token(user),
                                "subdomain": current_schema if current_schema != "public" else "",
                            }
                        )

                        user.email_user("Activate Your Account", message)
                        messages.info(request, "Please check your email to activate your account.")
                        return render(request, "accounts/registration/register_email_confirm.html")

                    except Exception as e:
                        messages.error(request, f"Email sending failed: {e}")
                        user.delete()
                        return render(request, "accounts/registration/register.html", {"form": registerForm})
    else:
        registerForm = TenantUserRegistrationForm(tenant=current_tenant)
    return render(request, "accounts/registration/register.html", {"form": registerForm})




from django.core.exceptions import ValidationError




def register_patient2(request):   
    current_tenant = None
    current_schema = None

    if hasattr(connection, 'tenant') and connection.tenant:
        current_tenant = connection.tenant
        current_schema = connection.tenant.schema_name   

    if request.method == 'POST':
        registerForm = TenantUserRegistrationForm(request.POST, request.FILES, tenant=current_tenant)

        if registerForm.is_valid():
            with transaction.atomic():  
                user = registerForm.save(commit=False)
                user.email = registerForm.cleaned_data['email']
                email_domain = user.email.split('@')[-1] if '@' in user.email else ''
                user.set_password(registerForm.cleaned_data['password1'])

                if CustomUser.objects.filter(email=user.email).exists():
                    messages.error(request, "This email is already registered.")
                    return render(request, 'accounts/registration/register.html', {'form': registerForm})

                user.is_active = False
                user.tenant = current_tenant
                user.role = 'patient'
                user.save()

                current_site = get_current_site(request)
                subdomain = current_schema if current_schema != 'public' else ''
                domain = current_site.domain  # e.g., "localhost"

                subject = 'Activate your Account'
                message = render_to_string('accounts/registration/account_activation_email.html', {
                    'user': user,
                    'domain': domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'subdomain': subdomain
                })
                user.email_user(subject=subject, message=message)

                tenant_instance = Client.objects.filter(schema_name=current_tenant.schema_name).first() if current_tenant else None
                UserProfile.objects.create(
                    user=user,
                    tenant=tenant_instance,
                    profile_picture=registerForm.cleaned_data.get('profile_picture'),
                )

                messages.info(request, "Please check your email to activate your account.")
                return render(request, 'accounts/registration/register_email_confirm.html', {'form': registerForm})  
    else:
        registerForm = TenantUserRegistrationForm(tenant=current_tenant)    
    return render(request, 'accounts/registration/register.html', {'form': registerForm})




from patients.forms import DirectPatientForm

@login_required
def direct_patient_registration(request):   
    current_tenant = None

    if hasattr(connection, 'tenant') and connection.tenant:
        current_tenant = connection.tenant

    if request.method == 'POST':
        registerForm = TenantUserRegistrationForm(request.POST, request.FILES, tenant=current_tenant)
        patient_form = DirectPatientForm(request.POST)

        if registerForm.is_valid() and patient_form.is_valid():
            with transaction.atomic():          
                user = registerForm.save(commit=False)
                email = registerForm.cleaned_data.get('email')
                password = registerForm.cleaned_data.get('password1')
 
                if CustomUser.objects.filter(email=email).exists():
                    messages.error(request, "This email is already registered.")
                    return render(
                        request,
                        'accounts/registration/direct_patient_register.html',
                        {'form': registerForm, 'patient_form': patient_form} )

                user.email = email
                user.set_password(password)
                user.tenant = current_tenant
                user.role = 'patient'
                user.is_active = True
                user.is_phone_verified = True if user.phone_number else False
                user.is_email_verified = True if user.email else False
                user.save()

                patient = patient_form.save(commit=False)
                patient.user = user
                patient.email = user.email
                patient.save() 

                tenant_instance = Client.objects.filter(id=current_tenant.id).first()                
                UserProfile.objects.create(
                    user=user,
                    tenant=tenant_instance,
                    profile_picture=registerForm.cleaned_data.get('photo_id'))

                messages.success(request, "User and patient account created successfully.")
                return redirect('workspace:staff_dashboard')
    else:
        registerForm = TenantUserRegistrationForm(tenant=current_tenant)
        patient_form = DirectPatientForm()

    return render(
        request,
        'accounts/registration/direct_patient_register.html',
        {'form': registerForm, 'patient_form': patient_form}
    )




from.forms import PublicRegistrationForm


def register_public(request):
    current_tenant = getattr(connection, 'tenant', None)
    current_schema = current_tenant.schema_name if current_tenant else None

    if request.method == 'POST':
        registerForm = TenantUserRegistrationForm(
            request.POST,
            request.FILES,
            tenant=current_tenant
        )

        if registerForm.is_valid():
            with transaction.atomic():

                user = registerForm.save(commit=False)
                email = (registerForm.cleaned_data.get('email') or "").strip()
                phone = (registerForm.cleaned_data.get('phone_number') or "").strip()

                role = registerForm.cleaned_data['role']
                if role not in ['general', 'patient']:
                    messages.warning(request, 'Please select customer or job seeker role')
                    return redirect('accounts:register_patient')

                user.email = email
                user.phone_number = phone
                user.is_active = False
                user.role = role
                user.tenant = current_tenant
                user.set_password(registerForm.cleaned_data['password1'])
                user.save()

                if not email and not phone:
                    messages.error(request, "You must provide either email or phone number.")
                    user.delete()
                    return render(request, "accounts/registration/register.html", {"form": registerForm})
    
                if phone:
                    try:
                        return send_otp(request, phone)  
                    except Exception as e:
                        messages.error(request, f"Failed to send OTP: {e}")
                        user.delete()
                        return render(request, "accounts/registration/register.html", {"form": registerForm})
     
                if email:
                    try:
                        current_site = get_current_site(request)
                        domain = current_site.domain

                        message = render_to_string(
                            "accounts/registration/account_activation_email.html",
                            {
                                "user": user,
                                "domain": domain,
                                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                                "token": account_activation_token.make_token(user),
                                "subdomain": current_schema if current_schema != "public" else "",
                            }
                        )

                        user.email_user("Activate Your Account", message)
                        messages.info(request, "Please check your email to activate your account.")
                        return render(request, "accounts/registration/register_email_confirm.html")

                    except Exception as e:
                        messages.error(request, f"Email sending failed: {e}")
                        user.delete()
                        return render(request, "accounts/registration/register.html", {"form": registerForm})
    else:
        registerForm = TenantUserRegistrationForm(tenant=current_tenant)
    return render(request, "accounts/registration/register.html", {"form": registerForm})




def account_activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)  
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None  

    if user and account_activation_token.check_token(user, token):

        if user.tenant.schema_name == "public":
            user.is_active = True
            user.is_staff = False    
            user.is_email_verified = True
       
        elif user.role in ['general','patient']:
            user.is_active = True 
            user.is_staff = False
            user.is_email_verified = True
        else:
            user.is_active = True 
            user.is_staff = True  
            user.is_email_verified = True

        user.save()
        messages.success(request, "Your account has been activated! You can work now.")
        login(request, user, backend='accounts.backends.TenantAuthenticationBackend')
        return redirect('clients:tenant_expire_check')

    return render(request, 'accounts/registration/activation_invalid.html')





def login_view(request):
    current_schema = None

    if hasattr(connection, 'tenant'):
        current_tenant = connection.tenant
        current_schema = current_tenant.schema_name
     
        current_date = timezone.now().date()
        subscriptions = Subscription.objects.all()

        for subscription in subscriptions:
            if subscription.expiration_date:
                if subscription.expiration_date < current_date:
                    subscription.is_expired = True
                    subscription.save()

  
    form = CustomLoginForm(initial={'tenant': current_schema})

    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user, backend='accounts.backends.TenantAuthenticationBackend')

                protocol = "https" if request.is_secure() else "http"
                host = request.get_host()
             
                is_public = request.tenant.schema_name == get_public_schema_name()
              
                if "localhost" in host or "127.0.0.1" in host:
                    tenant_url = f"{protocol}://{host}/clients/tenant_expire_check/"
              
                else:
                    tenant_domain = request.tenant.domain_url
                    tenant_url = f"{protocol}://{tenant_domain}/clients/tenant_expire_check/"

                messages.success(request, "Login successful!")
                return redirect(tenant_url)

            else:
                messages.error(request, "Invalid username or password.")

        else:
            messages.error(request, "Please provide correct username and password")

    # Reload form safely
    form = CustomLoginForm(initial={'tenant': current_schema})

    return render(request, 'accounts/registration/login.html', {'form': form})




from django.utils.crypto import constant_time_compare
from accounts.utils import send_sms   
from .models import PhoneOTP


def send_otp(request, phone_number):
    if not phone_number:
        return render(request, "accounts/registration/register.html", {"error": "Phone number required."})

    otp_obj, _ = PhoneOTP.objects.get_or_create(phone_number=phone_number)
    otp_obj.generate_otp()

    message = f"Your verification code is: {otp_obj.otp}"
    try:
        send_sms(tenant=getattr(request, "tenant", None), phone_number=phone_number, message=message)
        print(f'your otp code is {otp_obj.otp}')
    except Exception as e:
        return render(request, "accounts/registration/register.html", {"error": f"SMS failed: {e}"})

    return render(request, "accounts/otp_registration/verify_otp.html", {
        "phone": phone_number,
        "valid_until": otp_obj.valid_until,
    })




def verify_otp(request):
    phone = request.POST.get("phone")
    otp_input = request.POST.get("otp")
    current_tenant = None    
    if hasattr(connection, 'tenant'):       
        current_tenant_schema = connection.tenant.schema_name   
        current_tenant = request.tenant  #current_tenant = request.user.tenant # from model     


    if not phone or not otp_input:
        return render(request, "accounts/otp_registration/verify_otp.html", {
            "error": "Phone number and OTP are required.",
            "phone": phone
        })

    otp_entry = PhoneOTP.objects.filter(phone_number=phone).first()
    if not otp_entry:
        return render(request, "accounts/otp_registration/verify_otp.html", {
            "error": "OTP not found.",
            "phone": phone
        })

    if constant_time_compare(otp_entry.otp, otp_input) and timezone.now() <= otp_entry.valid_until:
        otp_entry.is_verified = True
        otp_entry.save()

        user = CustomUser.objects.filter(phone_number=phone).first()
        if user:
            if user.tenant.schema_name == "public":
                user.is_staff = False               
                user.tenant = current_tenant
            else:
                if user.role in ['patient','general'] :               
                    user.is_staff =False
                else:
                    user.is_staff = True

            user.is_phone_verified = True
            user.is_active = True               
            user.tenant = current_tenant
            user.save()
            login(request, user, backend='accounts.backends.TenantAuthenticationBackend')           
            messages.success(request, "Phone number verified successfully. You can now log in.")
            return redirect("clients:tenant_expire_check")
        else:
            return render(request, "accounts/otp_registration/verify_otp.html", {
                "error": "No user found for this phone number.",
                "phone": phone
            })
    else:
        return render(request, "accounts/otp_registration/verify_otp.html", {
            "error": "Invalid or expired OTP.",
            "phone": phone
        })




def send_password_reset_otp(request):
    if request.method == "POST":
        phone_number = request.POST.get("phone")
        if not phone_number:
            return render(request, "accounts/otp_registration/forgot_password.html", {"error": "Phone number required."})
        otp_obj, _ = PhoneOTP.objects.get_or_create(phone_number=phone_number, purpose='forgot_password')
        otp_obj.generate_otp()
        message = f"Your password reset OTP is: {otp_obj.otp}"
        try:
            send_sms(tenant=getattr(request, "tenant", None), phone_number=phone_number, message=message)
            print(f"OTP for forgot password: {otp_obj.otp}")
        except Exception as e:
            return render(request, "accounts/otp_registration/forgot_password.html", {"error": f"SMS failed: {e}"})
        # Store phone in session to identify user in verification step
        request.session['reset_phone_number'] = phone_number
        return render(request, "accounts/otp_registration/verify_reset_otp.html", {
            "phone": phone_number,
            "valid_until": otp_obj.valid_until
        })
    return render(request, "accounts/otp_registration/forgot_password.html")



def verify_password_reset_otp(request):
    if request.method == "POST":
        phone = request.session.get("reset_phone_number")
        otp_input = request.POST.get("otp")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        if not phone or not otp_input or not new_password or not confirm_password:
            return render(request, "accounts/otp_registration/verify_reset_otp.html", {
                "error": "All fields are required.",
                "phone": phone
            })
        otp_entry = PhoneOTP.objects.filter(phone_number=phone, purpose='forgot_password').first()
        if not otp_entry:
            return render(request, "accounts/otp_registration/verify_reset_otp.html", {
                "error": "OTP not found.",
                "phone": phone
            })
        if constant_time_compare(otp_entry.otp, otp_input) and timezone.now() <= otp_entry.valid_until:
            if new_password != confirm_password:
                return render(request, "accounts/otp_registration/verify_reset_otp.html", {
                    "error": "Passwords do not match.",
                    "phone": phone
                })
            user = User.objects.filter(phone_number=phone).first()
            if user:
                user.set_password(new_password)
                user.save()
                otp_entry.is_verified = True
                otp_entry.save()
                messages.success(request, "Password reset successful. You can now log in.")
                # Clean session
                if 'reset_phone_number' in request.session:
                    del request.session['reset_phone_number']
                return redirect("accounts:login")
            else:
                return render(request, "accounts/otp_registration/verify_reset_otp.html", {
                    "error": "No user found for this phone number.",
                    "phone": phone
                })
        else:
            return render(request, "accounts/otp_registration/verify_reset_otp.html", {
                "error": "Invalid or expired OTP.",
                "phone": phone
            })
    return render(request, "accounts/otp_registration/verify_reset_otp.html")



@login_required
def send_change_password_otp(request):
    phone_number = request.user.phone_number
    otp_obj, _ = PhoneOTP.objects.get_or_create(phone_number=phone_number, purpose='change_password')
    otp_obj.generate_otp()
    message = f"Your OTP to change password is: {otp_obj.otp}"
    send_sms(tenant=getattr(request, "tenant", None), phone_number=phone_number, message=message)
    messages.success(request, "OTP sent to your phone. Please enter it to change password.")
    return redirect("accounts:verify_change_password_otp")




@login_required
def verify_change_password_otp(request):
    if request.method == "POST":
        phone = request.user.phone_number
        otp_input = request.POST.get("otp")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")
        otp_entry = PhoneOTP.objects.filter(phone_number=phone, purpose='change_password', is_verified=False).last()
        if otp_entry and constant_time_compare(otp_entry.otp, otp_input) and timezone.now() <= otp_entry.valid_until:
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("accounts:verify_change_password_otp")
            request.user.set_password(new_password)
            request.user.save()
            otp_entry.is_verified = True
            otp_entry.save()
            messages.success(request, "Password changed successfully!")
            login(request, request.user, backend='accounts.backends.TenantAuthenticationBackend')
            return redirect("core:dashboard")
        else:
            messages.error(request, "Invalid or expired OTP.")
            return redirect("verify_change_password_otp")
    return render(request, "accounts/otp_registration/verify_change_password_otp.html")






@login_required
def update_profile_picture(request): 
    if not request.user.is_authenticated:
        return redirect('core:home') 

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)

    profile_picture_url = user_profile.profile_picture.url if user_profile.profile_picture else None
    user_info = request.user.get_full_name() or request.user.username

    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            if request.user.groups.filter(name__in=('Customer','public','job_seekers')).exists():
                return redirect('clients:dashboard')  
            else:
                messages.success(request, "Login successful!")
                return redirect('core:dashboard')    
        else:
            messages.error(request,'there is an error in form')   
            print(form.errors)    
    else:
        form = ProfilePictureForm(instance=user_profile)

    return render(
        request, 
        'accounts/change_profile_picture.html', 
        {'form': form, 'user_info': user_info, 'profile_picture_url': profile_picture_url}
    )







def logged_out_view(request):
    plans = SubscriptionPlan.objects.all().order_by('duration')
    for plan in plans:
        plan.features_list = plan.features.split(',')
        
    is_partner_job_seeker = False    
    is_public = False

    if request.user.is_authenticated:        
        is_partner_job_seeker = request.user.groups.filter(name__in=('partner','job_seeker')).exists()       
        is_public = request.user.groups.filter(name='public').exists()
       
    logout(request)     
    return render(request, 'accounts/registration/logged_out.html',{'plans':plans})






def assign_model_permission_to_user(user, model_name, permission_codename): 
    try:
        app_label, model_label = model_name.split('.')
        model = apps.get_model(app_label, model_label)
        content_type = ContentType.objects.get_for_model(model)
        permission = Permission.objects.get(codename=permission_codename, content_type=content_type)

        user.user_permissions.add(permission)
        user.save()
        
        return f"Permission '{permission_codename}' successfully assigned to {user.username}."
    except Permission.DoesNotExist:
        return f"Permission '{permission_codename}' does not exist for the model '{model_name}'."
    except Exception as e:
        return f"An error occurred: {e}"



@login_required
def assign_permissions(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to assign roles.")
        return redirect('core:home')

    if request.method == 'POST':
        form = AssignPermissionsForm(request.POST)
        if form.is_valid():
            try:
               
                selected_permissions = form.cleaned_data['permissions']
                model_name = form.cleaned_data['model_name']   
                email = form.cleaned_data['email']  
                user = CustomUser.objects.get(email=email)
                     

                cleaned_model_name = model_name.strip("[]").strip("'\"")
                
                user = CustomUser.objects.get(email=email)
                
                for permission_codename in selected_permissions:
                    cleaned_codename = permission_codename.strip("[]").strip("'\"")                    

                    message = assign_model_permission_to_user(user, cleaned_model_name, cleaned_codename)
                    messages.success(request, message)
                
                return redirect('accounts:assign_permissions')
            except Permission.DoesNotExist:
                messages.error(request, f"Permission '{permission_codename}' does not exist.")
            except Exception as e:
                print(e)
                messages.error(request, f"An error occurred: {e}")
        else:
            print(form.errors)
    else:
        form = AssignPermissionsForm()

    users = CustomUser.objects.all().order_by('-date_joined')
    paginator = Paginator(users,8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/assign_permission.html', {'form': form, 'users': users,'page_obj':page_obj})



@login_required
def assign_user_to_group(request):
    group_data = Group.objects.all()

    if request.method == 'POST':
        form = UserGroupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email'] 
            group = form.cleaned_data['group']
            new_group_name = form.cleaned_data['new_group_name']

            try:
                user = CustomUser.objects.get( email=email)
            except User.DoesNotExist:
                messages.error(request, f"User '{username}' does not exist.")
                return redirect('accounts:assign_user_to_group')

            if group:
                user.groups.add(group)
                messages.success(request, f"User '{email}' was added to the existing group '{group.name}'.")
            elif new_group_name:
                group, created = Group.objects.get_or_create(name=new_group_name)
                user.groups.add(group)
                if created:
                    messages.success(request, f"Group '{new_group_name}' was created and '{username}' was added to it.")
                else:
                    messages.success(request, f"User '{username}' was added to the existing group '{new_group_name}'.")
            
            user.save()
            return redirect('accounts:assign_user_to_group')
    else:
        form = UserGroupForm()
    return render(request, 'accounts/assign_user_to_group.html', {'form': form,'group_data':group_data})




def assign_permissions_to_group(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to assign roles.")
        return redirect('core:home')

    group_name = None
    assigned_permissions = []
    group_data = Group.objects.all() 

    if request.method == 'POST':
        form = AssignPermissionsToGroupForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data['group']
            model_name = form.cleaned_data['model_name']
            selected_permissions = form.cleaned_data['permissions']

            try:
                model_class = apps.get_model(*model_name.split('.'))
                content_type = ContentType.objects.get_for_model(model_class)

                for permission in selected_permissions:
                    if permission.content_type == content_type:
                        group.permissions.add(permission)

                group_name = group.name
                assigned_permissions = group.permissions.select_related('content_type').all() 
                messages.success(request, f"Permissions successfully assigned to the group '{group.name}'.")
                return redirect('accounts:assign_permissions_to_group')

            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            print(form.errors)
    else:
        form = AssignPermissionsToGroupForm()

    groups_info = []
    for group in group_data:
        users_in_group = group.user_set.all() 
        permissions_in_group = group.permissions.select_related('content_type').all()  
        groups_info.append({
            'group': group,
            'users': users_in_group,
            'permissions': permissions_in_group
        })

    return render(
        request,
        'accounts/assign_permissions_to_group.html',
        {
            'form': form,
            'group_name': group_name,
            'assigned_permissions': assigned_permissions,
            'groups_info': groups_info,  # Pass the group data to the template
        }
    )



# for ajax
def get_permissions_for_model(request):
    model_name = request.GET.get('model_name', '')    
    try:
        app_label, model_name = model_name.split('.')
        model_class = apps.get_model(app_label, model_name)   
        content_type = ContentType.objects.get_for_model(model_class) 
        permissions = Permission.objects.filter(content_type=content_type)
        permission_data = [
            {'id': perm.id, 'name': perm.name, 'codename': perm.codename}
            for perm in permissions
        ]        
        return JsonResponse({'permissions': permission_data})    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


from core.models import Employee
from product.models import Product,Category,ProductType
from medical_records.models import Prescription


from purchase.models import PurchaseOrder,PurchaseRequestOrder
from logistics.models import PurchaseShipment
from finance.models import PurchaseInvoice,PurchasePayment



def common_search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:


        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(product_code__icontains=query) |
            Q(sku__icontains=query)
        ).values('id', 'name', 'product_code', 'sku')

        results.extend([
            {
                'id': prod['id'], 
                'text': f"{prod['name']} ({prod['product_code'] or prod['sku']})"
            }
            for prod in products
        ])

        # 🔹 Category search (by name or category_id)
        categories = Category.objects.filter(
            Q(name__icontains=query) | 
            Q(category_id__icontains=query)
        ).values('id', 'name', 'category_id')

        results.extend([
            {
                'id': cat['id'], 
                'text': f"{cat['name']} ({cat['category_id']})"
            }
            for cat in categories
        ])


        employees = Employee.objects.filter(
            Q(name__icontains=query) | Q(employee_code__icontains=query)
        ).values('id', 'name', 'employee_code')
        results.extend([
            {'id': emp['id'], 'text': f"{emp['name']} ({emp['employee_code']})"}
            for emp in employees
        ])   

        purchase_orders = PurchaseOrder.objects.filter(
            Q(order_id__icontains=query)
        ).values('id', 'order_id')
        results.extend([
            {'id': data['id'], 'text': f"{data['order_id']}"}
            for data in purchase_orders
        ])   

        purchase_request_orders = PurchaseRequestOrder.objects.filter(
            Q(order_id__icontains=query)
        ).values('id', 'order_id')
        results.extend([
            {'id': data['id'], 'text': f"{data['order_id']}"}
            for data in purchase_request_orders
        ])   

        
        purchase_shipment_orders = PurchaseShipment.objects.filter(
            Q(shipment_id__icontains=query)
        ).values('id', 'shipment_id')
        results.extend([
            {'id': data['id'], 'text': f"{data['shipment_id']}"}
            for data in purchase_shipment_orders
        ])       


        purchase_invoice_numbers = PurchaseInvoice.objects.filter(
            Q(invoice_number__icontains=query)
        ).values('id', 'invoice_number')
        results.extend([
            {'id': data['id'], 'text': f"{data['invoice_number']}"}
            for data in purchase_invoice_numbers
        ])  

        employees = Employee.objects.filter(
            Q(name__icontains=query) | Q(employee_code__icontains=query)
        ).values('id', 'name', 'employee_code')
        results.extend([
            {'id': emp['id'], 'text': f"{emp['name']} ({emp['employee_code']})"}
            for emp in employees
        ]) 

        medications = Product.objects.filter(
            Q(name__icontains=query) | Q(product_code__icontains=query)
        ).values('id', 'name', 'product_code')
        results.extend([
            {'id': prod['id'], 'text': f"{prod['name']} ({prod['product_code']})"}
            for prod in medications
        ])

        medication_categories = Category.objects.filter(
            Q(name__icontains=query)
        ).values('id', 'name')
        results.extend([
            {'id': prod['id'], 'text': f"{prod['name']}"}
            for prod in medication_categories 
        ])

     

    return JsonResponse({'results': results})



@login_required
def search_all(request):
    query = request.GET.get('q')
   
    employees = Employee.objects.filter(
        Q(name__icontains=query) | 
        Q(employee_code__icontains=query) | 
        Q(email__icontains=query) | 
        Q(phone__icontains=query) | 
        Q(position__name__icontains=query) | 
        Q(department__name__icontains=query)
    )

  



    return render(request, 'accounts/search_results.html', {
        'employees': employees, 
      
        'query': query,
        
    })
