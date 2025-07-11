
from django.db.models import Sum
from .models import Doctor, DoctorServiceLog, DoctorPayment

def get_doctor_financials(doctor_id):
    total_due = DoctorServiceLog.objects.filter(doctor_id=doctor_id).aggregate(
        total=Sum('service_fee')
    )['total'] or 0

    total_paid = DoctorPayment.objects.filter(doctor_id=doctor_id).aggregate(
        total=Sum('total_paid_amount')
    )['total'] or 0

    remaining = total_due - total_paid

    return {
        'total_due': total_due,
        'total_paid': total_paid,
        'remaining': remaining,
    }

