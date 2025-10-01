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





class BillingInvoice(models.Model):
    invoice_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    medical_record = models.OneToOneField(MedicalRecord, null=True, blank=True, on_delete=models.SET_NULL, related_name='billing_medical_record')
    admission = models.OneToOneField('patients.PatientAdmission', on_delete=models.CASCADE, null=True, blank=True, related_name="billing_admission")
   # appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE, null=True, blank=True, related_name="appointment_invoices")
    INVOICE_TYPE = [
         ('', 'All'),
        ('OPD', 'Outpatient'),
        ('IPD', 'Inpatient'),
        ('Emergency', 'Emergency'),
	('External-Lab-Test', 'External Lab Test patient'),
        ('Medicine-Sale-Only', 'Medicine Sale Only'),
    ]
    invoice_type = models.CharField(max_length=50, choices=INVOICE_TYPE, default='OPD')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='patient_billing')   
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency'),
        ('Medicine-Only','Medicine Only')
        ],null=True,blank=True) 
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid')],
        default='Unpaid'
    )
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invoice_id:
            self.invoice_id = self.generate_unique_invoice_id()
        self.remaining_amount = self.total_amount - self.total_paid
        if self.total_amount > 0 and self.total_paid >= self.total_amount:
            self.status = 'Paid'
        elif 0 < self.total_paid < self.total_amount:
            self.status = 'Partially Paid'
        else:
            self.status = 'Unpaid'
        super().save(*args, **kwargs)

    
    def generate_unique_invoice_id(self):
        last_invoice = BillingInvoice.objects.aggregate(Max('invoice_id'))['invoice_id__max']
        if last_invoice:   
            last_invoice_number = int(last_invoice.split('-')[-1]) 
            new_invoice_number = last_invoice_number + 1
        else:
            new_invoice_number = 1 
        return f"INV-{timezone.now().year}-{str(new_invoice_number).zfill(4)}"



    def calculate_total_paid_amount(self):
        return self.payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    

    def calculate_total(self):
        consultation_total = self.consultation_bills.aggregate(
            total=Sum('consultation_fee'))['total'] or 0
        
        lab_total = self.lab_test_bills.aggregate(
            total=Sum('test_fee'))['total'] or 0

        medicine_total = self.medicine_bills.aggregate(
            total=Sum(ExpressionWrapper(
                F('quantity') * F('price_per_unit'),
                output_field=DecimalField()))
        )['total'] or 0


        ward_total = self.ward_bills.aggregate(
            total=Sum('total_bill')
        )['total'] or 0


        OT_total = self.ot_bills.aggregate(
            total=Sum('total_charge'))['total'] or 0
      

        misc_total = self.misc_bills.aggregate(
            total=Sum('amount'))['total'] or 0

        return consultation_total + lab_total + medicine_total + ward_total + misc_total + OT_total
    
    def update_totals(self):
        self.total_amount = self.calculate_total()
        self.total_paid = self.calculate_total_paid_amount()
        self.remaining_amount = self.total_amount - self.total_paid

        if self.remaining_amount == 0:
            self.status = 'Paid'
        elif self.total_paid == 0:
            self.status = 'Unpaid'
        else:
            self.status = 'Partially Paid'

        self.save(update_fields=['total_amount', 'total_paid', 'remaining_amount', 'status'])
        print(f'Updated total invoice = {self.total_amount}, status = {self.status}')



    def update_total_wardbill(self):    
            for ward_bill in self.ward_bills.all():
                ward_bill.save()  
            self.total_amount = self.calculate_total()
            self.total_paid = self.calculate_total_paid_amount()
            self.remaining_amount = self.total_amount - self.total_paid
            self.save(update_fields=['total_amount', 'total_paid', 'remaining_amount'])

  
    def is_fully_paid(self):
        return self.total_paid >= self.total_amount

    def __str__(self):
        return f"{self.invoice_id or 'Invoice'} -for Patient: {self.patient.name}/{self.patient.patient_id}-invoice type:{self.invoice_type})"
    




class ConsultationBill(models.Model):
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="consultation_bills")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE,related_name='consultation_fees',null=True,blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    consultation_date = models.DateTimeField(auto_now_add=True)
    patient_type =  models.CharField(max_length=50,choices=[('IPD','Inpatient'),('OPD','OutPatient'),('Emergency','Emergency')],null=True,blank=True)
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
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    class Meta:
        unique_together = ('invoice', 'appointment')
    def __str__(self):
        return f"Consultation {self.id} - {self.doctor} for {self.invoice.patient}"


class LabTestBill(models.Model):
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="lab_test_bills")
    lab_test = models.ForeignKey(LabTest, on_delete=models.CASCADE,null=True,blank=True)
    lab_test_catelogue = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE, null=True, blank=True)
    test_fee = models.DecimalField(max_digits=10, decimal_places=2)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f"Lab Test {self.lab_test_catelogue.test_name} - {self.invoice.patient}"




class MedicineBill(models.Model):
    delivered_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="medicine_bills",null=True,blank=True)
    medicine = models.ForeignKey(Product, on_delete=models.CASCADE)  # Assuming Medicine model exists
    quantity = models.IntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid'),('Delivered', 'Delivered')],
        default='Unpaid'
    )

    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)


    def total_price(self):
        return self.quantity * self.price_per_unit

    def __str__(self):
        return f"Medicine {self.medicine.name} for {self.invoice.patient}"





class WardBill(models.Model):
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="ward_bills")
    ward = models.ForeignKey('facilities.Ward', on_delete=models.CASCADE, related_name="ward_facility")
    bed = models.ForeignKey('facilities.Bed', on_delete=models.CASCADE, related_name="bed_facility")
    room = models.ForeignKey('facilities.Room', on_delete=models.CASCADE, related_name="room_facility", null=True, blank=True)
    charge_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    patient_admission = models.ForeignKey('patients.PatientAdmission', on_delete=models.CASCADE, null=True, blank=True)
    days_stayed = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    total_bill = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    patient_type =  models.CharField(max_length=50,choices=[('IPD','Inpatient'),('OPD','OutPatient'),('Emergency','Emergency')],null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)


    def recalculate_bill(self):
        # Default to bed's rate
        rate = self.bed.daily_charge if self.bed and self.bed.daily_charge else 0
        self.charge_per_day = rate

        start = None
        end = None
        stay_hours=None
      

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
        else:
            self.days_stayed = 0
            self.total_bill = 0

    def total_charge(self):
        if self.bed and self.bed.daily_charge is not None and self.days_stayed is not None:
            return self.bed.daily_charge * self.days_stayed
        return 0


    def __str__(self):
        return f"WardBill for {self.invoice.patient} — {self.ward.name}"


class OTBill(models.Model):
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="ot_bills")
    ot_booking = models.OneToOneField('facilities.OTBooking', on_delete=models.CASCADE, related_name="ot_bill",null=True, blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,null=True, blank=True)
    operation_theatre = models.ForeignKey('facilities.OperationTheatre', on_delete=models.SET_NULL, null=True, blank=True)
    procedure_name = models.CharField(max_length=100,null=True, blank=True)
    duration_hours = models.DecimalField(max_digits=6, decimal_places=2,null=True, blank=True)
    charge_per_hour = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)
    total_charge = models.DecimalField(max_digits=12, decimal_places=2)
    patient_type =  models.CharField(max_length=50,choices=[('IPD','Inpatient'),('OPD','OutPatient'),('Emergency','Emergency')],null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    def save(self, *args, **kwargs):
        if self.ot_booking:
            self.operation_theatre = self.ot_booking.operation_theatre
            self.patient = self.ot_booking.patient
            self.procedure_name = self.ot_booking.procedure_name
            self.duration_hours = self.ot_booking.duration_hours()
            self.charge_per_hour = self.ot_booking.operation_theatre.hourly_rate
            self.total_charge = float(self.charge_per_hour) * float(self.duration_hours)
            self.patient_type = self.ot_booking.patient_type
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OT Bill for {self.patient} - {self.procedure_name}"

    

class MiscellaneousBill(models.Model):
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="misc_bills")
    service_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid')],
        default='Unpaid'
    )
    patient_type =  models.CharField(max_length=50,choices=[('IPD','Inpatient'),('OPD','OutPatient'),('Emergency','Emergency')],null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f"{self.service_name} - {self.invoice.patient}"



class EmergencyVisit(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    visit_time = models.DateTimeField(auto_now_add=True)
    chief_complaint = models.TextField()
    triage_level = models.CharField(
        max_length=1,
        choices=[
            ('1', 'Level 1 - Resuscitation'),
            ('2', 'Level 2 - Emergent'),
            ('3', 'Level 3 - Urgent'),
            ('4', 'Level 4 - Semi-Urgent'),
            ('5', 'Level 5 - Non-Urgent'),
        ]
    )
    treated_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    invoice = models.OneToOneField(BillingInvoice, on_delete=models.CASCADE,related_name="emergergency_visit_invoices")
    medical_record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE,related_name="emergergency_medical_records",null=True,blank=True)
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)

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
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=100,null=True, blank=True, choices=[
        ('Consultation', 'Consultation'),
        ('Followup-Consultation', 'Followup Consultation'),
        ('Surgery', 'Surgery'),
        ('Lab Review', 'Lab Review'),       
        ('Lab Test', 'Lab Test'),    
        ('External-Lab-Test', 'external Lab Test'),    
        ('Others', 'Others'),    
    ])

    SURGERY_TYPE_CHOICES = [
        ('Minor', 'Minor Surgery'),
        ('Major', 'Major Surgery'),
        ('OT-Procedure', 'OT Procedure'),
        ('Emergency', 'Emergency Surgery'),
       
    ]
    surgery_type = models.CharField(max_length=100, choices=SURGERY_TYPE_CHOICES, null=True, blank=True)
    rate = models.DecimalField(max_digits=30, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'service_type', 'surgery_type')

    def __str__(self):
        if self.service_type == 'Surgery' and self.surgery_type:
            return f"{self.service_type} ({self.surgery_type})"
        return f"{self.service_type}"
    








# payment to doctor
class DoctorPayment(models.Model):
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True,blank=True)
    total_due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,blank=True, null=True)  # total service value
    total_paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,blank=True, null=True)   # actual payment done
    payment_method = models.CharField(max_length=50, choices=[
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Mobile', 'Mobile Payment'),
    ],default='Cash',blank=True, null=True)
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


class DoctorServiceLog(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, limit_choices_to={'role': 'doctor'})
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE, related_name="doctor_service_logs",null=True, blank=True,)
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.SET_NULL, null=True, blank=True)

    service_type = models.CharField(max_length=100,null=True, blank=True, choices=[
        ('Consultation', 'Consultation'),
        ('Surgery', 'Surgery'),
        ('Lab Review', 'Lab Review'),
	('Lab-Test-Report','Lab Test Report')
       
    ])
    SURGERY_TYPE_CHOICES = [
        ('Minor', 'Minor Surgery'),
        ('Major', 'Major Surgery'),
        ('OT-Procedure', 'OT Procedure'),
        ('Emergency', 'Emergency Surgery'),
       
    ]
    surgery_type = models.CharField(max_length=100, choices=SURGERY_TYPE_CHOICES, null=True, blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,null=True, blank=True)
    service_date = models.DateField()
    service_fee = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)

    is_paid = models.BooleanField(default=False)
    payment = models.ForeignKey(DoctorPayment, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.service_fee:
            try:
                rate_obj = DoctorServiceRate.objects.get(doctor=self.doctor, service_type=self.service_type)
                self.service_fee = rate_obj.rate
            except DoctorServiceRate.DoesNotExist:
                raise ValueError(f"Rate not defined for {self.doctor} - {self.service_type}")

        super().save(*args, **kwargs) 
        payment_obj, created = DoctorPayment.objects.get_or_create(doctor=self.doctor)
        if created:
            payment_obj.total_due_amount = self.service_fee
            payment_obj.save()
        else:
            DoctorPayment.objects.filter(doctor=self.doctor).update(
                total_due_amount=F('total_due_amount') + self.service_fee
            )


    def __str__(self):
        return f"{self.service_type} by {self.doctor} on {self.service_date}"
 



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

