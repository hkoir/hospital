
from decimal import Decimal
from billing.models import OTBill, DoctorServiceLog
from django.utils import timezone
from .models import OTBookingProcedure



def generate_ot_bills(booking):
    invoice = booking.invoice

    if booking.operation_theatre and booking.booked_start and booking.booked_end:
        ot_charge = Decimal(booking.operation_theatre.hourly_rate or 0) * Decimal(booking.duration_hours())
        OTBill.objects.create(
            invoice=invoice,
            ot_booking=booking,
            service_type="Operation_Theatre",
            total_charge=ot_charge
        )

    procedures = OTBookingProcedure.objects.filter(ot_booking=booking)
    for bp in procedures:
        proc = bp.procedure
        doctor = bp.doctor

        if proc.service_type == "Operation_Theatre":
            continue

        OTBill.objects.create(
            invoice=invoice,
            ot_booking=booking,
            service_type=proc.service_type,
            procedure = bp,
            total_charge=Decimal(proc.rate or 0)
        )  

        DoctorServiceLog.objects.create(
            doctor=bp.procedure.doctor,
            service_type=bp.procedure.service_type,
            surgery_type=getattr(proc, 'surgery_type', None),
            patient=booking.patient,
            service_date=booking.booked_end or timezone.now(),
            invoice=invoice,
            medical_record=invoice.medical_record,
            service_fee=Decimal(proc.rate or 0),
            share_type=proc.share_type,
            doctor_share=proc.doctor_share,
            hospital_share=(Decimal(proc.rate or 0) - proc.doctor_share)
        )

    return True

