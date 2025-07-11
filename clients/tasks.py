from celery import shared_task
from django.utils import timezone
from django.utils.timezone import now
from clients.utils import activate_paid_plan  
from django.utils import timezone
from .models import Subscription
from .views import  handle_auto_renewal_success

from django.db.models import Count
import calendar
from django.core.mail import send_mail
from clients.models import Subscription, PaymentProfile, BillingRecord,UserRequestLog,PaymentProfile
from accounts.models import CustomUser
from datetime import timedelta
#from clients.payment_gateway import PaymentGatewayAPI  # Assuming you have this module
PaymentGatewayAPI =None




@shared_task
def check_trial_expiry():
    expired_trials = Subscription.objects.filter(is_trial=True, trial_end_date__lte=now(), is_active=True)

    for subscription in expired_trials:
        activate_paid_plan(subscription.user)  # Start new plan automatically





@shared_task
def check_and_renew_subscriptions():   
    today = now().date()
    subscriptions = Subscription.objects.filter(expiration_date__lte=today)

    for subscription in subscriptions:
        tenant = subscription.tenant
        user = CustomUser.objects.filter(tenant=tenant).first()

        if not user:
            print(f"No user found for tenant {tenant}. Skipping renewal.")
            continue

        try:
            payment_profile = PaymentProfile.objects.get(user=user)
            payment_token = payment_profile.payment_token
        except PaymentProfile.DoesNotExist:
            print(f"No payment profile found for {user}. Cannot auto-renew.")
            continue

        if not subscription.subscription_plan:
            print(f"No subscription plan found for {tenant}. Cannot renew.")
            continue

        bill_details = calculate_monthly_bill(tenant)
        amount = bill_details["total_amount"]
        if amount <= 0:
            print(f"Billing amount is zero for {tenant}. Skipping renewal.")
            continue

        payment_gateway = PaymentGatewayAPI(api_key="your_api_key")
        try:
            charge_response = payment_gateway.charge_card(
                token=payment_token,
                amount=int(amount * 100),
                currency='usd'
            )
            

            if charge_response['status'] == 'success':
                handle_auto_renewal_success(user, subscription.subscription_plan)
                BillingRecord.objects.create(
                    tenant=tenant,
                    amount=amount,
                    billing_date=now(),
                    total_users=bill_details["total_users"],
                    status="Paid"
                )

                send_invoice_email(tenant.owner.email, amount, bill_details)
                print(f" Auto-renewal and billing successful for {tenant} - ${amount}")
            else:
                print(f" Auto-renewal failed for {tenant}")
        except Exception as e:
            print(f"Payment error for {tenant}: {str(e)}")
    return "Subscription renewal check completed!"



def calculate_monthly_bill(client):
    today = now().date()

    subscription = Subscription.objects.get(tenant=client)
    start_date = subscription.start_date  
    billing_cycle_days = 30  


    first_day = start_date 
    last_day = first_day + timedelta(days=billing_cycle_days)  # 30-day cycle

    if today > last_day: 
        first_day = last_day
        last_day = first_day + timedelta(days=billing_cycle_days)

    user_requests = UserRequestLog.objects.filter(
        user__tenant=client,
        timestamp__range=[first_day, last_day]
    ).values('user').annotate(request_count=Count('id'))

    active_users = user_requests.filter(request_count__gte=3).count()
    total_requests = sum(data['request_count'] for data in user_requests)

    base_cost = subscription.subscription_plan.price
    extra_users = max(0, active_users - subscription.subscription_plan.base_users)
    extra_user_charges = extra_users * subscription.subscription_plan.price_per_user
    request_charges = total_requests * subscription.subscription_plan.price_per_request

    total_users = CustomUser.objects.filter(tenant=client, is_active=True).count()

    return {
        "total_amount": base_cost + extra_user_charges + request_charges,
        "active_users": active_users,
        "total_requests": total_requests,
        "extra_user_charges": extra_user_charges,
        "request_charges": request_charges,
        "total_users": total_users,
        "billing_period_start": first_day,
        "billing_period_end": last_day
    }


def send_invoice_email(email, amount, bill_details):
    """Sends an invoice email to the client."""
    subject = f"Subscription Invoice - {now().strftime('%B %Y')}"
    message = f"""
    Hello,
    
    Your subscription invoice for {now().strftime('%B %Y')} is ready.

    Amount: ${amount}
    Total Users: {bill_details['active_users']}
    Total Requests: {bill_details['total_requests']}
    Extra User Charges: ${bill_details['extra_user_charges']}
    Request Charges: ${bill_details['request_charges']}

    Status: Paid

    Thank you for your business.

    Regards,  
    Your Company Name
    """
    send_mail(subject, message, "billing@yourcompany.com", [email])
