
from django.db import models
from django.contrib.auth.models import User

from accounts.models import UserProfile
from decimal import Decimal
from django.utils import timezone
from datetime import datetime
from core.utils import DEPARTMENT_CHOICES,EMPLOYEE_LEVEL_CHOICES,POSITION_CHOICES,LOCATION_CHOICES
import uuid
from accounts.models import CustomUser



class Notice(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255,null=True,blank=True)
    content = models.TextField(null=True,blank=True)
    notice_attachment = models.ImageField(upload_to='notices',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title




class Department(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100,choices=DEPARTMENT_CHOICES)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Employeelevel(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100,choices=EMPLOYEE_LEVEL_CHOICES)  
    description = models.TextField(null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
            return self.name



class Position(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, choices=POSITION_CHOICES)    
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="positions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    



class JobRequirement(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)    
    department = models.ForeignKey(Department, on_delete=models.CASCADE,null=True, blank=True)  
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="requirements",null=True, blank=True)  # ✅ Related name added
    requirement = models.TextField()     
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.position.name} - {self.requirement}"  




class JobDescription(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)  
    department = models.ForeignKey(Department, on_delete=models.CASCADE,null=True, blank=True)  
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="descriptions",null=True, blank=True)  # ✅ Related name added
    description = models.TextField()     
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.position.name} - {self.description}"  





class Company(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='company_hq_user')
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logo/',blank=True, null=True)
    contact_person = models.CharField(max_length=30,null=True,blank=True)
    phone = models.IntegerField(null=True,blank=True)
    email= models.EmailField(null=True,blank=True)
    website = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.name




class Location(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='company_location_user')
    company = models.ForeignKey(Company, related_name='company_locations', on_delete=models.CASCADE,null=True, blank=True)
    name = models.CharField(max_length=255,null=True, blank=True,choices=LOCATION_CHOICES)
       
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20,null=True, blank=True)
    email = models.EmailField(null=True, blank=True)    
    city = models.CharField(max_length=100,null=True,blank=True)
    state = models.CharField(max_length=100,null=True,blank=True)
    country = models.CharField(max_length=100,null=True,blank=True)
    postal_code = models.CharField(max_length=20,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'core'

    def __str__(self):
        return f"{self.name}"
    


class Shareholder(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100)
    percentage_share = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 25.00 for 25%
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f" {self.name}-company{self.company}"





   
class PoliciesAndGuideline(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,null=True,blank=True)
    workplace_security_policies = models.ImageField(upload_to='workplace_security_policies',null=True,blank=True)
    workplace_health_safety = models.ImageField(upload_to='workplace_health_safety',null=True,blank=True)
    equal_opportunity_policy = models.ImageField(upload_to='equal_opportunity_policy',null=True,blank=True)
    employee_code_of_conduct_policy = models.ImageField(upload_to='employee_code_of_conduct_policy ',null=True,blank=True)
    leave_of_absence_policy = models.ImageField(upload_to='leave_of_absence_policy',null=True,blank=True)
    employee_disciplinary_action_policy = models.ImageField(upload_to='employee_disciplinary_action_policy',null=True,blank=True)
    travel_policies = models.ImageField(upload_to='travel_policies',null=True,blank=True)
    remote_work_policy = models.ImageField(upload_to=' remote_work_policy',null=True,blank=True)
    work_schedule_and_rest_period_policies = models.ImageField(upload_to='work_schedule_and_rest_period_policies',null=True,blank=True)
    ethics_policy = models.ImageField(upload_to='ethics_policy',null=True,blank=True)
    employee_complaint_policies = models.ImageField(upload_to='employee_complaint_policies',null=True,blank=True)
    compensation_and_benefits_policy = models.ImageField(upload_to='compensation_and_benefits_policy',null=True,blank=True)
    employee_fraternization_policy = models.ImageField(upload_to='employee_fraternization_policy',null=True,blank=True)   
    BYOD = models.ImageField(upload_to='BYOD',null=True,blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f" {self.company}"


class CompanyPolicy(models.Model):
    name =models.CharField(max_length=30,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    policy_code = models.CharField(max_length=30,null=True,blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True,blank=True)
    hra_percentage = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    medical_allowance_percentage = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True)
    conveyance_allowance_percentage = models.DecimalField(max_digits=5,decimal_places=2, null=True, blank=True)
    performance_bonus_percentage = models.DecimalField(max_digits=5,decimal_places=2, null=True, blank=True)
    festival_bonus_percentage = models.DecimalField(max_digits=5,decimal_places=2,null=True, blank=True)
    provident_fund_percentage = models.DecimalField(max_digits=5,decimal_places=2,null=True, blank=True)
    professional_tax = models.DecimalField(max_digits=10,decimal_places=2,null=True, blank=True)
    grauity_percentage = models.DecimalField(max_digits=5,decimal_places=2,null=True, blank=True)
    leave_travel_allowance_performance = models.DecimalField(max_digits=5,decimal_places=2,null=True, blank=True)
    office_start_time = models.TimeField(null=True, blank=True)
    office_end_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.policy_code:
            self.policy_code = f"CPC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Policy: {self.policy_code}-{self.name}"


class Festival(models.Model):
    year = models.IntegerField(null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50,null=True,blank=True,help_text='any name you prefer')
    company_policy = models.ForeignKey(CompanyPolicy, on_delete=models.CASCADE)   
    month = models.PositiveIntegerField(help_text='use numerical month like 1,2 etc. 1=January, 2=February')  
    description =models.CharField(max_length=255,null=True,blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    def __str__(self):
        return f"{self.name} ({self.month})"
    


class PerformanceBonus(models.Model):
    year = models.IntegerField(null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50,null=True,blank=True,help_text='any name you prefer')
    company_policy = models.ForeignKey(CompanyPolicy, on_delete=models.CASCADE)
    month = models.PositiveIntegerField(help_text='use numerical month like 1=January, 2=February')
    description =models.CharField(max_length=255,null=True,blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    def __str__(self):
        return f"{self.name} ({self.month})"


class SalaryStructure(models.Model):
    name =models.CharField(max_length=30,null=True,blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    salary_structure_code = models.CharField(max_length=50,null=True,blank=True)
    company_policy = models.ForeignKey(CompanyPolicy,on_delete=models.CASCADE,null=True,blank=True)

    SALARY_LEVEL_CHOICES =[
        ('LEVEL-1','Level-1'),
        ('LEVEL2','Level-2'),
        ('LEVEL-3','Level-3'),
        ('LEVEL-4','Level-4'),
        ('LEVEL-5','Level-5'),
        ('LEVEL-6','Level-6'),
        ('LEVEL-7','Level-7'),
        ('LEVEL-8','Level-8'),
        ('LEVEL-9','Level-9'),
        ('LEVEL-10','Level-10'),
    ]
    salary_level = models.CharField(max_length=50,choices= SALARY_LEVEL_CHOICES,null=True,blank=True)   

    basic_salary = models.DecimalField(max_digits=15, decimal_places=2, help_text="Base salary of the employee",null=True,blank=True)
    car_entitle_status = models.BooleanField("Entitled to a car?", default=False,null=True,blank=True)   
    food_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True,blank=True, help_text="Allowance for meals or food")
    insurance = models.BooleanField('Cover insurance policy?', default=False,null=True,blank=True)
    stock_options = models.BooleanField('have stock option?', default=False,null=True,blank=True)   
    overtime_pay_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True, help_text="Rate per hour for overtime work")    
    income_tax_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,null=True,blank=True, help_text="Income tax deduction")
    created_at=models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    @property
    def hra(self): return (self.basic_salary * self.company_policy.hra_percentage) / 100
    @property
    def medical_allowance(self):return (self.basic_salary * self.company_policy.medical_allowance_percentage) / 100
    @property
    def conveyance_allowance(self): return (self.basic_salary * self.company_policy.conveyance_allowance_percentage) / 100
    @property
    def performance_bonus(self): return (self.basic_salary * self.company_policy.performance_bonus_percentage) / 100
    @property
    def festival_allowance(self): return (self.basic_salary * self.company_policy.festival_bonus_percentage) / 100
    @property
    def provident_fund(self): return (self.basic_salary * self.company_policy.provident_fund_percentage) / 100
    @property
    def gratuity(self): return (self.basic_salary * self.company_policy.grauity_percentage) / 100
    @property
    def professional_tax(self): return (self.basic_salary * self.company_policy.professional_tax) / 100
    @property
    def income_tax(self): return (self.basic_salary * self.income_tax_percentage) / 100

    def is_festival_month(self):   
        return Festival.objects.filter(
            company_policy=self.company_policy,
            month=datetime.now().month
        ).exists()
    
    def is_performance_bonus_month(self):   
        return PerformanceBonus.objects.filter(
            company_policy=self.company_policy,
            month=datetime.now().month
        ).exists()

    

    def gross_salary(self):
        base_gross_salary= (
            self.basic_salary
            + self.hra
            + self.medical_allowance
            + self.conveyance_allowance        
             + self.performance_bonus  
             + self.festival_allowance  
        )
    
        if self.is_festival_month():
            base_gross_salary += self.festival_allowance
        if self.is_performance_bonus_month():
            base_gross_salary += self.performance_bonus
        if self.is_festival_month() and self.is_performance_bonus_month():
            base_gross_salary += self.performance_bonus + self.festival_allowance

        return base_gross_salary
    
    def net_salary(self):
        return (
            self.gross_salary()
            - self.professional_tax
            - self.income_tax    
            - self.provident_fund     
            - self.gratuity 
        )
    
    def save(self, *args, **kwargs):
        if not self.salary_structure_code:
            self.salary_structure_code = f"SSC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)  
                

    def __str__(self):
        return f"Salary Structure: {self.name}-{self.salary_level}"


from core.utils import EMPLOYEE_LEVEL_CHOICES
from leavemanagement.models import LatePolicy

class Employee(models.Model):  
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    employee_code = models.CharField(max_length=100, null=True, blank=True)  
    name = models.CharField(max_length=100, null=True, blank=True,default="Nome")  
    first_name = models.CharField(max_length=100, null=True, blank=True,default="Nome")
    last_name = models.CharField(max_length=100,null=True, blank=True,default="Nome")   
    phone = models.IntegerField(null=True,blank=True)
    email = models.EmailField(null=True, blank=True)
    father_name = models.CharField(max_length=100,null=True, blank=True,default="Nome") 
    mother_name = models.CharField(max_length=100,null=True, blank=True,default="Nome") 
    
               
    company = models.ForeignKey(Company,on_delete=models.CASCADE,null=True, blank=True,related_name='employee_company')    
    department = models.ForeignKey(Department,on_delete=models.CASCADE,null=True, blank=True,related_name='employee_department')   
    position = models.ForeignKey(Position,on_delete=models.CASCADE,null=True, blank=True,related_name='employee_position')            
    location = models.ForeignKey(Location,on_delete=models.SET_NULL,null=True,blank=True,related_name='employee_location')   
    
    is_roster_employee = models.BooleanField(default=False)
    is_senior_employee =models.BooleanField(default=False)    
    employee_level = models.CharField(max_length=200,choices=EMPLOYEE_LEVEL_CHOICES,null=True,blank=True)
    salary_structure=models.ForeignKey(SalaryStructure,on_delete=models.CASCADE,null=True,blank=True)
    late_policy = models.ForeignKey(LatePolicy,on_delete=models.CASCADE,null=True,blank=True)
    office_start_time = models.TimeField(null=True, blank=True)
    office_end_time = models.TimeField(null=True, blank=True)
    flexible_hours = models.BooleanField(default=False, help_text="Whether the employee is allowed flexible hours.")
    lateness_salary_deductions = models.FloatField(default=0.0, help_text="Total deducted amount due to lateness or penalties",null=True,blank=True)
         
    gender_choices =[
        ('Male','Male'),
        ('Female','Female'),
        ('Others', 'Others')
    ]   
    gender = models.CharField(max_length=20,choices= gender_choices,null=True, blank=True,default="Nome")
    state = models.CharField(max_length=50,null=True,blank=True)
    district = models.CharField(max_length=50,null=True,blank=True)
    city = models.CharField(max_length=50,null=True,blank=True)
    postal_code = models.CharField(max_length=50,null=True,blank=True)
    address=models.TextField(null=True,blank=True)    
  
    employee_photo_ID = models.ImageField(upload_to='employee_photo_ID/', null=True, blank=True) 
    employee_education_certificate = models.ImageField(upload_to='employee_edu/', null=True, blank=True,help_text='pls upload single image file') 
    employee_NID = models.ImageField(upload_to='employee_nid/', null=True, blank=True,help_text='pls upload single image file')     
    
    joining_date = models.DateField(null=True,blank=True)
    resignation_date = models.DateField(null=True, blank=True, default=timezone.now, help_text="Format: YYYY-MM-DD")
                   
    created_at=models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.employee_code or self.employee_code == 'None':
            self.employee_code = f"EMP-{uuid.uuid4().hex[:8].upper()}"
        
        super().save(*args, **kwargs)

            
    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    

class EmployeeGratuityProvidentFund(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    salary_disbursed = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    provident_fund = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gratuity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.year = timezone.now().year
        self.month = timezone.now().month
        self.salary_disbursed = self.employee.salary_structure.net_salary()
        self.provident_fund = self.employee.salary_structure.provident_fund
        self.gratuity = self.employee.salary_structure.gratuity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.employee.name} ({self.month}/{self.year})'
    
    # example usage  EmployeeGratuityProvidentFund.objects.create(employee=employee)





from django.db.models import Sum
from.utils import SPECIALIZATION_CHOICES 

class Specialization(models.Model):
    name = models.CharField(max_length=100,choices=SPECIALIZATION_CHOICES , unique=True) 
    description = models.TextField(blank=True, null=True)   
    image = models.ImageField(upload_to='specializations/', blank=True, null=True)  
    treatments = models.TextField(blank=True, null=True) 

    def __str__(self):
        return self.name
    


class Doctor(Employee):      
    specialization = models.ForeignKey(Specialization,on_delete=models.CASCADE,related_name="specialized_doctors",null=True, blank=True)
    medical_license_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.TextField(
        null=True, blank=True, 
        help_text="Provide a short  bio"
    )
    education = models.TextField(null=True, blank=True, help_text="Degrees and certifications")
    experience_years = models.PositiveIntegerField(null=True, blank=True, help_text="Years of medical experience")
    hospital_affiliations = models.TextField(null=True, blank=True, help_text="List of hospitals/clinics affiliated with")
    memberships = models.TextField(null=True, blank=True, help_text="Medical associations or memberships")
    awards = models.TextField(null=True, blank=True, help_text="Recognitions or achievements")
    language = models.CharField(max_length=255, null=True, blank=True)
    doctor_location= models.CharField(max_length=255, null=True, blank=True)
    start_time = models.TimeField(help_text="Doctor's available start time", null=True, blank=True)
    end_time = models.TimeField(help_text="Doctor's available end time", null=True, blank=True)
    consultation_fees = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)

    def __str__(self):
        return self.name if  self.name else 'Unnamed Doctor'


class Nurse(Employee):
    ward = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True,blank=True)
    nurse_license_number = models.CharField(max_length=100, unique=True, null=True, blank=True)





class SalaryIncrementAndPromotion(models.Model):
    INCREMENT_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('HALF-YEARLY', 'Half Yearly'),
        ('YEARLY', 'Yearly'),
    ]

    MONTH_CHOICES = [
        ('JANUARY', 'January'),
        ('FEBRUARY', 'February'),
        ('MARCH', 'March'),
        ('APRIL', 'April'),
        ('MAY', 'May'),
        ('JUNE', 'June'),
        ('JULY', 'July'),
        ('AUGUST', 'August'),
        ('SEPTEMBER', 'September'),
        ('OCTOBER', 'October'),
        ('NOVEMBER', 'November'),
        ('DECEMBER', 'December'),
    ]

    QUARTER_CHOICES = [
        ('1ST-QUARTER', '1st Quarter'),
        ('2ND-QUARTER', '2nd Quarter'),
        ('3RD_QUARTER', '3rd Quarter'),
        ('4TH-QUARTER', '4th Quarter'),
    ]

    HALF_YEAR_CHOICES = [
        ('1ST-HALF-YEAR', 'First Half Year'),
        ('2ND-HALF-YEAR', 'Second Half Year'),
    ]

    PROMOTION_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    appraisal_year = models.IntegerField(blank=True, null=True)
    appraisal_category = models.CharField(max_length=30,choices=[('BY_EMPLOYEE','By Employee'),('BY_DEPARTMENT','By department'),('BY_POSITION','By Position'),('BY_COMPANY','By Company')],blank=True, null=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='increment_employee',blank=True, null=True)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='increment_position',blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='increment_department',blank=True, null=True)
    
    appraisal_type = models.CharField(max_length=30, choices=INCREMENT_TYPE_CHOICES,blank=True, null=True)
    month = models.CharField(max_length=30, choices=MONTH_CHOICES, blank=True, null=True)
    quarter = models.CharField(max_length=30, choices=QUARTER_CHOICES, blank=True, null=True)
    half_year = models.CharField(max_length=30, choices=HALF_YEAR_CHOICES, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)

    salary_increment_percentage = models.FloatField(blank=True, null=True)
    promotional_increment_percentage = models.FloatField(blank=True, null=True)
    obtained_salary_increment_percentage = models.FloatField(blank=True, null=True)
    obtained_promotional_increment_percentage = models.FloatField(blank=True, null=True)
    salary_increment_amount = models.FloatField(blank=True, null=True)
    promotional_increment_amount = models.FloatField(blank=True, null=True)
    new_basic_salary = models.FloatField(blank=True, null=True)
    obtained_promotion_recommendation = models.CharField(max_length=10, choices=PROMOTION_CHOICES,blank=True, null=True)
    promotion_recommendation = models.CharField(max_length=10, choices=PROMOTION_CHOICES,blank=True, null=True)
    max_task_count = models.IntegerField(blank=True, null=True)  # New field
    task_count_employee = models.IntegerField(blank=True, null=True)  
    task_factor = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)  # New field
    avg_task_count = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)  # New field
    final_score = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)  # New field
    weighted_final_score = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)  # New field
           
    effective_date = models.DateField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'appraisal_type', 'appraisal_year')

    def save(self, *args, **kwargs):
        existing_record = SalaryIncrementAndPromotion.objects.filter(
            employee=self.employee,
            appraisal_year=self.appraisal_year
        ).first()

        if existing_record and existing_record.appraisal_type != self.appraisal_type: 
            self.pk = None  
        super().save(*args, **kwargs)

    def __str__(self):
        if self.employee:      
            return f'{self.employee.name}'
        else:
            return f'Unknown'



class EmployeeRecordChange(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(default=timezone.now)
    field_name = models.CharField(max_length=100,default="None")
    old_value = models.CharField(max_length=255, default="None")
    new_value = models.CharField(max_length=255,default="None" )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class MonthlySalaryReport(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.IntegerField()  # Month number (e.g., 1 for January)
    year = models.IntegerField()
    total_working_hours = models.DecimalField(max_digits=5, decimal_places=2 , null=True, blank=True )
    total_salary = models.DecimalField(max_digits=10, decimal_places=2 , null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

