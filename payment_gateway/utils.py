import requests
from clients.models import GlobalSMSConfig, TenantSMSConfig
import requests


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






# example of sending sms
def notify_payment(student, guardian, paid_amount):
    tenant = student.user.tenant
    phone_number = guardian.phone_number
    message = f"Dear {guardian.name}, your payment of BDT {paid_amount} has been received. Thank you."

    try:
        send_sms(tenant, phone_number, message)
    except Exception as e:
        print("SMS failed:", e)
