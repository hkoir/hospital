from django.db import models
from patients.models import Patient
from core.models import Doctor
from accounts.models import CustomUser
from django.utils import timezone
from medical_records.models import MedicalRecord

from datetime import datetime


class AppointmentSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField(null=True,blank=True)
    start_time = models.TimeField(null=True,blank=True)
    end_time = models.TimeField(null=True,blank=True)
    slot_duration = models.IntegerField(null=True,blank=True)
    is_booked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:    
            start_dt = datetime.combine(self.date or datetime.today().date(), self.start_time)
            end_dt = datetime.combine(self.date or datetime.today().date(), self.end_time)
            duration = (end_dt - start_dt).total_seconds() / 60  
            self.slot_duration = int(duration) if duration > 0 else 0
        else:
            self.slot_duration = None  # Or keep it blank

        super().save(*args, **kwargs)

    def __str__(self):
        return f" with {self.doctor} on {self.date}-at slots:{self.start_time}-{self.end_time}"
 



    
import logging

logger = logging.getLogger(__name__)

class Appointment(models.Model):
    appointment_code = models.CharField(max_length=30,null=True,blank=True)
    medical_record = models.ForeignKey(MedicalRecord, null=True, blank=True, on_delete=models.SET_NULL, related_name='medical_record_appointments')
    invoice = models.ForeignKey('billing.BillingInvoice', null=True, blank=True, on_delete=models.SET_NULL, related_name='invoice_appointments')
    appointment_type = models.CharField(max_length=20,choices={('New','New'),('Follow-up','Follow up')},null=True,blank=True)
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Checked', 'Checked'),
        ('Prescription-Given', 'Prescription Given'),
        ('Lab-Test-Requested', 'Lab Test Requested'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Scheduled', 'Scheduled'),
    ]
    user= models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True,blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE,null=True,blank=True,related_name='doctor_appointments')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE,null=True,blank=True,related_name='patient_appointments')
    patient_type = models.CharField(max_length=20,choices={('OPD','OPD'),('IPD','IPD')},null=True,blank=True)
    timeslot = models.ForeignKey(AppointmentSlot,on_delete=models.CASCADE,null=True,blank=True)
    payment_status = models.CharField(
        max_length=50, 
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Partially-Paid', 'Partially Paid')],
        default='Unpaid'
    )
    date = models.DateField(default=timezone.now)   
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')    
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)

    def save(self, *args, **kwargs):
        if self.timeslot:
            self.date = self.timeslot.date

        if not self.appointment_code:
            year = timezone.now().strftime("%y")  # Last 2 digits of year
            existing_appointments = Appointment.objects.filter(date__year=self.date.year).count() + 1
            self.appointment_code = f"AP{year}{existing_appointments:06d}"

        super().save(*args, **kwargs)

    def has_medicine_or_labtest_bills(self):
        try:
            invoice = self.medical_record.billing_medical_record
            logger.debug(f"Invoice found for MedicalRecord {self.medical_record.id}: {invoice}")

            has_medicine = invoice.medicine_bills.exists()
            has_lab = invoice.lab_test_bills.exists()

            logger.debug(f"Has Medicine Bills: {has_medicine}, Has Lab Bills: {has_lab}")

            return has_medicine or has_lab
        except AttributeError as e:
            logger.error(f"AttributeError accessing billing_invoice_records: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error in has_medicine_or_labtest_bills: {e}")
            return False






    def __str__(self):
        return f"Patient:{self.patient} with {self.doctor} on {self.date}-at {self.timeslot}"

