from django.shortcuts import redirect
from .models import TenantPaymentConfig, PaymentSystem
import requests



def get_payment_gateway(patient):
    tenant = patient.tenant
    payment_config = TenantPaymentConfig.objects.get(tenant=tenant)

    if payment_config.payment_system.method == 'bKash':
        return BkashPaymentGateway(payment_config)
    elif payment_config.payment_system.method == 'Rocket':
        return RocketPaymentGateway(payment_config)
    elif payment_config.payment_system.method == 'CreditCard':
        return CreditCardPaymentGateway(payment_config)
    else:
        raise ValueError("Unsupported payment system")
    


class BkashPaymentGateway:
    def __init__(self, config):
        self.config = config

    def initiate_payment(self, amount):       
        url = "https://api.bkash.com/payment/initiate" 
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        data = {"amount": amount, "merchant_id": self.config.merchant_id}
        response = requests.post(url, json=data, headers=headers)
        return response.json().get("payment_link")

    def verify_payment(self, payment_id):
        url = f"https://api.bkash.com/payment/verify/{payment_id}" 
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            payment_status = data.get("status")
            amount = data.get("amount")  
            return payment_status, amount
        else:
            return "failed", None


class RocketPaymentGateway:
    def __init__(self, config):
        self.config = config

    def initiate_payment(self, amount):

        pass

    def verify_payment(self, payment_id):

        pass


class CreditCardPaymentGateway:
    def __init__(self, config):
        self.config = config

    def initiate_payment(self, amount):

        pass

    def verify_payment(self, payment_id):

        pass



from patients.models import Patient


def initiate_payment(request, patient_id, amount):
    patient = Patient.objects.get(id=patient_id)
    payment_gateway = get_payment_gateway(patient)
    
    payment_link = payment_gateway.initiate_payment(amount)
    
    if payment_link:
        return redirect(payment_link) 
    else:
        return redirect('payment_failure')
    

Payment=None
    
def verify_payment(request, patient_id, payment_id):
    patient = patient.objects.get(id=patient_id)
    payment_gateway = get_payment_gateway(patient)
    
    payment_status, amount = payment_gateway.verify_payment(payment_id)
    
    if payment_status == "success" and amount is not None:
        Payment.objects.create(
            patient=patient, 
            amount=amount, 
            status="Paid"
        )
        return redirect('payment_success')
    else:
        return redirect('payment_failure')


