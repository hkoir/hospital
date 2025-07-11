from django.utils import timezone
from django.db.models import Sum
from datetime import date
from core.models import Employee
from .models import AttendanceLog, AttendanceModel, RosterSchedule
from .models import EmployeeLeaveBalance, LeaveApplication,EmployeeLeaveBalance
from datetime import datetime, timedelta
from .views import has_flexible_hours
from celery import shared_task

from django.core.mail import send_mail
from .views import combined_check_lates_or_earlyouts, deduct_salary, deduct_leave
from.models import LatePolicy
from django.core.exceptions import ObjectDoesNotExist


@shared_task
def carry_forward_leave_task():
    current_date = timezone.now()

    if current_date.month != 1:
        return "Skipping: Carry forward process can only run in January."

    current_year = current_date.year
    next_year = current_year + 1

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

    return "Leave balances successfully carried forward!"



@shared_task
def monthly_leave_accrual_update_task():
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

            # Skip if accrual has already been done for the current month
            if balance_instance.last_accrued_month == current_month:
                continue  

            approved_leaves = LeaveApplication.objects.filter(
                employee=employee,
                leave_type=leave_type,
                status='APPROVED',
                approved_start_date__year=current_year,
                approved_start_date__month=current_month,
            ).aggregate(total_days=Sum('approved_no_of_days'))['total_days'] or 0

            # Accrue the leave days and subtract approved leave days
            accrued_days = leave_type.accrual_rate
            balance_instance.balance += accrued_days
            balance_instance.balance -= approved_leaves
            if balance_instance.balance < 0:
                balance_instance.balance = 0

            balance_instance.last_accrued_month = current_month
            balance_instance.save()

    return "Monthly leave accrual updated successfully for all employees."




@shared_task
def daily_attendance_update_task(attendance_date=None):
    policy = LatePolicy.objects.first()
    if not policy:
        return "LatePolicy not found."

    max_check_in_time = policy.max_check_in_time

    try:
        if attendance_date is None:
            attendance_date = date.today()

        employees = Employee.objects.filter(is_roster_employee=False)

        for employee in employees:
            logs = AttendanceLog.objects.filter(employee=employee, date=attendance_date).order_by("check_in_time")

            if not logs.exists():
                continue

            first_check_in = logs.first().check_in_time
            last_check_out = logs.last().check_out_time if logs.last().check_out_time else None

            is_late = first_check_in > max_check_in_time
            left_early = last_check_out and last_check_out < employee.office_end_time

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
                    "is_late": is_late,
                    "left_early": left_early
                }
            )

        return f"Attendance processed for all employees on {attendance_date}"

    except ObjectDoesNotExist:
        return "Error: One or more employees not found or invalid data."

    except Exception as e:
        return f"An error occurred: {str(e)}"


@shared_task
def check_and_deduct_late_leaves_task():
    employees = Employee.objects.all()
    deductions = []
    
    for employee in employees:
        # Fetch violations for both lateness and early outs
        result_late = combined_check_lates_or_earlyouts(employee, is_late=True)
        result_early_out = combined_check_lates_or_earlyouts(employee, is_late=False)

        salary_violation = result_late.get("salary_violation", False) or result_early_out.get("salary_violation", False)
        leave_violation = result_late.get("leave_violation", False) or result_early_out.get("leave_violation", False)

        if salary_violation:
            salary_deducted = deduct_salary(employee, is_late=True)
            if salary_deducted:
                deductions.append(f"Deducted {salary_deducted} from salary for {employee.name} due to excessive lateness/early-out.")

        if leave_violation:
            leave_deducted = deduct_leave(employee)
            if leave_deducted:
                deductions.append(f"Deducted {leave_deducted} leave days for {employee.name} due to lateness/early-out policy violation.")

    if deductions:
        send_mail(
            "Late Leave Deductions Summary",
            f"Deductions made: {', '.join(deductions)}",
            "from@example.com",  # Change to your email address
            ["admin@example.com"],  # Recipients (e.g., admin email)
            fail_silently=False,
        )        

        return f"Deductions processed: {', '.join(deductions)}"
    
    return "No deductions were made today."
