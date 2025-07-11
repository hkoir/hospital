from django.db import models
from django.utils.timezone import now
from datetime import date,timedelta,datetime
from django.utils import timezone

# from core.models import Company,Employee
from accounts.models import CustomUser

import uuid

class LatePolicy(models.Model):
    WEEKDAY_CHOICES = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]
   
    policy_id = models.CharField(max_length=50,null=True,blank=True)
    company = models.ForeignKey('core.Company', on_delete=models.CASCADE,null=True,blank=True)  
    late_policy_type = models.CharField(max_length=50,choices=[('consecutive_late','Consecutive late'),('monthly_total_late','Monthly Total late')],null=True,blank=True)
   
    max_check_in_time = models.TimeField(help_text="Max allowed check-in time before considered late",null=True,blank=True)
   
    max_consecutive_late_in_before_leave_deduction = models.IntegerField(help_text="Number of consecutive lates before leave deduction",null=True,blank=True)
    max_consecutive_early_out_before_leave_deduction = models.IntegerField(help_text="Number of consecutive early clock-outs before leave deduction",null=True,blank=True)
   
    max_monthly_early_out_before_leave_deduction = models.IntegerField(help_text="Total number of early clock-outs per month before leave deduction",null=True,blank=True)
    max_monthly_late_in_before_leave_deduction = models.IntegerField(help_text="Number of times an employee can be late per month without penalty",null=True,blank=True)
   

    max_consecutive_early_out_before_salary_deduction = models.IntegerField(help_text="Number of lates allowed per month before salary deduction",null=True,blank=True)
    max_consecutive_lates_in_before_salary_deduction = models.IntegerField(help_text="Number of lates allowed per month before salary deduction",null=True,blank=True)
   
    max_monthly_early_out_before_salary_deduction = models.IntegerField(help_text="Number of lates allowed per month before salary deduction",null=True,blank=True)
    max_monthly_lates_in_before_salary_deduction = models.IntegerField(help_text="Number of lates allowed per month before salary deduction",null=True,blank=True)
  
    flexible_hours = models.BooleanField(default=False, help_text="Allow employees to compensate late time by staying late")
    senior_staff_exempt = models.BooleanField(default=True, help_text="Exclude senior employees from late penalties")
   
    salary_deduction_percentage_for_late_policy_violation = models.FloatField( help_text="Percentage of daily salary deducted for excessive lateness",null=True,blank=True)   
    leave_day_deduction_for_late_policy_violation = models.FloatField(help_text="Number of leave days deducted when late policy is violated",null=True,blank=True)
  
    biometric_tracking = models.BooleanField(default=True, help_text="Enable biometric tracking for attendance")
    auto_deduction_enabled = models.BooleanField(default=True, help_text="Automatically deduct leave or salary if limits are exceeded")
    weekened = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def get_weekends_list(self):
            """Return weekends as a list"""
            return self.weekened.split(',') if self.weekened else []

    def save(self, *args, **kwargs): 
        if not self.policy_id:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4().hex)[:6]  
            self.policy_id = f"AP-{timestamp}-{unique_id}"
        super().save(*args, **kwargs)  

    def __str__(self):
        return f"Attendance Policy for {self.company.name}"
    # today = now().strftime('%A') if today in late_policy.get_weekends_list():


class Shift(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift'),
    ]
    name = models.CharField(max_length=20, choices=SHIFT_CHOICES, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    
    
class RosterSchedule(models.Model):
    employee = models.ForeignKey('core.Employee', on_delete=models.CASCADE,null=True,blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateField()
    day_off = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('employee', 'date')  # Prevent duplicate shifts on same day

    def __str__(self):
        return f"{self.employee.name}"



class Holiday(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255, help_text="Name of the holiday (e.g., New Year's Day, Christmas)")
    holiday_date = models.DateField(help_text="Date of the holiday")
    holiday_type = models.CharField(
        max_length=50, 
        choices=[('public', 'Public Holiday'), ('company', 'Company Holiday'), ('weekly', 'Weekly Holiday')],
        default='public', 
        help_text="Type of holiday (e.g., public holiday, company holiday, weekly holiday)"
    )
    year = models.IntegerField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.holiday_date}"

    class Meta:
        ordering = ['holiday_date']



class AttendanceLog(models.Model):
    employee = models.ForeignKey('core.Employee', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.name} - {self.date} - {self.check_in_time} to {self.check_out_time}"
    


class AttendanceModel(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    employee = models.ForeignKey('core.Employee', on_delete=models.CASCADE, related_name='employee_attendance')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='shift_attendance', null=True, blank=True)
    date = models.DateField()
    first_check_in = models.TimeField()  # The employee's check-in time
    last_check_out = models.TimeField()  # The employee's check-out time
    total_hours_worked = models.DurationField(null=True, blank=True)
    
    attendance_status_choices = [
        ('present', 'present'),
        ('absent', 'absent'),
        ('weekend', 'weekend'),
        ('holiday', 'holiday'),
    ]
    attendance_status = models.CharField(max_length=50, choices=attendance_status_choices, default='None')
    is_late = models.BooleanField(default=False)
    left_early = models.BooleanField(default=False)
    leave_deducted = models.BooleanField(default=False)
    salary_deducted = models.BooleanField(default=False) 
    flexible_hours_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total_hours(self):
        if self.first_check_in and self.last_check_out:
            check_in = datetime.combine(date.today(), self.first_check_in)
            check_out = datetime.combine(date.today(), self.last_check_out)
            duration = check_out - check_in
            total_hours = duration.total_seconds() / 3600  # Convert seconds to hours
            return round(total_hours, 2)
        else:
            return 0.0 

    def save(self, *args, **kwargs):
        self.total_hours_worked = timedelta(hours=self.calculate_total_hours())         
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.date}"



class LeaveType(models.Model):  
    LEAVE_TYPES = [
        ('ANNUAL', 'Annual Leave'),
        ('SICK', 'Sick Leave'),
        ('CASUAL', 'Casual Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('EARNED', 'Earned Leave'),
        ('COMPENSATORY', 'Compensatory Leave'),
        ('UNPAID', 'Unpaid Leave'),
        ('BEREAVEMENT', 'Bereavement Leave'),
        ('STUDY', 'Study Leave'),
        ('HALF-DAY', 'Half-Day Leave'),
        ('MARRIAGE', 'Marriage Leave'),
        ('SPECIAL', 'Special Leave'),
    ]

    name = models.CharField(max_length=50, choices=LEAVE_TYPES,null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    annual_allowance = models.PositiveIntegerField(default=0)
    allow_carry_forward = models.BooleanField('? is carry forwardable',default=False)
    max_carry_forward_limit = models.PositiveIntegerField(default=0, blank=True, null=True)  # New field
    accrues_monthly = models.BooleanField('Is monthly accurable',default=False)  # New Field
    accrual_rate = models.DecimalField(max_digits=5, decimal_places=2,null=True,blank=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.accrues_monthly and self.annual_allowance > 0:
            self.accrual_rate = self.annual_allowance / 12
        else:
            self.accrual_rate = 0
        super().save(*args, **kwargs)
   
    def __str__(self):
        return self.name


class LeaveApplication(models.Model):
    application_id = models.CharField(max_length=30,null=True,blank=True)
    employee = models.ForeignKey('core.Employee', on_delete=models.CASCADE,null=True, blank=True)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE,null=True, blank=True)
    applied_start_date = models.DateField()
    applied_end_date = models.DateField()
    applied_no_of_days=models.PositiveBigIntegerField(null=True, blank=True)
    applied_reason = models.TextField(null=True, blank=True)
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    applied_on = models.DateTimeField(auto_now_add=True)
    approved_start_date = models.DateField(null=True, blank=True)
    approved_end_date = models.DateField(null=True, blank=True)
    approved_no_of_days=models.PositiveBigIntegerField(null=True, blank=True)
    approved_on = models.DateTimeField(default=timezone.now)
    rejection_reason = models.TextField(null=True, blank=True)
   
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.application_id:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4().hex)[:6]  
            self.application_id = f"AP-{timestamp}-{unique_id}"

        if self.applied_end_date and self.applied_start_date:
            self.applied_no_of_days = (self.applied_end_date - self.applied_start_date).days

        if self.approved_end_date and self.approved_start_date:
            self.approved_no_of_days = (self.approved_end_date - self.approved_start_date).days
       
        super().save(*args, **kwargs)

  

    def __str__(self):
        return f"{self.employee} - {self.leave_type.name}"



class EmployeeLeaveBalance(models.Model):    
    employee = models.ForeignKey('core.Employee', on_delete=models.CASCADE,null=True, blank=True)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE,related_name='leave_balance',null=True, blank=True)
    balance = models.PositiveIntegerField(default=0,null=True, blank=True)  
    carry_forward = models.PositiveIntegerField(default=0) 
    year = models.PositiveIntegerField(default=timezone.now().year) 
    total_available = models.PositiveIntegerField(null=True, blank=True)
    last_accrued_month = models.IntegerField(default=0,null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.balance and self.carry_forward:
            self.total_available= (self.balance - self.carry_forward)
        elif not self.carry_forward :
            self.total_available = self.balance 
       
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.leave_type} - {self.year}"
    


class LeaveBalanceHistory(models.Model):
    employee = models.ForeignKey('core.Employee', on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    change = models.DecimalField(max_digits=5, decimal_places=2,blank=True, null=True)  # e.g., -1 for deduction, +1 for accrual
    reason = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(default=now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee} | {self.leave_type} | {self.change} | {self.date}"



class SalaryDeductionRecord(models.Model):
    employee = models.ForeignKey('core.Employee', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Salary deduction amount
    reason = models.TextField()
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.name} - {self.amount} deducted on {self.date}"
