# facilities/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import OTBooking
from billing.models import OTBill

@receiver(post_save, sender=OTBooking)
def create_or_update_ot_bill(sender, instance, created, **kwargs):
    if instance.invoice:  # Only create OTBill if linked to an invoice
        ot_bill, bill_created = OTBill.objects.get_or_create(
            ot_booking=instance,
            defaults={
                'invoice': instance.invoice,
                'patient': instance.patient,
                'operation_theatre': instance.operation_theatre,
                'procedure_name': instance.procedure_name,
                'duration_hours': instance.duration_hours(),
                'charge_per_hour': instance.operation_theatre.hourly_rate,
                'total_charge': instance.total_charge,
            }
        )
        if not bill_created:
            # If OTBill already exists, update it
            ot_bill.invoice = instance.invoice
            ot_bill.patient = instance.patient
            ot_bill.operation_theatre = instance.operation_theatre
            ot_bill.procedure_name = instance.procedure_name
            ot_bill.duration_hours = instance.duration_hours()
            ot_bill.charge_per_hour = instance.operation_theatre.hourly_rate
            ot_bill.total_charge = instance.total_charge
            ot_bill.save()

        if ot_bill.invoice:
                ot_bill.invoice.save()
