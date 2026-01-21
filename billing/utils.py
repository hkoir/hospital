
from django.db.models import Sum
from finance.models import AllExpenses
from accounting.service_type import SERVICE_TYPE_TO_REFERRAL_MAP






def get_doctor_financials(doctor_id):
    from billing.models import (
        DoctorServiceLog, DoctorPayment,
        ReferralCommissionTransaction, ReferralPayment,ReferralSource
    )   
    total_referral_due = 0
    total_referral_paid = 0
    remaining_referral_due = 0
 
    total_service_due = DoctorServiceLog.objects.filter(
        doctor_id=doctor_id
    ).aggregate(total=Sum('doctor_share'))['total'] or 0

    total_service_paid = DoctorPayment.objects.filter(
        doctor_id=doctor_id
    ).aggregate(total=Sum('total_paid_amount'))['total'] or 0

    remaining_service_due = total_service_due - total_service_paid
 
    referral_source = ReferralSource.objects.filter(
        internal_doctor_id=doctor_id
    ).first()

    if referral_source:     
        total_referral_due = ReferralCommissionTransaction.objects.filter(
            referral_source=referral_source,
            status="Pending"
        ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
        total_referral_paid = ReferralPayment.objects.filter(
            applied_referrals__referral_source=referral_source
        ).distinct().aggregate(total=Sum('amount_paid'))['total'] or 0

        remaining_referral_due = total_referral_due - total_referral_paid
    else:
        total_referral_due = 0
        total_referral_paid = 0
        remaining_referral_due = 0

    return {
        # service related
        'total_service_due': total_service_due,
        'total_service_paid': total_service_paid,
        'remaining_service_due': remaining_service_due,

        # referral related
        'total_referral_due': total_referral_due,
        'total_referral_paid': total_referral_paid,
        'remaining_referral_due': remaining_referral_due,
    }




def get_applicable_rule(referral_source, service_type):   
    from .models import ReferralSource, ReferralCommissionRule
    service_type = service_type.lower()
    qs = ReferralCommissionRule.objects.filter(referral_source=referral_source, service_type__in=[service_type,'All']).order_by('-id')
    if qs.exists():
        return qs.first()
    if referral_source:
        qs = ReferralCommissionRule.objects.filter(referral_type=referral_source.referral_type, service_type__in=[service_type,'All']).order_by('-id')
        if qs.exists():
            return qs.first()
    return None


def calculate_commission_amount(rule, service_amount):
    if rule is None:
        return 0
    if rule.commission_type == 'percent':
        return (service_amount * rule.value) / 100
    return rule.value



def create_referral_transaction_for_service(
        invoice, 
        service_type, 
        service_id, 
        service_amount,
        referral_source=None):  
    
    from billing.models import ReferralCommissionTransaction
 
     
    referral_source = invoice.patient.referral_source or invoice.referral_source
    if not referral_source:
        return None      
 
    raw_type = service_type    
    mapped_type = SERVICE_TYPE_TO_REFERRAL_MAP.get(raw_type)
    if not mapped_type:       
        return None   
    rule = get_applicable_rule(referral_source, mapped_type)
    if not rule:
        return None   
    
    #if rule.apply_once_per_patient:
     #   already = ReferralCommissionTransaction.objects.filter(
      #  referral_source=referral_source,      
       # service_type=mapped_type,    
        #).exists()
        #if already:
         #   print('this referral already created once. can not create again')
          #  return None   
       
    commission_amount = calculate_commission_amount(rule, service_amount) if rule else 0
    if commission_amount <= 0:
        return None   
     
    tx = ReferralCommissionTransaction.objects.create(
        referral_source=referral_source,
        invoice=invoice,
        service_type=mapped_type,
        service_id=service_id,
        service_amount=service_amount,
        commission_amount=commission_amount,
        status='Pending'
    )   
    return tx



def create_referral_transactions_for_invoice(invoice):   
    from billing.models import ReferralCommissionTransaction  

    referral_source = invoice.patient.referral_source or invoice.referral_source
    if not referral_source:
        return None
    bill_groups = [
        invoice.consultation_bills.all(),
        invoice.lab_test_bills.all(),
        invoice.medicine_bills.all(),
        invoice.ward_bills.all(),
        invoice.ot_bills.all(),
        invoice.misc_bills.all(),
    ]

    for group in bill_groups:
        for bill in group:

            raw_type = bill.service_type 
            service_amount = bill.total_amount
            service_type = SERVICE_TYPE_TO_REFERRAL_MAP.get(raw_type)

            if not service_type:
                print("No referral mapping for", raw_type)
                continue

            rule = get_applicable_rule(referral_source, service_type)
            if not rule:
                continue

            #if rule.apply_once_per_patient:
             #   exists = ReferralCommissionTransaction.objects.filter(
              #      referral_source=referral_source,                    
               #     service_type=service_type,
                #).exists()
                #if exists:
                 #   continue

            commission = calculate_commission_amount(rule, service_amount)
            if commission <= 0:
                continue

            ReferralCommissionTransaction.objects.create(
                referral_source=referral_source,
                invoice=invoice,
                service_type=service_type,
                service_id=bill.id,
                service_amount=service_amount,
                commission_amount=commission,
                status="Pending"
            )           



# ----------------------------------------------------
# Tax and VAT calculation for all models which will be applied at each individual modesl 
# and then aggregate at Billing invoice and at Billing invoice apply a single journal entry 
# with breakdown as revenues,This journal entry is applied at finalize invoice once invoice 
# is locked
#-----------------------------------------------------

from decimal import Decimal, ROUND_HALF_UP

def apply_service_taxes(instance, total_field='test_fee'):
    total = Decimal(getattr(instance, total_field) or 0)
 
    service_type = getattr(instance, 'service_type', None)
    service_policy = None

    if service_type:
        from core.models import ServiceTaxPolicy
        service_policy = ServiceTaxPolicy.objects.filter(
            name=service_type, is_active=True
        ).first()

    if not service_policy:
        from core.models import TaxPolicy
        service_policy = TaxPolicy.objects.filter(is_active=True).first()

    if not service_policy:
        instance.vat_amount = Decimal("0.00")
        instance.ait_amount = Decimal("0.00")
        instance.net_amount = total
        return

    vat_rate = Decimal(service_policy.vat_rate or 0) / 100
    ait_rate = Decimal(service_policy.ait_rate or 0) / 100
    vat_type = (service_policy.vat_type or "").lower()
    ait_type = (service_policy.ait_type or "").lower()

    if vat_type == "inclusive":
        base = total / (1 + vat_rate)
        vat_amount = total - base
        amount_after_vat = base
    elif vat_type == "exclusive":
        vat_amount = total * vat_rate
        amount_after_vat = total + vat_amount
    else:
        vat_amount = Decimal("0")
        amount_after_vat = total

 
    if ait_type == "inclusive":
        base2 = amount_after_vat / (1 + ait_rate)
        ait_amount = amount_after_vat - base2
        amount_after_ait = base2
    elif ait_type == "exclusive":
        ait_amount = amount_after_vat * ait_rate
        amount_after_ait = amount_after_vat + ait_amount
    else:
        ait_amount = Decimal("0")
        amount_after_ait = amount_after_vat

    vat_amount = vat_amount.quantize(Decimal("0.01"), ROUND_HALF_UP)
    ait_amount = ait_amount.quantize(Decimal("0.01"), ROUND_HALF_UP)
    net_amount = amount_after_ait.quantize(Decimal("0.01"), ROUND_HALF_UP)

    instance.vat_amount = vat_amount
    instance.ait_amount = ait_amount
    instance.net_amount = net_amount



