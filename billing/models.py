
from django.db import models
from inventory.models import Medicine
from product.models import Product
from lab_tests.models import LabTest,LabTestCatalog,LabTestRequestItem,SuggestedLabTestItem
from core.models import Doctor
from django.db.models import Sum, F, ExpressionWrapper, DecimalField,Max
from django.utils import timezone
from decimal import Decimal
from django.db import models
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from django.db import models, IntegrityError
from datetime import datetime
from math import ceil
from medical_records.models import MedicalRecord
from accounts.models import CustomUser

from decimal import Decimal, ROUND_HALF_UP
from django.utils.timezone import is_naive, make_aware
from django.utils.timezone import now as tz_now
import random 

from decimal import Decimal
from accounting.service_type import SERVICE_TYPE_CHOICES




class ReferralSource(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='referer_users', null=True, blank=True)
    REFERRAL_TYPES = [
        ('internal_doctor', 'Internal Doctor'),
        ('external_doctor', 'External Doctor'),
        ('agent', 'Marketing Agent'),
        ('hospital', 'Hospital/Clinic'),
        ('self', 'Self/Walk-in'),
        ('other', 'Other'),
    ]

    referral_type = models.CharField(max_length=30, choices=REFERRAL_TYPES, blank=True, null=True)
    internal_doctor = models.ForeignKey(Doctor, null=True, blank=True, on_delete=models.SET_NULL)    
    external_name = models.CharField(max_length=255, blank=True, null=True)
    external_contact = models.CharField(max_length=100, blank=True, null=True)
    agent_name = models.CharField(max_length=255, blank=True, null=True)
    agent_phone = models.CharField(max_length=100, blank=True, null=True)
    hospital_name = models.CharField(max_length=255, blank=True, null=True)
    hospital_contact = models.CharField(max_length=100, blank=True, null=True)
    referral_code = models.CharField(max_length=50, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = generate_unique_referral_code(length=6)  
        super().save(*args, **kwargs)
            

    def __str__(self):
        return f"{self.name} ({self.referral_code})"
    

    def __str__(self):
        if self.internal_doctor:
            return self.internal_doctor.name
        if self.external_name:
            return self.external_name
        if self.agent_name:
            return self.agent_name
        if self.hospital_name:
            return self.hospital_name
        return f"{self.get_referral_type_display()}"
    
    def display_name(self):
        if self.referral_type == 'internal_doctor' and self.internal_doctor:
            return f"Dr. {self.internal_doctor.name} (Internal Doctor)"
        elif self.referral_type == 'external_doctor' and self.external_name:
            return f"{self.external_name} (External Referral)"
        elif self.referral_type == 'agent' and self.agent_name:
            return f"{self.agent_name} (Agent)"
        elif self.referral_type == 'hospital' and self.hospital_name:
            return f"{self.hospital_name} (Hospital/Clinic)"
        else:
            return self.referral_type or "Unknown"
    

def generate_unique_referral_code(length=6):
    while True:
        code = str(random.randint(10**(length-1), 10**length - 1))
        if not ReferralSource.objects.filter(referral_code=code).exists():
            return code




class BillingInvoice(models.Model):
    referral_source = models.ForeignKey(
        ReferralSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referral_source_invoices')
    invoice_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    medical_record = models.OneToOneField(MedicalRecord, null=True, blank=True, on_delete=models.SET_NULL, related_name='billing_invoice_records')
    admission = models.OneToOneField('patients.PatientAdmission', on_delete=models.CASCADE, null=True, blank=True, related_name="billing_admission")
    #appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE, null=True, blank=True, related_name="appointment_invoices")
    INVOICE_TYPE = [
         ('', 'All'),
        ('OPD', 'Outpatient'),
        ('IPD', 'Inpatient'),
        ('Emergency', 'Emergency'),
        ('External-Lab-Test', 'External Lab Test patient'),
        ('Medicine-Sale-Only', 'Medicine Sale Only'),
        ('Other-Services', 'Other services'),
    ]
    invoice_type = models.CharField(max_length=50, choices=INVOICE_TYPE, default='OPD')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='patient_billing',null=True,blank=True)   
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency'),
        ('Medicine-Only','Medicine Only'),
        ('Other-Services', 'Other services'),
        ],null=True,blank=True) 
    service_type =  models.CharField(max_length=50,choices=SERVICE_TYPE_CHOICES,null=True,blank=True),
     
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid')],
        default='Unpaid'
    )
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(auto_now=True,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)   

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            self.invoice_id = self.generate_unique_invoice_id()
        if self.pk:
            child_aggregates = {
                'vat': Decimal('0.00'),
                'ait': Decimal('0.00'),
                'net': Decimal('0.00'),
                'total': Decimal('0.00'),
            }

            for rel in ['consultation_bills', 'lab_test_bills', 'medicine_bills', 
                        'ward_bills', 'ot_bills', 'misc_bills']:
                agg = getattr(self, rel).aggregate(
                    total=Sum('total_amount') if rel != 'lab_test_bills' else Sum('test_fee'),
                    vat_sum=Sum('vat_amount'),
                    ait_sum=Sum('ait_amount'),
                    net_sum=Sum('net_amount')
                )
                child_aggregates['total'] += Decimal(agg.get('total') or 0)
                child_aggregates['vat'] += Decimal(agg.get('vat_sum') or 0)
                child_aggregates['ait'] += Decimal(agg.get('ait_sum') or 0)
                child_aggregates['net'] += Decimal(agg.get('net_sum') or 0)

            self.total_amount = child_aggregates['total'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.vat_amount = child_aggregates['vat'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.ait_amount = child_aggregates['ait'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.net_amount = child_aggregates['net'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            self.remaining_amount = (Decimal(self.total_amount) - Decimal(self.total_paid or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            if self.total_amount <= 0 or (self.total_paid or 0) <= 0:
                self.status = 'Unpaid'
            elif self.total_paid >= self.total_amount:
                self.status = 'Paid'
            else:
                self.status = 'Partially Paid'

        super().save(*args, **kwargs)

    def all_medicine_delivered(self):       
        items = self.medicine_bills.all()          
        for item in items:            
            if not item or item.status != "Delivered":
                return False
        return True

    def generate_unique_invoice_id(self):
        last_invoice = BillingInvoice.objects.aggregate(Max('invoice_id'))['invoice_id__max']
        if last_invoice:
            last_invoice_number = int(last_invoice.split('-')[-1])
            new_invoice_number = last_invoice_number + 1
        else:
            new_invoice_number = 1
        return f"INV-{timezone.now().year}-{str(new_invoice_number).zfill(4)}"

    def get_all_bill_items(self):
        bill_items = []

        for item in self.consultation_bills.all():
            bill_items.append({
                "amount": item.consultation_fee,
                "revenue_type": "Consultation"
            })

        for item in self.medicine_bills.all():
            bill_items.append({
                "amount": item.quantity * item.price_per_unit,
                "revenue_type": "Medicine"
            })

        for item in self.lab_test_bills.all():
            bill_items.append({
                "amount": item.lab_test.price if item.lab_test else 0.0,
                "revenue_type": "Lab"
            })

        for item in self.ot_bills.all():
            bill_items.append({
                "amount": item.total_charge,
                "revenue_type": "OT"
            })

        for item in self.ward_bills.all():
            bill_items.append({
                "amount": item.total_bill,
                "revenue_type": "Ward"
            })

        if hasattr(self, "miscellaneous_bills"):
            for item in self.miscellaneous_bills.all():
                bill_items.append({
                    "amount": item.amount,
                    "revenue_type": "Miscellaneous"
                })

        return bill_items



    def calculate_total_paid_amount(self):
        return self.payments.aggregate(total=Sum('amount_paid'))['total'] or 0   

    def calculate_total(self):
        consultation_total = Decimal(self.consultation_bills.aggregate(
            total=Sum('consultation_fee'))['total'] or 0)
        
        lab_total = Decimal(self.lab_test_bills.aggregate(
            total=Sum('test_fee'))['total'] or 0)

        medicine_total = Decimal(self.medicine_bills.aggregate(
            total=Sum(ExpressionWrapper(
                F('quantity') * F('price_per_unit'),
                output_field=DecimalField()))
        )['total'] or 0)

        ward_total = Decimal(self.ward_bills.aggregate(
            total=Sum('total_bill'))['total'] or 0)

        ot_total = Decimal(self.ot_bills.aggregate(
            total=Sum('total_charge'))['total'] or 0)      

        misc_total = Decimal(self.misc_bills.aggregate(
            total=Sum('amount'))['total'] or 0)

        total = consultation_total + lab_total + medicine_total + ward_total + ot_total + misc_total
        print(f"[Invoice {self.id}] Calculated total = {total}")
        return total

    def update_totals(self):   
        self.total_amount = self.calculate_total()
        self.total_paid = self.calculate_total_paid_amount()
        self.remaining_amount = self.total_amount - self.total_paid
        if self.remaining_amount <= 0:
            self.status = 'Paid'
        elif self.total_paid <= 0:
            self.status = 'Unpaid'
        else:
            self.status = 'Partially Paid'
        self.save(update_fields=['total_amount', 'total_paid', 'remaining_amount', 'status'])
        print(f"[Invoice {self.id}] Updated totals = {self.total_amount}")

    def update_total_wardbill(self):
     
        for ward_bill in self.ward_bills.all():
            bed = ward_bill.bed
            assigned_dt = ward_bill.assigned_at
            released_dt = ward_bill.released_at or tz_now()

            if is_naive(assigned_dt):
                assigned_dt = make_aware(assigned_dt)
            if is_naive(released_dt):
                released_dt = make_aware(released_dt)

            if self.invoice_type in ['Emergency','IPD']and getattr(bed, 'hourly_charge', None):
                duration_hours = (released_dt - assigned_dt).total_seconds() / 3600
                total_bill = (Decimal(duration_hours) * bed.get_effective_hourly_charge()).quantize(Decimal('0.01'))
                ward_bill.days_stayed = None
            else:
                num_days = max(1, (released_dt.date() - assigned_dt.date()).days)
                total_bill = (Decimal(num_days) * bed.get_effective_daily_charge()).quantize(Decimal('0.01'))
                ward_bill.days_stayed = num_days
            ward_bill.total_bill = total_bill
            ward_bill.save(update_fields=['total_bill', 'days_stayed'])
        self.total_amount = self.calculate_total()
        self.total_paid = self.calculate_total_paid_amount()
        self.remaining_amount = self.total_amount - self.total_paid
        self.save(update_fields=['total_amount', 'total_paid', 'remaining_amount'])       
  
    def is_fully_paid(self):
        return self.total_paid >= self.total_amount

    def __str__(self):
        return f"{self.invoice_id or 'Invoice'} -for Patient: {self.patient.name}/{self.patient.patient_id}-invoice type:{self.invoice_type})"
    



from .utils import apply_service_taxes

class ConsultationBill(models.Model):  
    CONSULTATION_SERVICES = [
    ('Consultation', 'Consultation'),
    ('Followup_Consultation', 'Follow-up Consultation'),
    ('Consultation_Discount', 'Consultation Discount'),
    ('Emergency', 'Emergency Service'),
]

    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="consultation_bills")
    doctor = models.ForeignKey('core.Doctor', on_delete=models.CASCADE)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE,related_name='consultation_fees',null=True,blank=True)
    service_type = models.CharField(max_length=50, choices=CONSULTATION_SERVICES,null=True,blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
   
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)   
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)    
  
    consultation_date = models.DateTimeField(auto_now_add=True)
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    consultation_type = models.CharField(max_length=50, choices=[
        ('Initial', 'Initial'),
        ('Follow-Up', 'Follow-Up'),
        ('Specialist', 'Specialist'),
    ], default='Follow-Up')
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid')],
        default='Unpaid'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('invoice', 'appointment')       

    def save(self, *args, **kwargs):    
        if not self.total_amount:
            self.total_amount = self.consultation_fee  
        self.remaining_amount = Decimal(self.total_amount) - Decimal(self.total_paid)
        apply_service_taxes(
            self,
            total_field='total_amount',           
        )
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Consultation {self.id} - {self.doctor} for {self.invoice.patient}"


from lab_tests.models import LabTestCatalog

class LabTestBill(models.Model):  
    lab_test_request_order = models.ForeignKey('lab_tests.LabTestRequest',on_delete=models.CASCADE,null=True,blank=True,related_name="lab_test_requests") 
    LAB_SERVICES = [
    ('Lab_Test', 'Lab / Diagnostic Test'),
    ('Radiology', 'Radiology / Imaging (X-ray, USG, CT, MRI)'),
    ('ECG', 'ECG / EEG / EMG'),
    ('Procedure', 'Minor Procedures'),
]

    service_type = models.CharField(max_length=50, choices=LAB_SERVICES,null=True,blank=True)
    delivered_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="lab_test_bills")
    lab_test = models.ForeignKey(LabTest, on_delete=models.CASCADE,null=True, blank=True)   
    lab_test_catelogue = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE, null=True, blank=True)   
    test_fee = models.DecimalField(max_digits=10, decimal_places=2)  
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True) 
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True)   
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True)

    test_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid'),('Delivered','Delivered')],
        default='Unpaid'
    )
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    notes =models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):    
        if not self.total_amount:
            self.total_amount = self.test_fee
        self.remaining_amount = Decimal(self.total_amount) - Decimal(self.total_paid)
        apply_service_taxes(
            self,
            total_field="total_amount",            
        )
        super().save(*args, **kwargs)      
       
    def __str__(self):
        return f"Lab Test {self.lab_test_catelogue.test_name} - {self.invoice.patient}"



class MedicineBill(models.Model):  
    MEDICINE_SERVICES = [
    ('Medicine_Sale', 'Medicine / Pharmacy Sale'),
    ('Injection', 'Injection / IV / Medication Service'),
]
    service_type = models.CharField(max_length=50, choices=MEDICINE_SERVICES,null=True,blank=True)
    delivered_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="medicine_bills",null=True,blank=True)
    medicine = models.ForeignKey(Product, on_delete=models.CASCADE)  # Assuming Medicine model exists
    
    quantity = models.IntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)

    dosage = models.CharField(max_length=100, blank=True, null=True)
    dosage_schedule = models.CharField(max_length=50, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
   
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)   
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid'),  ('Delivered', 'Delivered')],
        default='Unpaid'
    )

    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = (Decimal(self.quantity) * self.price_per_unit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.remaining_amount = Decimal(self.total_amount) - Decimal(self.total_paid)
        apply_service_taxes(
            self,
            total_field='total_amount',
           
        )

        super().save(*args, **kwargs)



    def total_price(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        return f"Medicine {self.medicine.name} for {self.invoice.patient}"




class WardBill(models.Model): 
    WARD_SERVICES = [
    ('Ward_Bed', 'Ward / Bed Charge'),
    ('Cabin', 'Cabin Charge'),
    ('ICU', 'ICU Charges'),
    ('CCU', 'CCU Charges'),
    ('NICU', 'NICU Charges'),
    ('PICU', 'PICU Charges'),
]

    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="ward_bills")
    service_type = models.CharField(max_length=50, choices=WARD_SERVICES,null=True,blank=True)
    ward = models.ForeignKey('facilities.Ward', on_delete=models.CASCADE, related_name="ward_facility",null=True,blank=True)
    bed = models.ForeignKey('facilities.Bed', on_delete=models.CASCADE, related_name="bed_facility")
    room = models.ForeignKey('facilities.Room', on_delete=models.CASCADE, related_name="room_facility", null=True, blank=True)
    charge_per_day = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    charge_per_hour = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    patient_admission = models.ForeignKey('patients.PatientAdmission', on_delete=models.CASCADE, null=True, blank=True,related_name='admission_ward')
    patient_emergency = models.ForeignKey('billing.EmergencyVisit', on_delete=models.CASCADE, null=True, blank=True,related_name='emergency_wards')
    days_stayed = models.DecimalField(max_digits=10,decimal_places=4,null=True,blank=True)

    total_bill = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)   
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    assigned_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    def save(self, *args, **kwargs):   
        total_amount = self.total_amount or Decimal('0.00')
        total_paid = self.total_paid or Decimal('0.00')
        total_bill = self.total_bill or Decimal('0.00')
    
        if self.total_amount is None or self.total_amount == Decimal('0.00'):
            self.total_amount = total_bill    
        self.remaining_amount = Decimal(self.total_amount) - Decimal(total_paid)
        apply_service_taxes(
            self,
            total_field='total_amount',
        )

        super().save(*args, **kwargs)


    def total_charge(self):
        if self.bed and self.bed.daily_charge is not None and self.days_stayed is not None:
            return self.bed.daily_charge * self.days_stayed
        return 0


    def __str__(self):
        return f"WardBill for {self.invoice.patient}"
    
    def recalculate_bill(self):
        # Default to bed's rate
        rate = self.bed.daily_charge if self.bed and self.bed.daily_charge else 0
        self.charge_per_day = rate

        start = None
        end = None
        stay_hours=None
        total_bill=None
      

        # Use latest active bed history if patient admission is available
        if self.patient_admission:
            self.bed = self.patient_admission.assigned_bed
            self.room = self.patient_admission.assigned_room
            self.ward = self.patient_admission.assigned_bed.ward

            bed_history = self.patient_admission.patient.patient_bed_histories.filter(released_at__isnull=True).first()
            start = bed_history.assigned_at if bed_history else None
            end = timezone.now() if bed_history else None

        # If start and end are available, calculate billing
        if isinstance(start, datetime) and isinstance(end, datetime):
            total_seconds = (end - start).total_seconds()
            stay_hours = total_seconds / 3600
            billable_hours = max(6, stay_hours)  # apply minimum cap of 6 hours
            hourly_rate = self.charge_per_day / 24
            self.days_stayed = round(billable_hours / 24, 4)
            self.total_bill = round(float( stay_hours) * float(hourly_rate), 2)
            total_bill = self.total_bill
        else:
            self.days_stayed = 0
            self.total_bill = 0
            total_bill = self.total_bill

        return total_bill
        



class OTBill(models.Model): 
    OT_SERVICES = [
    ('Operation_Theatre', 'Operation Theatre Charges'),
    ('Surgery', 'Surgical Charges'),
    ('OT_Consumables', 'OT Consumables'),
]

    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="ot_bills")
    service_type = models.CharField(max_length=50, choices=OT_SERVICES,null=True,blank=True)
    ot_booking = models.ForeignKey('facilities.OTBooking', on_delete=models.CASCADE, related_name="ot_bill",null=True, blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,null=True, blank=True)
    operation_theatre = models.ForeignKey('facilities.OperationTheatre', on_delete=models.SET_NULL, null=True, blank=True)
    procedure_name = models.CharField(max_length=100,null=True, blank=True)
    procedure = models.ForeignKey('facilities.OTBookingProcedure', on_delete=models.SET_NULL, null=True, blank=True,related_name='procedures')
    duration_hours = models.DecimalField(max_digits=6, decimal_places=2,null=True, blank=True)
    charge_per_hour = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
   
    total_charge = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)   
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
   
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    def save(self, *args, **kwargs):
        if self.total_amount is None or self.total_amount == Decimal('0.00'):
            self.total_amount = self.total_charge    
        self.remaining_amount = Decimal(self.total_amount) - Decimal(self.total_paid)
        apply_service_taxes(
            self,
            total_field='total_amount',          
        )
        super().save(*args, **kwargs)

        

    def __str__(self):
        return f"OT Bill for {self.patient} - {self.procedure_name}"


class MiscellaneousBill(models.Model):  
    OTHER_SERVICES = [
    ('Blood_Bank', 'Blood Bank Services'),
    ('Vaccination', 'Vaccination'),
    ('Dental', 'Dental Services'),
    ('ENT', 'ENT Procedures'),
    ('Eye', 'Eye / Ophthalmology Procedures'),
    ('Hospital_Package', 'Hospital Packages'), 
    ('Nursing', 'Nursing Service Charge'),
    ('Dialysis', 'Dialysis Charge'),
    ('Ambulance', 'Ambulance Charge'),
    ('Physiotherapy', 'Physiotherapy'),]

    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="misc_bills")
    service_name = models.CharField(max_length=50, choices=OTHER_SERVICES)
    service_type = models.CharField(max_length=50, choices=OTHER_SERVICES,null=True,blank=True)
   
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ait_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)   
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
   
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially Paid', 'Partially Paid')],
        default='Unpaid'
    )
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)      

    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)


    def save(self, *args, **kwargs):
        if not self.service_type:
            self.service_type = self.service_name
        if self.quantity and self.unit_price > 0:
            self.total_amount = (Decimal(self.quantity) * Decimal(self.unit_price)).quantize(Decimal('0.01'))
        else:
            self.total_amount = Decimal(self.amount or 0).quantize(Decimal('0.01'))
        self.remaining_amount = (Decimal(self.total_amount) - Decimal(self.total_paid or 0)).quantize(Decimal('0.01'))
        apply_service_taxes(
            self,
            total_field='total_amount',           
        )
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.service_name} - {self.invoice.patient}"



from django.utils.crypto import get_random_string

class EmergencyVisit(models.Model):  
    STATUS_CHOICES = [
        ('Admitted', 'Admitted'),
        ('Discharged', 'Discharged'),
        ('Transferred', 'Transferred'),
	('Emergency-Service', 'Emergency Service'),
    ]
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    admission_code=models.CharField(max_length=50,null=True,blank=True)
    service_type = models.CharField(
        max_length=50,
        choices=[('Emergency', 'Emergency Service')],
        default='Emergency',null=True,blank=True
    )
    
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    visit_time = models.DateTimeField(auto_now_add=True)
    chief_complaint = models.TextField()
    triage_level = models.CharField(
        max_length=1,
        choices=[
            ('1', 'Level 1 - Revival'),
            ('2', 'Level 2 - Emergent'),
            ('3', 'Level 3 - Urgent'),
            ('4', 'Level 4 - Semi-Urgent'),
            ('5', 'Level 5 - Non-Urgent'),
        ]
    )
    treated_by = models.ForeignKey('core.Doctor', on_delete=models.SET_NULL, null=True, blank=True)
    invoice = models.OneToOneField(BillingInvoice, on_delete=models.CASCADE,related_name="emergency_visit_invoice")
    medical_record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE,related_name="emergergency_medical_records",null=True,blank=True)
    assigned_bed = models.ForeignKey('facilities.Bed',on_delete=models.CASCADE,related_name='emergency_beds',null=True,blank=True)
    assigned_ward = models.ForeignKey('facilities.Ward', on_delete=models.SET_NULL, null=True, blank=True,related_name='emergency_wards')
    assigned_room = models.ForeignKey('facilities.Room', on_delete=models.SET_NULL, null=True, blank=True,related_name='emergency_rooms')
    bed_assignment_date = models.DateField(null=True, blank=True)
    discharge_approved = models.BooleanField(default=False)
    discharge_date = models.DateTimeField(null=True,blank=True)
    is_converted_to_admission = models.BooleanField(default=False)
    end_time = models.DateTimeField(null=True,blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Emergency-Service')
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def save(self, *args, **kwargs):
        if not self.admission_code:
            self.admission_code = self.generate_admission_code()
        super().save(*args, **kwargs)

    def generate_admission_code(self):
        if self.visit_time:
            date_str = self.visit_time.strftime("%y%m")  # Example: "2504" for April 2025
        else:
            date_str = timezone.now().strftime("%y%m")
        return f"EMGNCY-{date_str}-{self.patient.id}-{get_random_string(length=3).upper()}"

    def days_stayed(self):
        end_date = self.discharge_date or timezone.now()
        return (end_date - self.visit_time).days + 1

    def is_discharged(self):
        return self.status in ['Discharged','Transferred']

    def __str__(self):
        return f"PID:{self.admission_code} | {self.patient.name}--Doctor:{self.treated_by})"

    



# payment by patient
class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('Consultation', 'Consultation'),
        ('Lab', 'Lab Test'),
        ('Medicine', 'Medicine'),
        ('Ward', 'Ward'),
        ('OT', 'OT Bill'),
        ('Misc', 'Miscellaneous'),
        ('Advance', 'Advance'),
        ('Full', 'Full Bill Payment'),
        ('External-Lab-Test', 'External Lab test'),
        ('Medicine-Sale-Only', 'Medicine Sale Only'),
    ]

    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),
        ('OPD','OutPatient'),
        ('Emergency','Emergency'),
        ('External-Lab-Test','External Lab Test'),
        ('Medicine-Only','Medicine Only'),
        ],null=True,blank=True)

    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)
    payment_method = models.CharField(max_length=50, choices=[
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile', 'Mobile Payment'),
    ],default='Cash')
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES,null=True,blank=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f"{self.payment_type} - {self.amount_paid} on {self.created_at.strftime('%Y-%m-%d')}"






class DoctorServiceRate(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.ForeignKey('core.Doctor', on_delete=models.CASCADE)
    SERVICE_TYPE_CHOICES = [
        ('Minor', 'Minor Surgery'),
        ('Consultation', 'Consultation'),
        ('Followup-Consultation', 'Followup Consultation'),
        ('Surgery', 'Surgery'),
        ('Lab Review', 'Lab Review'),
        ('Lab-Test-Report','Lab Test Report'),
        ('Physiotherapy','Physiotherapy'),
        ('Anesthesia-Service','Anesthesia Service'),
    ]
    service_type = models.CharField(max_length=100, null=True, blank=True, choices=SERVICE_TYPE_CHOICES)
    SURGERY_TYPE_CHOICES = [
        ('Minor', 'Minor Surgery'),
        ('Major', 'Major'),
        ('OT-Procedure', 'OT Procedure'),
        ('Emergency', 'Emergency Surgery'),
    ]
    surgery_type = models.CharField(max_length=100, choices=SURGERY_TYPE_CHOICES, null=True, blank=True)
    rate = models.DecimalField(max_digits=30, decimal_places=2)
    share_type = models.CharField(
        max_length=20,
        choices=[("percentage", "Percentage"), ("fixed", "Fixed Amount")],
        default="percentage",
        null=True,
        blank=True
    )
    doctor_share = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'service_type', 'surgery_type')

    def save(self, *args, **kwargs):
        # Ensure doctor_share is at least 0
        if self.doctor_share is None:
            self.doctor_share = 0
        super().save(*args, **kwargs)

    def __str__(self):
        if self.service_type == 'Surgery' and self.surgery_type:
            return f" doctor-{self.doctor}--{self.service_type}--({self.rate})"
        return f" doctor-{self.doctor}--{self.service_type}-{self.rate}"







from django.db.models import F

class DoctorServiceLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="doctor_service_logs", null=True, blank=True)
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey('core.Doctor', on_delete=models.CASCADE)
    service_type = models.CharField(
        max_length=100, null=True, blank=True,
        choices=DoctorServiceRate.SERVICE_TYPE_CHOICES
    )
    surgery_type = models.CharField(
        max_length=100, null=True, blank=True,
        choices=DoctorServiceRate.SURGERY_TYPE_CHOICES
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, null=True, blank=True)
    service_date = models.DateField(default=timezone.now)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    share_type = models.CharField(max_length=10, choices=[('percent','%'), ('fixed','Fixed')], null=True, blank=True)
    doctor_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hospital_share = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
  
        if not self.service_fee or self.doctor_share is None or self.hospital_share is None or not self.share_type:
            try:
                filters = {'doctor': self.doctor, 'service_type': self.service_type}
                if self.service_type == 'Surgery' and self.surgery_type:
                    filters['surgery_type'] = self.surgery_type
                else:
                    filters['surgery_type__isnull'] = True

                rate_obj = DoctorServiceRate.objects.get(**filters)
                self.service_fee = rate_obj.rate
                self.share_type = rate_obj.share_type

                if self.share_type == "percentage":
                    self.doctor_share = self.service_fee * rate_obj.doctor_share / 100
                else:
                    self.doctor_share = rate_obj.doctor_share

                self.hospital_share = self.service_fee - self.doctor_share

            except DoctorServiceRate.DoesNotExist:
                raise ValueError(
                    f"Rate not defined for {self.doctor} - {self.service_type} {self.surgery_type or ''}"
                )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service_type} by {self.doctor} on {self.service_date}"



 
# payment to doctor
class DoctorPayment(models.Model):
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    doctor = models.ForeignKey('core.Doctor', on_delete=models.CASCADE, null=True,blank=True)
    total_due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,blank=True, null=True)  # total service value
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,blank=True, null=True)   # actual payment done
    payment_method = models.CharField(max_length=50, choices=[
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile', 'Mobile Payment'),
    ],default='Cash',blank=True, null=True)

    applied_service_logs = models.ManyToManyField(
        DoctorServiceLog,
        blank=True,
        related_name='service_log_payments'
    )
    payment_date = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def due_amount(self):
        return self.total_due_amount - self.total_paid_amount

    def update_payment_status(self):
        self.is_paid = self.due_amount <= 0
        self.save()
        
    def __str__(self):
        doctor_name = self.doctor.name if self.doctor and self.doctor.name else "Unknown Doctor"
        return f"Payment to {doctor_name} on {self.payment_date}"




################################################ Commision models ###################################

from accounting.service_type import SERVICE_REFERRAL_TYPES


class ReferralCommissionRule(models.Model):
    SERVICE_TYPES = [
        ('consultation', 'Consultation'),
        ('lab', 'Lab Test'),
        ('surgery', 'Surgery'),
        ('ot', 'Operation Theatre'),
        ('emergency', 'Emergency visit'),
        ('physio', 'Physiotherapy'),
        ('ward', 'ward bill'),
        ('medicine', 'medicine bill'),
        ('all', 'All services'),
        ('other', 'Other')
    ]
 

    referral_source = models.ForeignKey(ReferralSource, on_delete=models.CASCADE,null=True,blank=True,related_name='referral_commission_rules')
    referral_type = models.CharField(max_length=30, choices=ReferralSource.REFERRAL_TYPES, null=True, blank=True)
    service_type = models.CharField(max_length=30, choices=SERVICE_REFERRAL_TYPES,null=True,blank=True)
    commission_type = models.CharField(max_length=10, choices=[('percent','%'), ('fixed','Fixed')])
    value = models.DecimalField(max_digits=10, decimal_places=2)
    apply_once_per_patient = models.BooleanField(default=True)

    class Meta:
        unique_together = ('referral_source','service_type','commission_type')

    def __str__(self):
        target = self.referral_source or self.referral_type
        return f"{target} - {self.service_type} - {self.value} ({self.commission_type})"


class ReferralCommissionTransaction(models.Model):
    referral_source = models.ForeignKey(ReferralSource, on_delete=models.CASCADE,null=True,blank=True,related_name='referral_transactions')
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE,null=True,blank=True)
    service_type = models.CharField(max_length=30)
    service_id = models.PositiveIntegerField(null=True,blank=True)  
    service_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="Pending",
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Paid", "Paid")]
    )
    created_at = models.DateTimeField(auto_now_add=True)


from django.db import models

class ReferralPayment(models.Model):
    PAYMENT_MODES = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank'),
        ('bKash', 'bKash'),
        ('Other', 'Other'),
    ]

    referral_source = models.ForeignKey(ReferralSource, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    applied_referrals = models.ManyToManyField(
        ReferralCommissionTransaction,
        blank=True,
        related_name='referral_payments'
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payment {self.amount_paid} for {self.referral_source} on {self.payment_date.date()}"
    



#===========================================================================
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# wardbill signals 
@receiver(post_save, sender=WardBill)
def update_billing_invoice_after_ward_bill_save(sender, instance, **kwargs):
    if instance.invoice:
        instance.invoice.update_totals()


@receiver(post_delete, sender=WardBill)
def update_billing_invoice_after_ward_bill_delete(sender, instance, **kwargs):
    if instance.invoice:
         instance.invoice.update_totals()

#==========================================================================
# Consultation bill signals 
@receiver(post_save, sender=ConsultationBill)
def update_billing_invoice_after_consultation_bill_save(sender, instance, **kwargs):
    if instance.invoice:
         instance.invoice.update_totals()


@receiver(post_delete, sender=ConsultationBill)
def update_billing_invoice_after_consulation_bill_delete(sender, instance, **kwargs):
    if instance.invoice:
        instance.invoice.update_totals()


#==========================================================================
# Medicine bill signals calculate_total_paid_amount/calculate_total// total_amount/total_paid

@receiver(post_save, sender=MedicineBill)
def update_billing_invoice_after_medicine_bill_save(sender, instance, **kwargs):
    if instance.invoice:
         instance.invoice.update_totals()


@receiver(post_delete, sender=MedicineBill)
def update_billing_invoice_after_medicine_bill_delete(sender, instance, **kwargs):
    if instance.invoice:
        instance.invoice.update_totals()

#==========================================================================

#==========================================================================
# Misc bill signals 
@receiver(post_save, sender=MiscellaneousBill)
def update_billing_invoice_after_miscellaneous_bill_save(sender, instance, **kwargs):
    if instance.invoice:
        instance.invoice.update_totals()


@receiver(post_delete, sender=MiscellaneousBill)
def update_billing_invoice_after_miscellaneous_bill_delete(sender, instance, **kwargs):
    if instance.invoice:
         instance.invoice.update_totals()



#==========================================================================
# Lab Test bill signals 
@receiver(post_save, sender=LabTestBill)
def update_billing_invoice_after_lab_test_bill_save(sender, instance, **kwargs):
    if instance.invoice:
         instance.invoice.update_totals()


@receiver(post_delete, sender=LabTestBill)
def update_billing_invoice_after_lab_test_bill_delete(sender, instance, **kwargs):
    if instance.invoice:
        instance.invoice.update_totals()




#==========================================================================
# Payment signals  
@receiver(post_save, sender=Payment)
def update_billing_invoice_after_pament_save(sender, instance, **kwargs):
    if instance.invoice:
         instance.invoice.update_totals()


@receiver(post_delete, sender=Payment)
def update_billing_invoice_after_payment_delete(sender, instance, **kwargs):
    if instance.invoice:
        instance.invoice.update_totals()

