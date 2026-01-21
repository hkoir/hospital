from django.db import models
from accounts.models import CustomUser
from datetime import date
from facilities.models import Ward,Bed,Room
from core.models import Doctor
from django.utils import timezone
from billing.models import BillingInvoice
from django.utils.crypto import get_random_string




class Guardian(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)   
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address=models.TextField(null=True,blank=True)
    profile_picture = models.ImageField(upload_to='guardian_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"



from billing.models import ReferralSource
from datetime import timedelta

class Patient(models.Model):    
    referral_source = models.ForeignKey(
        ReferralSource, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='patient_referrals'
    )
    patient_id = models.CharField(max_length=30,null=True,blank=True,unique=True)    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    guardian =models.ForeignKey(Guardian, on_delete=models.CASCADE, null=True, blank=True)
    name=models.CharField(max_length=255,null=True,blank=True)
    email=models.EmailField(null=True,blank=True)
    phone=models.CharField(max_length=255,null=True,blank=True)
    date_of_birth = models.DateField(null=True,blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')],null=True,blank=True)
    address = models.TextField(null=True,blank=True)
    emergency_contact = models.CharField(max_length=15,null=True,blank=True)   
    medical_history = models.TextField(blank=True, null=True)
    patient_photo = models.ImageField(upload_to='patient_photos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'phone', 'date_of_birth'], name='unique_patient_record')
        ]

    def save(self, *args, **kwargs):
        if not self.patient_id:
            now = timezone.now()
            prefix = now.strftime("PT-%y%m")
            for i in range(1, 10000):
                patient_id = f"{prefix}-{i:04d}"
                if not Patient.objects.filter(patient_id=patient_id).exists():
                    self.patient_id = patient_id
                    break

        if self.pk:
            old = Patient.objects.filter(pk=self.pk).first()
            if old and old.referral_source != self.referral_source:
                PatientReferralHistory.objects.create(
                    patient=self,
                    referral_source=self.referral_source,
                    service_type=None,
                    service_id=None
                )

        super().save(*args, **kwargs)

    def get_current_bed(self):       
        return self.bed_histories.filter(
            released_at__isnull=True
        ).order_by('-assigned_at').first()

    def calculate_age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def has_scheduled_appointments(self):
        return self.patient_appointments.filter(status="Scheduled").exists()

    def next_appointment_type(self, doctor):
        last_appt = self.patient_appointments.filter(
            doctor=doctor,
            status='Prescription-Given'
        ).order_by('-date').first()

        if not last_appt:
            return 'New'

        if last_appt.appointment_type == 'Follow-up':
            return 'New'

        if last_appt.appointment_type == 'New':
            if last_appt.date + timedelta(days=10) < timezone.now().date():
                return 'New'
            else:
                return 'Follow-up'        
        return 'New'
    @property
    def has_active_admission(self):       
        return self.admissions.filter(discharge_approved=False).exists()

    def __str__(self):
        return self.name if self.name else 'Unnamed Patient'



class PatientReferralHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='referral_history')
    referral_source = models.ForeignKey(ReferralSource, on_delete=models.SET_NULL, null=True)
    service_type = models.CharField(max_length=50, null=True, blank=True)  # e.g., consultation, lab
    service_id = models.PositiveIntegerField(null=True, blank=True)         # the actual service record ID
    created_at = models.DateTimeField(auto_now_add=True)

from billing.models import EmergencyVisit

class PatientAdmission(models.Model):
    admission_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    emergency = models.OneToOneField(
        EmergencyVisit, null=True, blank=True, on_delete=models.SET_NULL
    )
    ADMISSION_TYPE_CHOICES = [
        ('Emergency', 'Emergency'),
        ('Planned', 'Planned'),
        ('Referral', 'Referral'),
        ('Emergency-To-IPD', 'Emergency to IPD'),
    ]

    STATUS_CHOICES = [
        ('Admitted', 'Admitted'),
        ('Discharged', 'Discharged'),
        ('Transferred', 'Transferred'),
        ('Convert-To-IPD', 'Convert to IPD'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="admissions")
    admission_date = models.DateTimeField(default=timezone.now)   
    
    admitting_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True,related_name='admitting_doctor')
    assigned_ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True,related_name='admitting_ward')
    assigned_bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True,related_name='admitting_bed')
    assigned_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True,related_name='admitting_room')

    reason_for_admission = models.TextField(blank=True)
    admission_type = models.CharField(max_length=20, choices=ADMISSION_TYPE_CHOICES, default='Planned')
    patient_photo = models.ImageField(upload_to='Patient_photo',null=True,blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Admitted')
    bed_assignment_date = models.DateField(null=True, blank=True)     
    discharge_approved = models.BooleanField(default=False)
    discharge_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def save(self, *args, **kwargs):
        if not self.admission_code:
            self.admission_code = self.generate_admission_code()
        super().save(*args, **kwargs)

    def generate_admission_code(self):
        if self.admission_date:
            date_str = self.admission_date.strftime("%y%m")  # Example: "2504" for April 2025
        else:
            date_str = timezone.now().strftime("%y%m")
        return f"ADM-{date_str}-{self.patient.id}-{get_random_string(length=3).upper()}"

    def days_stayed(self):
        end_date = self.discharge_date or timezone.now()
        return (end_date - self.admission_date).days + 1

    def is_discharged(self):
        return self.status in ['Discharged','Transferred']

    def __str__(self):
        return f"PID:{self.admission_code} | {self.patient.name}--Doctor:{self.admitting_doctor})"




from billing.models import EmergencyVisit

class DischargeReport(models.Model):
    patient_admission = models.OneToOneField(PatientAdmission, related_name='discharge_report', on_delete=models.CASCADE,null=True,blank=True)
    patient_emergency = models.OneToOneField(EmergencyVisit, related_name='emergency_discharge_report', on_delete=models.CASCADE,null=True,blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True,related_name='discharge_doctor')    
    invoice = models.OneToOneField(BillingInvoice, related_name='invoice_discharge_report', on_delete=models.CASCADE,null=True,blank=True)
    reason_for_admission = models.TextField(blank=True, null=True)
    diagnosis = models.TextField()
    treatment_given = models.TextField()
    investigations = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    condition_at_discharge = models.TextField(blank=True, null=True)
    follow_up_instructions = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)
    additional_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
 

    def __str__(self):
        return f"Discharge Report for {self.invoice.patient.name}"
