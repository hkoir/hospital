from django.core.management.base import BaseCommand
from django.utils.timezone import now
import calendar
from django.core.mail import send_mail
from clients.models import UserRequestLog, Subscription, PaymentProfile, BillingRecord
from accounts.models import CustomUser
from clients.billing.process_payment import process_payment  
from django.db.models import Count



class Command(BaseCommand):
    help = 'Manually process billing for active subscriptions'

    def handle(self, *args, **kwargs):  
      
        subscriptions = Subscription.objects.filter(status='active')

        for subscription in subscriptions:
            tenant = subscription.tenant
            bill_details = self.calculate_monthly_bill(tenant)
            amount = bill_details["total_amount"]

            try:
                payment_profile = PaymentProfile.objects.get(user=tenant.owner)
                payment_token = payment_profile.payment_token
                success = process_payment(payment_token, amount)

                if success:
                    BillingRecord.objects.create(
                        tenant=tenant,
                        amount=amount,
                        billing_date=now(),
                        total_users=bill_details["active_users"],
                        status="Paid"
                    )
                    self.send_invoice_email(tenant.owner.email, amount, bill_details)
                    self.stdout.write(self.style.SUCCESS(f"Billing processed for {tenant} - ${amount}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Billing failed for {tenant}"))
            except PaymentProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"No payment profile found for {tenant}"))




    def calculate_monthly_bill(self, client):
        today = now().date()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        user_requests = UserRequestLog.objects.filter(
            user__tenant=client,
            timestamp__range=[first_day, last_day]
        ).values('user').annotate(request_count=Count('id'))

        active_users = user_requests.filter(request_count__gte=3).count()
        total_requests = sum([data['request_count'] for data in user_requests])

        subscription = Subscription.objects.get(tenant=client)
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
            'total_users':total_users
        }
    



    def send_invoice_email(self, email, amount, bill_details):
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
