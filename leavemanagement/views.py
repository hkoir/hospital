from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator

from .forms import LeaveApplicationForm,LeaveTypeForm,ApprovalForm
from.models import LeaveApplication,EmployeeLeaveBalance,LeaveType
from .models import EmployeeLeaveBalance

from django.urls import reverse
from django.core.management.base import BaseCommand

from django.db.models import Sum
from .forms import ApprovalForm,AttendanceForm,EditAttendanceForm
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.utils import timezone
from.models import AttendanceModel,Shift, RosterSchedule,AttendanceLog,LeaveBalanceHistory,LatePolicy
from datetime import date



@login_required
def attendance_input(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()         
            return redirect('leavemanagement:view_attendance')
        else:
            print(form.errors)  
    else:
        form = AttendanceForm()    
    return render(request, 'leavemanagement/attendance_form.html', {'form': form})


@login_required
def view_attendance(request):
    attendance_records = AttendanceModel.objects.all()
    return render(request, 'leavemanagement/view_attendance.html', {'attendance_records': attendance_records})


@login_required
def update_attendance(request, employee_id):
    employee = get_object_or_404(AttendanceModel, id=employee_id) 
    print(employee)  
    if request.method == 'POST':
        form =  EditAttendanceForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('leavemanagement:view_attendance')  
    else:
        form =  EditAttendanceForm(instance=employee)
    return render(request, 'leavemanagement/attendance_form.html', {'form': form,'employee':employee})



@login_required
def leave_dashboard(request):
    menu_items = [
        {'title': 'Create leave type', 'url': reverse('leavemanagement:create_leave_type')},
        {'title': 'Apply for leave', 'url': reverse('leavemanagement:apply_leave')},
        {'title': 'Leave application status', 'url': reverse('leavemanagement:leave_history')},     
        {'title': 'Leave summary', 'url': reverse('leavemanagement:leave_summary')},
        {'title': 'Pending leave application', 'url': reverse('leavemanagement:pending_leave_list')},     
       
    ]
    return render(request, 'leavemanagement/leave_dashboard.html', {'menu_items': menu_items})


@login_required
def manage_leave_type(request, id=None):  
    instance = get_object_or_404(LeaveType, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = LeaveTypeForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('leavemanagement:create_leave_type')  

    datas = LeaveType.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'leavemanagement/manage_leave_type.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_leave_type(request, id):
    instance = get_object_or_404(LeaveType, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('leavemanagement:create_leave_type')   

    messages.warning(request, "Invalid delete request!")
    return redirect('leavemanagement:create_leave_type')  
  

from.models import LatePolicy
from.forms import  AttendancePolicyForm

@login_required
def manage_attendance_policy(request, id=None):   
    instance = get_object_or_404(LatePolicy, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AttendancePolicyForm(request.POST or None, instance=instance)

    if request.method == 'POST':
        form = AttendancePolicyForm(request.POST, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.user = request.user
            form_instance.save()        
            messages.success(request, message_text)
            return redirect('leavemanagement:create_attendance_policy')  
        else:
            print(form.errors)  # Debugging line to check form errors


    datas = LatePolicy.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)



    return render(request, 'leavemanagement/manage_attendance_policy.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_attendance_policye(request, id):
    instance = get_object_or_404(LatePolicy, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('leavemanagement:create_attendance_policy')    

    messages.warning(request, "Invalid delete request!")
    return redirect('leavemanagement:create_attendance_policy')  




def get_accrued_balance(employee, leave_type):
    balance_record, created = EmployeeLeaveBalance.objects.get_or_create(
        employee=employee,
        leave_type=leave_type,
        defaults={'balance': 0, 'carry_forward': 0}
    )

    if leave_type.accrues_monthly:
        current_month = date.today().month
        joining_month = employee.joining_date.month if employee.joining_date else 1

        eligible_months = max(0, current_month - joining_month + 1)
        max_accruable_days = leave_type.accrual_rate * eligible_months

        return min(balance_record.balance, max_accruable_days)

    return balance_record.balance




@login_required
def carry_forward_leave(request):
    current_date = timezone.now()
    current_year = current_date.year
    next_year = current_year + 1

    if current_date.month != 1: 
        messages.warning(request, 'Carry forward process is only allowed in January.')
        return redirect('leavemanagement:leave_dashboard')

    balances = EmployeeLeaveBalance.objects.filter(
        year=current_year,
        leave_type__allow_carry_forward=True
    )

    for balance in balances:
        max_limit = balance.leave_type.max_carry_forward_limit or 0
        carry_over_days = min(balance.balance, max_limit)

        next_year_balance, created = EmployeeLeaveBalance.objects.get_or_create(
            employee=balance.employee,
            leave_type=balance.leave_type,
            year=next_year,
            defaults={
                'balance': balance.leave_type.annual_allowance + carry_over_days,
                'carry_forward': carry_over_days,
            }
        )

        if not created:    
            next_year_balance.carry_forward = carry_over_days
            next_year_balance.balance += carry_over_days
            next_year_balance.save()

    messages.success(request, 'Eligible leave balances have been successfully carried forward!')
    return redirect('leavemanagement:create_leave_type')



from core.models import Employee

@login_required
def monthly_leave_accrual_update(request):
    today = date.today()
    current_month = today.month
    current_year = today.year

    employees = Employee.objects.all()

    for employee in employees:
        leave_balances = EmployeeLeaveBalance.objects.filter(employee=employee)

        for balance_instance in leave_balances:
            leave_type = balance_instance.leave_type
            if not leave_type.accrues_monthly:
                continue

            if balance_instance.last_accrued_month == current_month:
                continue  
 
            approved_leaves = LeaveApplication.objects.filter(
                employee=employee,
                leave_type=leave_type,
                status='APPROVED',
                approved_start_date__year=current_year,
                approved_start_date__month=current_month,
            ).aggregate(total_days=Sum('approved_no_of_days'))['total_days'] or 0
 
            accrued_days = leave_type.accrual_rate
            balance_instance.balance += accrued_days
            balance_instance.balance -= approved_leaves
            if balance_instance.balance < 0:
                balance_instance.balance = 0
 
            balance_instance.last_accrued_month = current_month
            balance_instance.save()
    return HttpResponse("Monthly leave accrual updated successfully for all employees.")



@login_required
def apply_leave(request):
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            start_date = form.cleaned_data['applied_start_date']
            end_date = form.cleaned_data['applied_end_date']
            leave_application = form.save(commit=False)
            employee = Employee.objects.filter(user_profile=request.user.user_profile).first()                    
            if not employee:
                messages.error(request, 'Employee record not found!')
                return redirect('leavemanagement:leave_history')
            leave_application.employee = employee
            balance_record, created = EmployeeLeaveBalance.objects.get_or_create(
                employee=leave_application.employee,
                leave_type=leave_application.leave_type,
                defaults={'balance': 0}
            )
            leave_days = (end_date - start_date).days + 1
            allowed_balance = get_accrued_balance(leave_application.employee, leave_application.leave_type)
            if allowed_balance < leave_days:
                messages.error(request, f'Insufficient balance! Allowable: {allowed_balance} days. Requested: {leave_days} days.')
                return redirect('leavemanagement:leave_history')
            leave_application.save()
            messages.success(request, 'Leave application submitted successfully!')
            return redirect('leavemanagement:leave_history')
    else:
        form = LeaveApplicationForm()

    return render(request, 'leavemanagement/apply_leave.html', {'form': form})



@login_required
def leave_history(request):
    leave_applications=[]
    leave_summary=[]
    employee=None
    try:
        user_profile = request.user.user_profile
        employee = Employee.objects.get(user_profile=user_profile)
        leave_applications = LeaveApplication.objects.filter(employee=employee).select_related('leave_type')
        leave_balances = EmployeeLeaveBalance.objects.filter(employee=employee).select_related('leave_type')

        approved_dict = {}
        for application in leave_applications:
            if application.leave_type.id in approved_dict:
                approved_dict[application.leave_type.id] += application.approved_no_of_days                
            else:
                approved_dict[application.leave_type.id] = application.approved_no_of_days               

        leave_summary = []
        for balance in leave_balances:
            leave_type = balance.leave_type
            total_leave = balance.balance
            approved_leave = approved_dict.get(leave_type.id, 0)  
            carry_forward = balance.carry_forward or 0
            available_leave = total_leave -  approved_leave if approved_leave else total_leave

            leave_summary.append({
                'leave_type': leave_type.name,
                'total_leave': total_leave,
                'approved_leave': approved_leave,
                'available_leave': available_leave,
                'employee': employee,
                'carry_forward': carry_forward
            })

    except Employee.DoesNotExist:
        messages.error(request, "No employee record found for your profile.")
       

    return render(request, 'leavemanagement/leave_history.html', {
        'leave_applications': leave_applications,  # Pass applications directly
        'leave_summary': leave_summary,
        'employee': employee,
    })




@login_required
def leave_summary(request):
    try:
        current_year = timezone.now().year
        user_profile = request.user.user_profile
        employee = Employee.objects.get(user_profile=user_profile)
        leave_balances = EmployeeLeaveBalance.objects.filter(employee=employee)     
        availed_leaves = LeaveApplication.objects.filter(
            employee=employee,
            status='APPROVED'  
        ).values('leave_type').annotate(total_availed=Sum('approved_no_of_days'))  

        availed_dict = {item['leave_type']: item['total_availed'] for item in availed_leaves}
      
        leave_summary = []
        for balance in leave_balances:
            leave_type = balance.leave_type
            total_leave = balance.balance  
            availed_leave = availed_dict.get(leave_type.id, 0)  
            available_leave = total_leave - availed_leave 
            carry_forward = balance.carry_forward

            leave_summary.append({
                'leave_type': leave_type.name,
                'total_leave': total_leave,
                'availed_leave': availed_leave,
                'available_leave': available_leave,
                'employee':employee,
                'carry_forward':carry_forward 
            })

    except Employee.DoesNotExist:
        messages.error(request, "No employee record found for your profile.")
        return redirect('leavemanagement:leave_dashboard')

    return render(request, 'leavemanagement/leave_summary.html', {
        'leave_summary': leave_summary,
        'employee':employee,
        'current_year': current_year
    })



@login_required
def approve_leave(request, leave_id):
    leave_application = get_object_or_404(LeaveApplication, id=leave_id)
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized action!')
        return redirect('leavemanagement:pending_leave_list')
    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['approved_start_date']
            end_date = form.cleaned_data['approved_end_date']

            leave_days = (end_date - start_date).days + 1

            if leave_application.status != 'APPROVED':
                balance_record = EmployeeLeaveBalance.objects.get(
                    employee=leave_application.employee,
                    leave_type=leave_application.leave_type,
                )

                allowed_balance = get_accrued_balance(leave_application.employee, leave_application.leave_type)
                if allowed_balance >= leave_days:
                    balance_record.balance -= leave_days
                    balance_record.save()

                    leave_application.status = 'APPROVED'
                    leave_application.approved_start_date = start_date
                    leave_application.approved_end_date = end_date
                    leave_application.approved_on = timezone.now()
                    leave_application.save()

                    messages.success(request, f'Leave approved for {leave_days} days.')
                else:
                    messages.error(
                        request,
                        f'Insufficient balance! Allowable: {allowed_balance} days. Requested: {leave_days} days.'
                    )
            else:
                messages.info(request, 'Leave is already approved.')
            return redirect('leavemanagement:pending_leave_list')

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        initial_days = (leave_application.applied_end_date - leave_application.applied_start_date).days + 1

        form = ApprovalForm(initial={
            'approved_start_date': leave_application.applied_start_date,
            'approved_end_date': leave_application.applied_end_date,
            'leave_type':leave_application.leave_type
        })

    return render(request, 'leavemanagement/approve_leave.html', {'form': form, 'leave_application': leave_application})




@login_required
def pending_leave_list(request):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access!")
        return redirect('leavemanagement:leave_dashboard')

    pending_applications = LeaveApplication.objects.filter(status='PENDING')
  
    pending_with_balance = []
    for leave_application in pending_applications:
        allowed_balance = get_accrued_balance(leave_application.employee, leave_application.leave_type)

        pending_with_balance.append({
            'application': leave_application,
            'allowed_balance': allowed_balance
        })

    return render(request, 'leavemanagement/pending_leave_list.html', {
        'pending_with_balance': pending_with_balance
    })


################################## late in adjustment #################

from datetime import timedelta, date
from django.db.models import Q
from .models import AttendanceModel, LatePolicy,Holiday



def daily_attendance_update_task(employee, attendance_date):
    policy = LatePolicy.objects.first()
    max_check_in_time = policy.max_check_in_time

    logs = AttendanceLog.objects.filter(employee=employee, date=attendance_date).order_by("ceated_at")
    if not logs.exists():
        return f"No attendance records found for {employee.name} on {attendance_date}"
    
    first_check_in = logs.first().check_in_time
    last_check_out = logs.last().check_out_time if logs.last().check_out_time else None
    
    if not employee.is_roster_employee:
        if not employee.office_start_time or not employee.office_end_time:
            return f"{employee.name} has no fixed schedule."        

        office_start_time = employee.office_start_time
        office_end_time = employee.office_end_time
    else:       
        schedule = RosterSchedule.objects.filter(employee=employee, date=attendance_date).first()
        if not schedule:
            return f"No shift found for {employee.name} on {attendance_date}"
        
        shift_start_time = schedule.shift.start_time
        shift_end_time = schedule.shift.end_time

    is_late = first_check_in > max_check_in_time
    left_early = last_check_out and last_check_out < office_end_time

    total_worked_time = timedelta()
    for log in logs:
        if log.check_out_time:
            total_worked_time += datetime.combine(attendance_date, log.check_out_time) - datetime.combine(attendance_date, log.check_in_time)

    attendance, created = AttendanceModel.objects.update_or_create(
        employee=employee,
        date=attendance_date,
        defaults={
            "first_check_in": first_check_in,
            "last_check_out": last_check_out,
            "total_hours_worked": total_worked_time,
            "is_late": is_late if not has_flexible_hours(employee) else False,  # Ignore lateness for flexible employees
            "left_early": left_early if not has_flexible_hours(employee) else False  # Ignore early leaving for flexible employees
        }
    )

    return f"Attendance processed for {employee.name} on {attendance_date}"



def daily_attendance_processing():
    employees = Employee.objects.all()
    for employee in employees:
        daily_attendance_update_task(employee)
     


def is_non_working_day(current_date):
    if current_date.weekday() in [5, 6]:  # Friday = 5, Saturday = 6
        return True   
    if Holiday.objects.filter(holiday_date=current_date).exists():
        return True    
    return False


def has_flexible_hours(employee):
    return employee.late_policy.flexible_hours


def calculate_work_hours(records):
    total_work_hours = 0
    for record in records:      
        work_duration = record.last_check_out - record.first_check_in
        total_work_hours += work_duration.total_seconds() / 3600  
    return total_work_hours



def has_compensated_hours_all_day(employee, records):
    if has_flexible_hours(employee):  # Only flexible employees
        total_work_hours = calculate_work_hours(records)
        required_work_hours = (employee.office_end_time - employee.office_start_time).total_seconds() / 3600
        return total_work_hours >= required_work_hours * len(records) 
    return True  # Fixed-hour employees don’t need total work hours check


def has_compensated_hours_exclude_holiday(employee, records):
    if has_flexible_hours(employee):  
        records = records.exclude(date__in=Holiday.objects.values_list('holiday_date', flat=True))
        total_work_hours = calculate_work_hours(records)
        required_work_hours = (employee.office_end_time - employee.office_start_time).total_seconds() / 3600
        return total_work_hours >= required_work_hours * len(records)
    return True  # Fixed-hour employees don’t need total work hours check

from datetime import date, timedelta
from django.db.models import Q

def combined_check_lates_or_earlyouts(employee, is_late=True):
    today = date.today()
    policy = LatePolicy.objects.first()  

    # Set thresholds for leave and salary deductions
    monthly_leave_deduct_threshold = (
        policy.max_monthly_late_in_before_leave_deduction if is_late 
        else policy.max_monthly_early_out_before_leave_deduction
    )
    monthly_salary_deduct_threshold = (
        policy.max_monthly_lates_in_before_salary_deduction if is_late 
        else policy.max_monthly_early_out_before_salary_deduction
    )

    max_consecutive_deduction = (
        policy.max_consecutive_late_in_before_leave_deduction if is_late 
        else policy.max_consecutive_early_out_before_leave_deduction
    )
    max_consecutive_salary_deduction = (
        policy.max_consecutive_lates_in_before_salary_deduction if is_late 
        else policy.max_consecutive_early_out_before_salary_deduction
    )

    result = {
        "salary_violation": False, 
        "leave_violation": False
    }

    # Check if employee is exempt from policy
    if (policy.flexible_hours and has_flexible_hours(employee)) or (
        policy.senior_staff_exempt and employee.is_senior_employee
    ):
        return result

    # Monthly Total Late Policy
    if policy.late_policy_type == "monthly_total_late":
        month_start = today.replace(day=1)
        records = AttendanceModel.objects.filter(
            employee=employee,
            date__range=[month_start, today],
        ).filter(
            Q(is_late=True) | Q(early_out=True)  # Corrected filtering logic
        ).exclude(date__in=Holiday.objects.values_list('holiday_date', flat=True))

        count = records.count()

        # Only apply deductions if count exceeds the thresholds
        if count > monthly_leave_deduct_threshold:
            result["leave_violation"] = True
            if has_flexible_hours(employee) and has_compensated_hours_exclude_holiday(employee, records):
                result["leave_violation"] = False

        if count > monthly_salary_deduct_threshold:
            result["salary_violation"] = True
            if has_flexible_hours(employee) and has_compensated_hours_exclude_holiday(employee, records):
                result["salary_violation"] = False

    # Consecutive Late Policy
    elif policy.late_policy_type == "consecutive_late":
        recent_attendance = AttendanceModel.objects.filter(
            employee=employee,
            date__lte=today,
        ).filter(
            Q(is_late=True) | Q(early_out=True)
        ).exclude(date__in=Holiday.objects.values_list('holiday_date', flat=True)).order_by('-date')[:max_consecutive_salary_deduction]

        count = recent_attendance.count()
        dates = [att.date for att in recent_attendance]

        # Function to check if dates are consecutive working days
        def are_consecutive_working_days(dates):
            return all(
                (dates[i - 1] - dates[i]).days == 1 
                for i in range(1, len(dates))
                if dates[i] not in Holiday.objects.values_list('holiday_date', flat=True)
            )

        # Leave deduction check
        if count >= max_consecutive_deduction and are_consecutive_working_days(dates[:max_consecutive_deduction]):
            result["leave_violation"] = True
            if has_flexible_hours(employee) and has_compensated_hours_exclude_holiday(employee, recent_attendance):
                result["leave_violation"] = False

        # Salary deduction check
        if count >= max_consecutive_salary_deduction and are_consecutive_working_days(dates):
            result["salary_violation"] = True
            if has_flexible_hours(employee) and has_compensated_hours_exclude_holiday(employee, recent_attendance):
                result["salary_violation"] = False

    return result




from.models import SalaryDeductionRecord

def deduct_salary(employee, is_late=True):  
    policy = LatePolicy.objects.first()   
    basic_salary = employee.basic_salary  
   
    deduction_amount = 0
    reason = ""

    if is_late:  
        deduction_percentage = policy.salary_deduction_percentage_for_late_policy_violation
        deduction_amount = (deduction_percentage / 100) * basic_salary  # Calculate percentage deduction
        reason = f"Salary deduction for excessive lateness: {deduction_percentage}% of daily salary"
    else:  # If it's early-out, apply similar logic
        deduction_percentage = policy.salary_deduction_percentage_for_late_policy_violation
        deduction_amount = (deduction_percentage / 100) * basic_salary
        reason = f"Salary deduction for excessive early out: {deduction_percentage}% of daily salary"
  
    if deduction_amount > 0:
        SalaryDeductionRecord.objects.create(
            employee=employee,
            amount=deduction_amount,
            reason=reason
        )

    return deduction_amount 


def deduct_leave(employee):  
    policy = LatePolicy.objects.first()
    leave_deduction = policy.leave_day_deduction_for_late_policy_violation

    try:
        earned_leave_balance = EmployeeLeaveBalance.objects.get(
            employee=employee, leave_type__name='Earned Leave'
        )
        if earned_leave_balance.balance >= leave_deduction:
            earned_leave_balance.balance -= leave_deduction
            earned_leave_balance.save()
            LeaveBalanceHistory.objects.create(
                employee=employee,
                leave_type=earned_leave_balance.leave_type,
                change=-leave_deduction,
                reason=f'Deduction due to lateness/early-out policy'
            )
            return True
    except EmployeeLeaveBalance.DoesNotExist:
        pass
    return False



@login_required
def check_and_deduct_late_leaves(request):
    employees = Employee.objects.all()
    deductions = []
    for employee in employees:        
        result_late = combined_check_lates_or_earlyouts(employee, is_late=True)
        result_early_out = combined_check_lates_or_earlyouts(employee, is_late=False)

        salary_deducted = False
        leave_deducted = False

        # Combine the results from both late and early-out checks
        result = {
            "salary_violation": result_late.get("salary_violation", False) or result_early_out.get("salary_violation", False),
            "leave_violation": result_late.get("leave_violation", False) or result_early_out.get("leave_violation", False)
        }

        if result["salary_violation"]:
            salary_deducted = deduct_salary(employee, is_late=True)
            if salary_deducted:
                deductions.append(f"Deducted {salary_deducted} from salary for {employee.name} due to excessive lateness/early-out.")
        
        if result["leave_violation"]:
            leave_deducted = deduct_leave(employee)
            if leave_deducted:
                deductions.append(f"Deducted {employee.late_policy.leave_day_deduction_for_late_policy_violation} leave days for {employee.name} due to lateness/early-out policy violation.")

    if deductions:
        messages.success(request, f"Deductions made: {', '.join(deductions)}")
        return JsonResponse({'status': 'success', 'deductions': deductions})
    else:
        messages.info(request, "No deductions were made today.")

    return redirect('leavemanagement:leave_dashboard')



