


# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import PatientAdmission
# from billing.models import BillingInvoice

# @receiver(post_save, sender=PatientAdmission)
# def create_or_reuse_admission_invoice(sender, instance, created, **kwargs):
#     if not created:
#         return

#     open_invoice = BillingInvoice.objects.filter(
#         patient=instance.patient,
#         status__in=['Unpaid', 'Partially Paid']
#     ).first()

#     if open_invoice: 
#         open_invoice.admission = instance
#         open_invoice.save()
#     else:
    
#         BillingInvoice.objects.get_or_create(
#             patient=instance.patient,
#             invoice_type = 'IPD',
#             admission=instance
#         )
