from django.db import models
from core.models import Doctor
from medical_records.models import MedicalRecord
import uuid
from django.utils import timezone

import qrcode
from django.core.files.base import ContentFile

class LabTestCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Example: "Blood Tests", "Radiology"
    LAB_SERVICES = [
    ('Lab_Test', 'Lab / Diagnostic Test'),
    ('Radiology', 'Radiology / Imaging (X-ray, USG, CT, MRI)'),
    ('ECG', 'ECG / EEG / EMG'),
    ('Procedure', 'Minor Procedures'),
    ]
    service_type = models.CharField(max_length=50, choices=LAB_SERVICES,null=True,blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)


    def __str__(self):
        return self.name




class LabTestCatalog(models.Model):  # New model
    lab_test_catelogue_code = models.CharField(max_length=30,null=True,blank=True,unique=True)
    category=models.ForeignKey(LabTestCategory,on_delete=models.CASCADE,null=True,blank=True)
    test_type = models.CharField(max_length=100)
    test_name = models.CharField(max_length=255, unique=True)  
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True,blank=True)


    def save(self, *args, **kwargs):
        if not self.lab_test_catelogue_code :            
            self.lab_test_catelogue_code  = f"LTC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)    

    def __str__(self):
        return f"{self.test_name} ({self.test_type})"





class LabTest(models.Model):
    lab_test_code = models.CharField(max_length=30,null=True,blank=True,unique=True)
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE,related_name='lab_tests_medical_records',blank=True, null=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,blank=True, null=True)
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE,blank=True, null=True)  
    test = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE,blank=True, null=True)
    test_type = models.CharField(max_length=100,blank=True, null=True)
    test_name = models.CharField(max_length=255, unique=True,blank=True, null=True)  
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending',blank=True, null=True)
    created_at= models.DateField(auto_now_add=True)
    updated_at= models.DateField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.lab_test_code:            
            self.lab_test_code = f"LTC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)                  


    def __str__(self):
        return f"{self.test.test_name}-{self.test.test_type}"



from medical_records.models import MedicalRecordProgress

class LabTestRequest(models.Model):
    requested_lab_test_code = models.CharField(max_length=20,null=True,blank=True)
    patient_type = models.CharField(max_length=50, choices=[
        ('IPD', 'Inpatient'), ('OPD', 'OutPatient'),
        ('External-Lab-Test', 'External Lab Test'), ('Emergency', 'Emergency')
    ], null=True, blank=True)

    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE,
        related_name='lab_tests_requests',null=True,blank=True
    )
    progress = models.ForeignKey(MedicalRecordProgress, on_delete=models.CASCADE, null=True, blank=True)
    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.CASCADE,
        related_name='appointment_labtest_request',null=True,blank=True
    )
    requested_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    external_ref = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'), ('Completed', 'Completed')
    ], default='Pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def all_samples_collected(self):       
        items = self.test_items.all()          
        for item in items:
            sample = item.sample_items.first()  # first sample per item
            if not sample or sample.status not in [ 'collected','received','processing','completed']:
                return False
        return True

    def save(self, *args, **kwargs):
        if not self.requested_lab_test_code:
            today = timezone.now().strftime("%Y%m%d")
            prefix = f"RLT-{today}"
            last_record = LabTestRequest.objects.filter(
                requested_lab_test_code__startswith=prefix
            ).order_by('-id').first()

            if last_record:
                last_number = int(last_record.requested_lab_test_code.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.requested_lab_test_code = f"{prefix}-{new_number:04d}"
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Request #{self.requested_lab_test_code} for MR #{self.medical_record.medical_record_code}-patient-{self.medical_record.patient.name}"



class LabTestRequestItem(models.Model):
    labtest_request = models.ForeignKey(
        LabTestRequest, on_delete=models.CASCADE,
        related_name='test_items'
    )
    lab_test = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE)
    prescription = models.ForeignKey('medical_records.Prescription', on_delete=models.CASCADE,
	 null=True, blank=True,related_name='pres_lab_req_items')
    progress = models.ForeignKey(MedicalRecordProgress, on_delete=models.CASCADE, null=True)
    priority = models.CharField(max_length=20, choices=[
        ('Normal', 'Normal'), ('Urgent', 'Urgent')
    ], default='Normal')

    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'), ('Completed', 'Completed')
    ], default='Pending')

    def __str__(self):
        return f"{self.lab_test} in Request #{self.labtest_request.id}"



class SuggestedLabTestRequest(models.Model):
    suggested_lab_test_code = models.CharField(max_length=20,null=True,blank=True)
    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.CASCADE,
        related_name='appointment_labtest',null=True,blank=True
    )
    patient_type = models.CharField(max_length=50, choices=[
        ('IPD', 'Inpatient'), ('OPD', 'OutPatient'),
        ('External-Lab-Test', 'External Lab Test'), ('Emergency', 'Emergency')
    ], null=True, blank=True)

    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE,
        related_name='suggested_lab_test_groups'
    )
    suggested_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'), ('Partially Completed', 'Partially Completed'), ('Completed', 'Completed')
    ], default='Pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.suggested_lab_test_code:
            today = timezone.now().strftime("%Y%m%d")
            prefix = f"SLT-{today}"
            last_record = SuggestedLabTestRequest.objects.filter(
                suggested_lab_test_code__startswith=prefix
            ).order_by('-id').first()

            if last_record:
                last_number = int(last_record.suggested_lab_test_code.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.suggested_lab_test_code = f"{prefix}-{new_number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Suggestion #{self.id} for MR #{self.medical_record.id}"
    



class SuggestedLabTestItem(models.Model):
    suggested_labtest = models.ForeignKey(
        SuggestedLabTestRequest, on_delete=models.CASCADE,
        related_name='suggested_items'
    )
    lab_test = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE)
    prescription = models.ForeignKey('medical_records.Prescription', on_delete=models.CASCADE, null=True, blank=True,related_name='pres_lab_suggest_items')
    progress = models.ForeignKey(MedicalRecordProgress, on_delete=models.CASCADE, null=True)
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'), ('Requested', 'Requested'), ('Completed', 'Completed')
    ], default='Pending')

    def __str__(self):
        return f"{self.lab_test} in Suggestion #{self.suggested_labtest.id}"



from accounts.models import CustomUser
from barcode import Code128
from barcode.writer import ImageWriter   
from django.core.files import File
from io import BytesIO

class LabSampleCollection(models.Model):
    SAMPLE_STATUS = [
        ('pending', 'Pending Collection'),
        ('collected', 'Collected'),
        ('received', 'Received in Lab'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]

    request_order = models.ForeignKey(LabTestRequest, on_delete=models.CASCADE, related_name="samples")
    request_item = models.ForeignKey(LabTestRequestItem, on_delete=models.CASCADE, related_name="sample_items")
    sample_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    sample_type = models.CharField(
        max_length=50,
        choices=[
            ("Blood", "Blood"),
            ("Urine", "Urine"),
            ("Stool", "Stool"),
            ("Sputum", "Sputum"),
            ("Swab", "Swab"),
            ("Other", "Other"),
        ]
    )
    barcode = models.CharField(max_length=100, unique=True)
    barcode_image = models.ImageField(upload_to="barcodes/", blank=True, null=True)
    collected_by = models.ForeignKey(
        CustomUser, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="collected_samples"
    )
    collected_at = models.DateTimeField(null=True, blank=True)    
    status = models.CharField(max_length=20, choices=SAMPLE_STATUS, default='pending')
    notes = models.TextField(null=True, blank=True)
  
    def save(self, *args, **kwargs):
        if not self.sample_id:
            self.sample_id = f"SMP-{uuid.uuid4().hex[:6].upper()}"
        if not self.barcode:
            self.barcode = str(uuid.uuid4()).replace("-", "")[:12]       

        buffer = BytesIO()
        barcode_obj = Code128(self.barcode, writer=ImageWriter())
        barcode_obj.write(buffer)
        file_name = f"{self.barcode}.png"
        self.barcode_image.save(file_name, File(buffer), save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sample_id} - {self.sample_type}"



class LabTestResultOrder(models.Model):   
     patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
     lab_test_request = models.ForeignKey(LabTestRequest,on_delete=models.CASCADE,null=True,blank=True,related_name='lab_test_result_order')
     lab_test_result_oder_code= models.CharField(max_length=30,null=True,blank=True,unique=True)
     medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name="test_results")
     test_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE,blank=True, null=True,related_name='labtest_doctor') 
     test_assistance = models.ForeignKey(Doctor, on_delete=models.CASCADE,blank=True, null=True,related_name='labtest_assistance') 
     summary_report = models.TextField(blank=True, null=True) 
     reviewed_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviewed_lab_tests")
     approved_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, blank=True, null=True, related_name="approved_lab_tests")
     recorded_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
     status = models.CharField(
        max_length=50, 
        choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('Completed', 'Completed'), ('Delivered', 'Delivered')],
        default='Pending')
     qr_code = models.ImageField( upload_to='lab_qr_codes/',null=True, blank=True)

     def generate_qr_code(self):      
        qr_data = f"Report ID: {self.lab_test_result_oder_code}\nPatient: {self.medical_record.patient.name}"
        qr_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        file_name = f"lab_report_qr_{self.id}.png"
        self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)

     def save(self, *args, **kwargs):
        if not self.lab_test_result_oder_code:
            today = timezone.now().strftime("%Y%m%d")
            prefix = f"ROLT-{today}"
            last_record = LabTestResultOrder.objects.filter(
                lab_test_result_oder_code__startswith=prefix
            ).order_by('-id').first()

            if last_record:
                last_number = int(last_record.lab_test_result_oder_code.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            self.lab_test_result_oder_code = f"{prefix}-{new_number:04d}"
        super().save(*args, **kwargs)

        if not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=['qr_code'])


class LabTestResult(models.Model):  
    patient_type =  models.CharField(max_length=50,choices=[
        ('IPD','Inpatient'),('OPD','OutPatient'),
        ('External-Lab-Test','External Lab Test'),
        ('Emergency','Emergency')
        ],null=True,blank=True) 
    result_order = models.ForeignKey(LabTestResultOrder, on_delete=models.CASCADE, related_name="results", blank=True, null=True) 
    test_name = models.ForeignKey(LabTestCatalog,on_delete=models.CASCADE,null=True,blank=True)
    test_value = models.CharField(max_length=255,blank=True, null=True) 
    standard_value = models.CharField(max_length=255, blank=True, null=True)  
    findings = models.TextField(blank=True, null=True)  
    report_file = models.FileField(upload_to='lab_reports/', blank=True, null=True)        
    prescription = models.ForeignKey('medical_records.Prescription', on_delete=models.CASCADE, null=True, blank=True,related_name='pres_lab_result_items')
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True, null=True)  # Optional comments from doctor or lab
    status = models.CharField(
        max_length=50, 
        choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('Completed', 'Completed')],
        default='Pending'
    )

    def __str__(self):
        return f"Result for {self.result_order.medical_record}.. status: ({self.status})"




class ExternalLabVisit(models.Model):
    lab_test_request =models.ForeignKey(LabTestRequest,on_delete=models.CASCADE,null=True,blank=True,related_name="external_lab_tests")
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,blank=True, null=True)
    doctor_ref= models.CharField(max_length=255, blank=True, null=True)   
    medical_record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE, related_name='external_lab_visit',blank=True, null=True)
    doctor = models.ForeignKey(Doctor,on_delete=models.CASCADE,null=True,blank=True,related_name='external_test_doctors')
    prescription_file = models.FileField(upload_to='external_prescriptions/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=50, 
        choices=[('Pending', 'Pending'), ('Completed', 'Completed')],
        default='Pending'
    )
    invoice = models.OneToOneField('billing.BillingInvoice', on_delete=models.CASCADE,related_name="external_lab_visit_invoices",null=True,blank=True)
    medical_record = models.OneToOneField(MedicalRecord, on_delete=models.CASCADE,related_name="external_lab_visit_medical_records",null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"External Lab Visit: {self.patient} ({self.status})"
