from django.utils.timezone import now, timedelta
from .models import Subscription, SubscriptionPlan 

def activate_paid_plan(user):

    subscription = Subscription.objects.filter(user=user, is_active=True).first()
    
    if subscription and subscription.is_expired():
        try:     
            default_plan = SubscriptionPlan.objects.get(duration=6) 
        except SubscriptionPlan.DoesNotExist:
            return 

    subscription, created = Subscription.objects.get_or_create(user=user)

    subscription.subscription_plan = default_plan
    subscription.is_trial = False
    subscription.start_date = now()
    subscription.next_billing_date = now() + timedelta(days=(default_plan.duration * 30))  # Convert months to days
    subscription.save()
