from django.db import models
from core.models import Doctor
from django.utils import timezone
import uuid
from accounts.models import CustomUser



class MedicalRecord(models.Model):
    medical_record_code= models.CharField(max_length=30,null=True,blank=True,unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, null=True, blank=True,related_name='patient_medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='medical_records')
    external_doctor = models.CharField(max_length=255, blank=True, null=True)
    diagnosis = models.TextField(default='N/A')
    treatment_plan = models.TextField(default='N/A')
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.medical_record_code:
            year = timezone.now().strftime("%y")  # Last 2 digits of year
            unique_suffix = uuid.uuid4().hex[:6].upper()  # Short but unique
            self.medical_record_code = f"MR{year}{unique_suffix}"

        super().save(*args, **kwargs)


    def __str__(self):
        doctor_name = self.doctor.name if self.doctor else self.external_doctor or "Unknown Doctor"
        patient_name = self.patient.name if self.patient else "Unknown Patient"
        return f"Medical Code: {self.medical_record_code} - Doctor: {doctor_name} - Patient: {patient_name}"




class MedicalRecordProgress(models.Model):
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='progress_notes')
    date = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,related_name='add_progress_notes')
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    remarks = models.TextField(blank=True, null=True)

    last_modified = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    edited_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='edited_progress_notes')
   
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']



class Prescription(models.Model):
    prescription_id = models.CharField(max_length=30, null=True, blank=True, unique=True)
    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions',null=True,blank=True
    )
    patient_type = models.CharField(
        max_length=50, choices=[('IPD', 'Inpatient'), ('OPD', 'OutPatient')], null=True, blank=True
    )
    created_by = models.ForeignKey(CustomUser,on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.prescription_id:
            today = timezone.now().strftime('%y%m%d')
            record_code = f"REC{self.medical_record.id if self.medical_record else '000'}"
            suffix = uuid.uuid4().hex[:4].upper()
            self.prescription_id = f"RX-{today}-{record_code}-PRES{suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medical_record} - {self.prescription_id}"




class PrescribedMedicine(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name='medicines'
    )
    medication_type = models.ForeignKey(
        'inventory.ProductType', on_delete=models.CASCADE, null=True, blank=True
    )
    medication_category = models.ForeignKey(
        'inventory.ProductCategory', on_delete=models.CASCADE, null=True, blank=True
    )
    medication_name = models.ForeignKey('inventory.Product', on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100, default='None')
    dosage_schedule = models.CharField(
        max_length=50,
        choices=[
            ("1+0+1", "1+0+1"),
            ("1+1+0", "1+1+0"),
            ("1+1+1", "1+1+1"),
            ('0+1+1', '0+1+1'),
            ('0+1+0', '0+1+0'),
            ('0+0+1', '0+0+1'),
            ('1+0+0', '1+0+0'),
            ("Every-4-Hours", "Every 4 Hours"),
            ("Every-6-Hours", "Every 6 Hours"),
            ("Every-8-Hours", "Every 8 Hours"),
            ("Every-12-Hours", "Every 12 Hours"),
            ("Every-24-Hours", "Every 24 Hours"),
            ("As Needed", "As Needed")
        ], null=True, blank=True
    )
    medication_duration = models.IntegerField(blank=True, null=True)
    UOM = models.CharField(max_length=20, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    additional_instructions = models.TextField(blank=True, null=True)
    date_issued = models.DateField(auto_now_add=True)

    def calculate_quantity(self):
        if not self.dosage_schedule or not self.dosage or not self.medication_duration:
            return 0

        if self.dosage_schedule == "As Needed":
            return 0

        try:
            dosage_val = int(self.dosage)
        except ValueError:
            return 0

        if '+' in self.dosage_schedule:
            try:
                parts = list(map(int, self.dosage_schedule.split("+")))
                total_doses = sum(parts)
            except Exception:
                return 0
        elif "Every" in self.dosage_schedule:
            try:
                hours = int(self.dosage_schedule.split("-")[1].split("-")[0])
                total_doses = 24 // hours
            except Exception:
                return 0
        else:
            return 0

        return dosage_val * total_doses * self.medication_duration

    def save(self, *args, **kwargs):
        self.quantity = self.calculate_quantity()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medication_name.name} for {self.prescription.prescription_id}"


