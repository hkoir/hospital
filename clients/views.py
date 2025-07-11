
from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
import requests
from django.conf import settings
from django.http import JsonResponse
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now
from django.db import transaction, connection
from django.core.mail import send_mail
from django.db import IntegrityError

from django_tenants.utils import get_public_schema_name
from accounts.forms import UserProfileForm
from accounts.models import UserProfile
from .models import TenantInfo,Tenant,Client,Domain,SubscriptionPlan, PaymentProfile,Subscription
from .forms import TenantApplicationForm,CreditCardPaymentForm

from .models import DemoRequest
from.forms import DemoRequestForm
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Count
from datetime import datetime, timedelta
from django.utils.timezone import now
from .models import Subscription

CustomUser = get_user_model()
from.models import BillingRecord
from django.core.exceptions import ValidationError





def demo_request(request):
    if request.method == 'POST':
        form = DemoRequestForm(request.POST) 
        if form.is_valid():
            demo_request = form.save()  
            messages.success(request,'Thanks for your interest, we will contact with you soon, in the mean time if you feel to contact with us , please do not hesitate to knock us.')        
            return redirect('clients:dashboard') 
    else:
        form = DemoRequestForm() 
    return render(request, 'tenant/demo_request.html', {'form': form})





def tenant_dashboard(request):  
    print('user=',request.user) 
    
    plans = SubscriptionPlan.objects.all().order_by('duration')
    for plan in plans:
        plan.features_list = plan.features.split(',') if plan.features else [] 

    tenant_links = [
        {'name': 'only_core_dashboard', 'url': reverse('core:only_core_dashboard')},
        {'name': 'home', 'url': reverse('core:home')},
             
    ]
   
    tenant = get_object_or_404(Client, schema_name=request.tenant.schema_name)
    tenant = getattr(request, 'tenant', None)
  
    is_public_schema = tenant.schema_name == get_public_schema_name()
    tenant_schema_name = request.tenant.schema_name
   
  

    if is_public_schema:
        template_name = "tenant/default_dashboard.html"
        context = {
            "welcome_message": "Welcome to the public dashboard",
            'plans':plans,           
            'username':request.user.username

        }
    elif is_public_schema and request.user.is_authenticated:
        template_name = "tenant/default_dashboard.html"
        context = {
            "welcome_message": "Welcome to the public dashboard",
            'plans':plans,           
            'username':request.user.username

        }
    else:
        template_name = "tenant/tenant_dashboard.html"
       
        context = {
            "tenant": tenant,
            "welcome_message": f"Welcome to {tenant.name}'s Dashboard!",
            'tenant_links':tenant_links,
            'plans':plans,      
            'username':request.user.username
        }        
    return render(request, template_name, context)


def public_tenant_login(request):
    return render(request,'tenant/default_dashboard.html')



def tenant_expire_check(request):
    tenant = get_object_or_404(Client, schema_name=request.tenant.schema_name)
    tenant = getattr(request, 'tenant', None)
    is_public_schema = tenant.schema_name == get_public_schema_name()

    tenant = getattr(request, 'tenant', None)
    if tenant:
        tenant_instance = tenant.tenant.first()
        if tenant_instance and tenant_instance.subscription and tenant_instance.subscription.is_expired:
            messages.warning(request,'Your subscription has expired, please renew')
            return redirect('clients:renew_tenant')            

    if not request.user.is_authenticated:       
        return redirect('clients:dashboard')

    else:
        if is_public_schema:
            return redirect('clients:dashboard')
        elif request.user.groups.filter(name='partner').exists():
            return redirect('customerportal:partner_landing_page')
        elif request.user.groups.filter(name='job_seeker').exists():
            return redirect('customerportal:job_landing_page')
        elif request.user.groups.filter(name='public').exists():
             return redirect('customerportal:public_landing_page')
        elif request.user.role=='patient':
             return redirect('visitors:visitor_landing_page')
        else:
            return redirect('core:dashboard')
   


def create_user_profile(request):
    if request.user.is_authenticated:
        user_instance = request.user
        user_profile = UserProfile.objects.filter(user=user_instance).first()
        if request.method == 'POST':
            form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
            if form.is_valid():
                form.save()
                return redirect('clients:dashboard')
        else:
            form = UserProfileForm(instance=user_profile)
    else:
        return redirect('accounts:login')
    return render(request, 'tenant/user_profile.html', {'form': form})




def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


PaymentGatewayAPI=None

def process_payment(payment_token, amount, currency='usd'):
    payment_gateway = PaymentGatewayAPI(api_key="your_api_key")    
    try:
        charge_response = payment_gateway.charge_card(
            token=payment_token,
            amount=amount,
            currency=currency
        )
        
        if charge_response['status'] == 'success':
            return True
        else:
            return False
    except Exception as e:
        return False



@login_required
@login_required
def apply_for_tenant_subscription(request):
    plan_id = request.GET.get('plan_id')
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    tenant = request.tenant
    base_users = int(request.GET.get("users", plan.base_users))
    total_users = CustomUser.objects.filter(tenant=tenant, is_active=True).count()
    amount = plan.calculate_total_cost(total_users)

    if plan.duration != 1:  # Paid plan, requires payment
        try:
            payment_profile = PaymentProfile.objects.get(user=request.user)
            payment_token = payment_profile.payment_token
            amount = plan.price
            currency = 'usd'

            if not process_payment(payment_token, amount, currency):
                messages.error(request, "Payment processing failed. Please try again.")
                return redirect('clients:save_payment_info', plan_id=plan_id)

        except PaymentProfile.DoesNotExist:
            messages.error(request, "Please add a payment method before subscribing to this plan.")
            return redirect('clients:save_payment_info', plan_id=plan_id)

        except Exception as e:
            messages.error(request, f"An error occurred during payment: {e}")
            return redirect('clients:save_payment_info', plan_id=plan_id)
        
    try:
        payment_profile = PaymentProfile.objects.get(user=request.user)
    except PaymentProfile.DoesNotExist:
        return redirect('clients:save_payment_info', plan_id=plan_id)

    if request.method == 'POST':
        form = TenantApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            subdomain = form.cleaned_data['subdomain']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            address = form.cleaned_data['address']
            logo = form.cleaned_data['logo']
            ip_address = get_client_ip(request)

            if Client.objects.filter(schema_name=subdomain).exists():
                messages.error(request, "A tenant with this subdomain already exists.")
                return redirect('clients:dashboard')

            existing_tenant = Tenant.objects.filter(email=email).first()
            if existing_tenant:
                if existing_tenant.subscription.subscription_plan.duration == 1 and existing_tenant.is_trial_used:
                    messages.info(request, "This email has already been used for a trial.")
                    return redirect('clients:dashboard')

            password = '1234567890'

            try:
                with transaction.atomic():
                    tenant = Client.objects.create(schema_name=subdomain, name=subdomain)
                    tenant.registered_tenant = True
                    tenant.save()

                    domain = Domain(domain=f"{subdomain}.localhost", tenant=tenant, is_primary=True)
                    domain.save()

                    # Create user
                    if not request.user.is_authenticated:
                        connection.set_schema(tenant.schema_name)
                        user = CustomUser.objects.create_superuser(
                            username=name,
                            email=email,
                            password=password
                        )
                        user.is_staff = True
                        user.tenant = tenant
                        user.save()
                    else:
                        user = request.user
                        user.email = email
                        user.tenant = tenant
                        user.save()

                    tenant_instance = Tenant.objects.create(
                        ip_address=ip_address,
                        is_trial_used=True,
                        user=user,
                        tenant=tenant,
                        name=name,
                        subdomain=subdomain,
                        email=email,
                        phone_number=phone_number,
                        address=address,
                        logo=logo,
                    )

                    Subscription.objects.create(
                        tenant=tenant_instance,
                        subscription_plan=plan,
                        expiration_date=now().date() + timedelta(days=plan.duration * 30),
                        is_renewal=False,
                        status='active',
                    )

                    send_tenant_email(email, name, password, subdomain)
                    messages.success(request, "Tenant created successfully. Credentials sent to your email.")
                    return redirect(f'http://{subdomain}.localhost:8000/register/')

            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
                return redirect('clients:dashboard')

    else:
        form = TenantApplicationForm()   

    return render(request, 'tenant/apply_for_tenant.html', {'form': form, 'plan': plan})


PaymentGatewayAPI=None

def save_payment_info(request,plan_id):  
  
    plan = get_object_or_404(SubscriptionPlan,id=plan_id)
    if request.method == 'POST':
        form = CreditCardPaymentForm(request.POST)
        if form.is_valid():
            card_number = form.cleaned_data['card_number']
            expiry_date = form.cleaned_data['expiry_date']
            cvv = form.cleaned_data['cvv']     
            card_brand=form.cleaned_data['card_brand']     
            tenant=request.user.tenant

            payment_gateway = PaymentGatewayAPI(api_key="your_api_key")
            try:        
                payment_token = payment_gateway.save_card(
                    card_number=card_number,
                    expiry_date=expiry_date,
                    cvv=cvv,
                    user_id=request.user.id
                )
                card_last4 = card_number[-4:]               
                expiry_month, expiry_year = map(int, expiry_date.split('/'))

                PaymentProfile.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'payment_token': payment_token,
                        'card_last4': card_last4,
                        'card_brand': card_brand,
                        'card_expiry_month': expiry_month,
                        'card_expiry_year': expiry_year,
                        'expiry_date':expiry_date,
                        'cvv':cvv,
                        'tenant':tenant
                    }
                )

                messages.success(request, "Payment information saved successfully!")
                return redirect(reverse('clients:apply_for_tenant') + f"?plan_id={plan_id}")
            except Exception as e:
                messages.error(request, f"Error saving payment information: {str(e)}")
        else:
            messages.error(request, "Invalid payment information. Please try again.")
    else:
        form = CreditCardPaymentForm()    
    return render(request, 'tenant/save_payment_info.html', {'form': form, 'plan_id': plan_id,'plan':plan})



def send_tenant_email(email, username, password, subdomain):
    subject = "Your Tenant Credentials"
    message = (
        f"Welcome to our platform!\n\n"
        f"Your tenant has been created successfully.\n\n"
       
        f"Subdomain: {subdomain}\n"
        f"Login URL: http://{subdomain}.localhost:8000\n\n"
        f"Please register with new username and password and start working"
        f"Thank you for using our service!"
    )
    send_mail(subject, message, 'your-email@example.com', [email])




def handle_auto_renewal_success(user, plan):  
    tenant = user.tenant
    subscription = tenant.subscription

    subscription.expiration_date = now().date() + timedelta(days=30)
    subscription.subscription_plan = plan
    subscription.save()
    print(f"Subscription renewed for {tenant}. Next billing: {subscription.expiration_date}")




def handle_renewal_success(user, plan):  
    tenant = user.tenant
    subscription = tenant.subscription

    total_users = tenant.user_set.count()
    total_cost = plan.price + (total_users * plan.price_per_user)

 
    subscription.expiration_date = timezone.now().date() + timedelta(days=30)
    subscription.subscription_plan = plan
    subscription.save()

    BillingRecord.objects.create(
        tenant=tenant,
        billing_cycle=timezone.now().date(),
        total_users=total_users,
        total_cost=total_cost,
        is_paid=True
    )

    print(f"Subscription renewed for {tenant}. Next billing: {subscription.expiration_date}")



@login_required
def renew_subscription(request):
    current_date = timezone.now().date()
    plan_id = request.GET.get('plan_id')
    user = request.user

    # Fetch Subscription Plan
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    # Get User's Tenant
    user_profile = getattr(user, 'user_profile', None)
    if not user_profile or not user_profile.tenant:
        messages.error(request, "No tenant found for this user.")
        return redirect('clients:dashboard')

    try:
        tenant = Tenant.objects.get(tenant=user_profile.tenant)
    except Tenant.DoesNotExist:
        messages.error(request, "No tenant found for this client.")
        return redirect('clients:dashboard')

    # Fetch the subscription
    try:
        subscription = tenant.subscription
    except Subscription.DoesNotExist:
        messages.error(request, "No subscription found for this tenant.")
        return redirect('clients:apply_for_tenant')

    current_plan = subscription.subscription_plan

    # Allow renewal even if expired
    if subscription.expiration_date < current_date:
        messages.warning(request, "Your subscription has expired. Please renew it now.")

    # Check if user has a saved payment method
    try:
        payment_profile = PaymentProfile.objects.get(user=user)
        payment_token = payment_profile.payment_token
        has_saved_payment = True
    except PaymentProfile.DoesNotExist:
        has_saved_payment = False

    # Handle payment
    if not has_saved_payment:
        if request.method == 'POST':
            form = CreditCardPaymentForm(request.POST)
            if form.is_valid():
                card_number = form.cleaned_data['card_number']
                expiry_date = form.cleaned_data['expiry_date']
                cvv = form.cleaned_data['cvv']

                payment_gateway = PaymentGatewayAPI(api_key="your_api_key")
                try:
                    charge_response = payment_gateway.charge_card(
                        card_number=card_number,
                        expiry_date=expiry_date,
                        cvv=cvv,
                        amount=int(plan.price * 100), 
                        currency='usd'
                    )

                    if charge_response.get('status') == 'success':
                        handle_renewal_success(user, plan)
                        messages.success(request, "Your subscription has been successfully renewed!")
                        return redirect(reverse('clients:dashboard'))
                    else:
                        messages.error(request, "Payment failed. Please try again.")
                except Exception as e:
                    messages.error(request, f"Payment error: {str(e)}")
        else:
            form = CreditCardPaymentForm()

        return render(request, 'tenant/renew_subscription.html', {
            'form': form, 
            'subscription': subscription, 
            'plan': plan,
            'current_date': current_date,
            'current_plan': current_plan
        })

    # Process payment using saved payment method
    payment_gateway = PaymentGatewayAPI(api_key="your_api_key")
    try:
        charge_response = payment_gateway.charge_card(
            token=payment_token,
            amount=int(plan.price * 100), 
            currency='usd'
        )

        if charge_response.get('status') == 'success':
            handle_renewal_success(user, plan)
            messages.success(request, "Your subscription has been successfully renewed!")
            return redirect(reverse('clients:dashboard'))
        else:
            messages.error(request, "Payment failed. Please try again.")
    except Exception as e:
        messages.error(request, f"Payment error: {str(e)}")

    return redirect('clients:renew_subscription')



def thanks_for_application(request):
    rules = TenantInfo.objects.filter(name="Rules and Regulations").first()
    guidelines = TenantInfo.objects.filter(name="Branding Guidelines").first()

    return render(request, 'tenant/thanks_for_application.html', {
        'rules': rules,
        'guidelines': guidelines,
    })

