from django.db import models
from core.models import Doctor
from medical_records.models import MedicalRecord
import uuid
from django.utils import timezone



class LabTestCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Example: "Blood Tests", "Radiology"
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name




class LabTestCatalog(models.Model):  # New model
    lab_test_catelogue_code = models.CharField(max_length=30,null=True,blank=True,unique=True)
    category=models.ForeignKey(LabTestCategory,on_delete=models.CASCADE,null=True,blank=True)
    test_type = models.CharField(max_length=100)
    test_name = models.CharField(max_length=255, unique=True)  
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

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





class LabTestRequest(models.Model):
    patient_type = models.CharField(max_length=50, choices=[
        ('IPD', 'Inpatient'), ('OPD', 'OutPatient'),
        ('External-Lab-Test', 'External Lab Test'), ('Emergency', 'Emergency')
    ], null=True, blank=True)

    medical_record = models.ForeignKey(
        MedicalRecord, on_delete=models.CASCADE,
        related_name='lab_tests_requests',null=True,blank=True
    )
    requested_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'), ('Completed', 'Completed')
    ], default='Pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Request #{self.pk} for MR #{self.medical_record.id}"



class LabTestRequestItem(models.Model):
    labtest_request = models.ForeignKey(
        LabTestRequest, on_delete=models.CASCADE,
        related_name='test_items'
    )
    lab_test = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE)
    
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

    def __str__(self):
        return f"Suggestion #{self.id} for MR #{self.medical_record.id}"
    



class SuggestedLabTestItem(models.Model):
    suggested_labtest = models.ForeignKey(
        SuggestedLabTestRequest, on_delete=models.CASCADE,
        related_name='suggested_items'
    )
    lab_test = models.ForeignKey(LabTestCatalog, on_delete=models.CASCADE)
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'), ('Requested', 'Requested'), ('Completed', 'Completed')
    ], default='Pending')

    def __str__(self):
        return f"{self.lab_test} in Suggestion #{self.suggested_labtest.id}"






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
        default='Pending'
    )
     
     def save(self, *args, **kwargs):
        if not self.lab_test_result_oder_code:
            year = timezone.now().strftime("%y")  # Last 2 digits of year
            self.lab_test_result_oder_code = f"{year}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)   



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
