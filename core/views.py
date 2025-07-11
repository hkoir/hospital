
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import uuid
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from openpyxl import Workbook
from io import BytesIO
from django.http import HttpResponse

from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4,letter
from reportlab.pdfgen import canvas
from django.utils import timezone
import os
from django.conf import settings
from datetime import datetime,timedelta

from.forms import MonthYearForm,AddCompanyForm,ManageLocationForm,UpdateLocationForm,NoticeForm
from .models import EmployeeRecordChange,MonthlySalaryReport,Notice,Location,Company

from .forms import CommonFilterForm
from core.models import Employee
from core.forms import AddEmployeeForm
from django.db.models.signals import pre_save
from django.dispatch import receiver

from.forms import ManageDepartmentForm,ManagePositionForm
from.models import Department,Position
from clients.models import SubscriptionPlan

from.models import CompanyPolicy,SalaryStructure
from.forms import CompanyPolicyForm,SalaryStructureForm
from .forms import ManageLocationForm

from django.template.loader import render_to_string
from django.core.mail import EmailMessage,send_mail

import base64







@login_required
def dashboard(request):
    plans = SubscriptionPlan.objects.all().order_by('duration')
    for plan in plans:
        plan.features_list = plan.features.split(',')

    modules = [
  
    {"name": "Core HR Management", "icon": "fas fa-cogs", "description": "Streamline core business processes.", "link": "core:only_core_dashboard"},
   
    {"name": "Leave management", "icon": "fas fa-users", "description": "Automate entire leave management system and established association with others.., .", "link": "leavemanagement:leave_dashboard"},
  
   
]

    return render(request,'core/dashboard.html',{'plans':plans,'modules':modules})

@login_required
def home(request):
    return render(request,'core/home.html')

@login_required
def core_dashboard(request):
    return render(request,'core/core_dashboard.html')

@login_required
def only_core_dashboard(request):
    return render(request,'core/only_core_dashboard.html')


@login_required
def all_qc(request):
    return render(request,'core/all_qc.html')



@login_required
def manage_department(request):
    departments = Department.objects.all().order_by('-created_at')  
    form = ManageDepartmentForm(request.POST or None)

    if request.method == 'POST':
        if 'entity_submit' in request.POST:  
            if form.is_valid():
                department = form.save(commit=False)
                department.user = request.user  
                department.save()
                messages.success(request, "Department added successfully.")
                return redirect('core:manage_department')  
            else:
                messages.error(request, "Form is invalid. Please check the details and try again.")

        elif 'action' in request.POST:
            print(request.POST)  
            action = request.POST.get('action')
            entity_id = int(request.POST.get('entity_id', 0))

            if not entity_id: 
                messages.error(request, "Invalid entry ID provided.")
                return redirect('core:manage_department')

            if action == 'update':
                entity_obj = get_object_or_404(Department, id=entity_id)
                form = ManageDepartmentForm(request.POST, instance=entity_obj)
                if form.is_valid():
                    updated_entity = form.save(commit=False)
                    updated_entity.user = request.user
                    updated_entity.save()
                    messages.success(request, "Department updated successfully.")
                    return redirect('core:manage_department')
                else:
                    messages.error(request, "Form is invalid. Please check the details.")
            elif action == 'delete':
                entity_obj = get_object_or_404(Department, id=entity_id)
                entity_obj.delete()
                messages.success(request, "Department deleted successfully.")
                return redirect('core:manage_department')


    paginator = Paginator(departments, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,'core/manage_department.html',{'form': form, 'page_obj': page_obj})





@login_required
def manage_position(request, id=None):  
    instance = get_object_or_404(Position, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ManagePositionForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()   
        form.save_m2m()     
        messages.success(request, message_text)
        return redirect('core:create_position')  
    else:
        print(form.errors)

    datas = Position.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ManagePositionForm(instance=instance)
    return render(request, 'core/manage_position.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_position(request, id):
    instance = get_object_or_404(Position, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_position')  

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_position') 


def position_details(request,id):
    position_instance = get_object_or_404(Position,id=id)
    return render(request,'core/position_details.html',{'position_instance':position_instance})



from.models import JobDescription,JobRequirement
from.forms import JobDescriptionForm,JobRequirementForm



@login_required
def manage_job_description(request, id=None):  
    datas=[]
    position=None
    department = None
    
    instance = get_object_or_404(JobDescription, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = JobDescriptionForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        position = form.cleaned_data['position']
        department = form.cleaned_data['department']
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('core:create_job_description')  
    
    if instance:
        datas = JobDescription.objects.filter(position=instance.position,department=instance.department).order_by('-created_at')
    elif position and department:
         datas = JobDescription.objects.filter(position=position,department=department).order_by('-created_at')
    else:
        datas = JobDescription.objects.all().order_by('-created_at')

    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = JobDescriptionForm(instance=instance)
    return render(request, 'core/manage_job_description.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_job_descriptiont(request, id):
    instance = get_object_or_404(JobDescription, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_job_description')    

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_job_description')  



@login_required
def manage_job_requirement(request, id=None):  
    instance = get_object_or_404(JobRequirement, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = JobRequirementForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('core:create_job_requirement')  

    datas = JobRequirement.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    form = JobRequirementForm( instance=instance)
    return render(request, 'core/manage_job_requirement.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_job_requirement(request, id):
    instance = get_object_or_404(JobRequirement, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_job_requirement')    

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_job_requirement')  





@login_required
def create_company(request, id=None):  
    instance = get_object_or_404(Company, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddCompanyForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('core:create_company')  

    datas = Company.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/create_company.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_company(request, id):
    instance = get_object_or_404(Company, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_company')   

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_company')   





@login_required
def manage_location(request, id=None):  
    instance = get_object_or_404(Location, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ManageLocationForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('core:create_location')  

    datas = Location.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/manage_location.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_location(request, id):
    instance = get_object_or_404(Location, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_location')   

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_location')   



@login_required
def manage_company_policy(request, id=None):  
    instance = get_object_or_404(CompanyPolicy, id=id) if id else None
    message_text = "updated successfully!" if instance else "added successfully!"    
    form = CompanyPolicyForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST':
        form = CompanyPolicyForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form_instance = form.save(commit=False)        
            form_instance.user = request.user
            form_instance.save()    
            messages.success(request, message_text)
            return redirect('core:create_company_policy')  # Redirect ensures form is cleared

    # If a new entry is being created (no id), clear the form
    if not id and request.method != "POST":
        form = CompanyPolicyForm()  

    datas = CompanyPolicy.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/manage_company_policy.html', {
        'form': form,  
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_company_policy(request, id):
    instance = get_object_or_404(CompanyPolicy, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_company_policy')  

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_company_policy')  



@login_required
def manage_salary_structure(request, id=None):
    instance = get_object_or_404(SalaryStructure, id=id) if id else None
    message_text = "updated successfully!" if instance else "added successfully!"

    form = SalaryStructureForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_instance = form.save(commit=False)
        form_instance.user = request.user  
            
        form_instance.save()
        messages.success(request, message_text)     
        return redirect('core:create_salary_structure')
  
    datas = SalaryStructure.objects.all().order_by('-created_at')    
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

 
    return render(request, 'core/manage_salary_structure.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_salary_structure(request, id):
    instance = get_object_or_404(SalaryStructure, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_salary_structure') 

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_salary_structure')


from.models import Festival,PerformanceBonus
from.forms import FestivalForm,PeformanceBonusForm

@login_required
def manage_festival(request, id=None):
    instance = get_object_or_404(Festival, id=id) if id else None
    message_text = "updated successfully!" if instance else "added successfully!"

    form = FestivalForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_instance = form.save(commit=False)
        form_instance.user = request.user  
            
        form_instance.save()
        messages.success(request, message_text)     
        return redirect('core:create_festival')
  
    datas = Festival.objects.all().order_by('-created_at')    
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

 
    return render(request, 'core/manage_festival.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_festival(request, id):
    instance = get_object_or_404(Festival, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_festival') 

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_festival')



@login_required
def manage_performance_bonus(request, id=None):
    instance = get_object_or_404(PerformanceBonus, id=id) if id else None
    message_text = "updated successfully!" if instance else "added successfully!"

    form = PeformanceBonusForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_instance = form.save(commit=False)
        form_instance.user = request.user  
            
        form_instance.save()
        messages.success(request, message_text)     
        return redirect('core:create_performance_bonus')
  
    datas = PerformanceBonus.objects.all().order_by('-created_at')    
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

 
    return render(request, 'core/manage_performance_bonus.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_performance_bonus(request, id):
    instance = get_object_or_404(PerformanceBonus, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:create_performance_bonus') 

    messages.warning(request, "Invalid delete request!")
    return redirect('core:create_performance_bonus') 








@login_required
def manage_employee(request, id=None):  
    instance = get_object_or_404(Employee, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddEmployeeForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('core:manage_employee')

    datas = Employee.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/manage_employee.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_employee(request, id):
    instance = get_object_or_404(Employee, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:manage_employee')

    messages.warning(request, "Invalid delete request!")
    return redirect('core:manage_employee')

from.models import Doctor,Nurse
from.forms import AddDoctorForm,AddNurseForm

from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from .models import Employee, UserProfile
from .forms import AddEmployeeForm
from django.conf import settings

from clients.models import Client
from django.db import connection







User = get_user_model()  

@login_required
def manage_doctor(request, id=None):  
    current_tenant = None
    current_schema = None

    if hasattr(connection, 'tenant') and connection.tenant:
        current_tenant = connection.tenant
        current_schema = connection.tenant.schema_name   

    instance = get_object_or_404(Doctor, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddDoctorForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_instance = form.save(commit=False)

        if not id:    
            random_password = get_random_string(length=6)    

            user = User.objects.create_user(
                username=form_instance.name, 
                email=form_instance.email,
                password=random_password,
                tenant=current_tenant,
                photo_id = form_instance.employee_photo_ID
            )
            user.is_active = True
            user.is_staff = True
            user.save()

           

            send_mail(
                subject="Your New Account Details",
                message=f"Hello {form_instance.name},\n\nYour account has been created.\n\nUsername: {form_instance.name}\nPassword: {random_password}\n\nPlease login and change your password.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[form_instance.email],
                fail_silently=False
            )

        form_instance.save()        
        messages.success(request, message_text)
        return redirect('core:manage_doctor')

    # Pagination - Fetch doctors instead of employees
    datas = Doctor.objects.all().order_by('-id')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/doctor_nurse/manage_doctor.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_doctor(request, id):
    instance = get_object_or_404(Doctor, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:manage_doctor')

    messages.warning(request, "Invalid delete request!")
    return redirect('core:manage_doctor')





@login_required
def manage_nurse(request, id=None):  
    instance = get_object_or_404(Nurse, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddNurseForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('core:manage_nurse')

    datas = Nurse.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'core/doctor_nurse/manage_nurse.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_nurse(request, id):
    instance = get_object_or_404(Nurse, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('core:manage_nurse')

    messages.warning(request, "Invalid delete request!")
    return redirect('core:manage_nurse')









@login_required
def view_employee(request):
    employee_name = None
    employee_records = Employee.objects.all().order_by('-created_at')

    form=CommonFilterForm(request.GET or None)

    if form.is_valid():
        employee_name = form.cleaned_data['employee_name']
        if employee_name:
            employee_records=employee_records.filter(name=employee_name)

    paginator = Paginator(employee_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    form=CommonFilterForm()
    return render(request, 'core/view_employee.html', 
    {
        'employee_records': employee_records,
        'form':form,
        'page_obj':page_obj
    })



@login_required
def employee_list(request):
    employees = Employee.objects.all().order_by('-created_at') 
    days=None
    start_date=None
    end_date =None
    name = None

   
    form= CommonFilterForm(request.GET or None)

    if form.is_valid():
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        days = form.cleaned_data.get('days')
        name = form.cleaned_data.get('employee_name')

        if name:
            employees = employees.filter(id=name.id)
        
        if start_date and end_date:
             employees =  employees.filter(created_at__range=(start_date, end_date))
        elif days:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            employees=  employees.filter(created_at__range=(start_date, end_date))

    paginator = Paginator(employees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = CommonFilterForm()


    return render(request,'core/employee_list.html', 
        {
        'employees': employees,
        'page_obj':page_obj,
        'form':form,
         'days':days,
         'start_date':start_date,
         'end_date':end_date,
         'name':name,    

        })





@login_required
@receiver(pre_save, sender=Employee)
def log_employee_changes(sender, instance, **kwargs):
    if instance.pk:
        old_instance = Employee.objects.get(pk=instance.pk)
        for field in instance._meta.fields:
            old_value = getattr(old_instance, field.attname)
            new_value = getattr(instance, field.attname)
            if old_value != new_value:
                EmployeeRecordChange.objects.create(
                    employee=instance,
                    field_name=field.attname,
                    old_value=str(old_value),
                    new_value=str(new_value)
                )




@login_required
def view_employee_changes(request): 
    changes = EmployeeRecordChange.objects.all()
    history =  changes.all()
    return render(request, 'core/employee_change_record.html', {'changes': changes,'history':history})


@login_required
def view_employee_changes_single(request, employee_id): 
    employee = get_object_or_404(Employee, pk=employee_id)
    changes_single = EmployeeRecordChange.objects.filter(employee=employee)
    history =  changes_single.all()
    return render(request, 'core/employee_change_record.html', {'changes_single': changes_single,'history':history})




@login_required
def download_employee_changes(request): 
    employee_changes = EmployeeRecordChange.objects.all()
    workbook = Workbook()
    worksheet = workbook.active
    headers = ['Employee ID', 'Field Name', 'Old Value', 'New Value']
    worksheet.append(headers)
    for change in employee_changes:
        row = [change.employee_id, change.field_name, change.old_value, change.new_value]
        worksheet.append(row)
    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)
    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=employee_changes.xlsx'
    return response



salary_month=None
salary_year = None 

@login_required
def create_salary(request):
    global salary_month,salary_year
    salary_month = request.GET.get('month')  
    salary_year = request.GET.get('year')  
    salary = None

    if salary_month and salary_year: 
        month = int(salary_month)
        year = int(salary_year)

        employees = Employee.objects.all()

        for employee in employees:
            total_salary = (
                employee.salary_structure.basic_salary +
                employee.salary_structure.hra +
                employee.salary_structure.medical_allowance +
                employee.salary_structure.conveyance_allowance +
                employee.salary_structure.festival_allowance +
                 employee.salary_structure.performance_bonus
            )

            MonthlySalaryReport.objects.update_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={'total_salary': total_salary}
            )

        salary = MonthlySalaryReport.objects.filter(month=month, year=year)

    form = MonthYearForm()

    context = {'form': form, 'salary': salary, 'month': salary_month, 'year': salary_year}
    return render(request, 'core/create_monthly_salary.html', context)



def generate_salary_sheet(month, year):   
    salary_reports = MonthlySalaryReport.objects.filter(month=month, year=year)
    
    salary_sheet = []
    for report in salary_reports: 
        if isinstance(report.employee, Employee):
            total_salary = report.total_salary
            salary_sheet.append({
                'employee': report.employee,
                'total_salary': total_salary
            })
        else:
            print(f"Invalid employee reference in report: {report}")
    
    return salary_sheet




@login_required
def download_salary(request):
    global salary_month,salary_year   

    if not salary_month or not salary_year:
        messages.error(request, "Month and Year must be provided to download the salary report.")
        return redirect('core:create_salary')

    try:
        month = int(salary_month)
        year = int(salary_year)
    except ValueError:
        messages.error(request, "Invalid Month or Year format.")
        return redirect('core:create_salary') 

    salary_sheet = generate_salary_sheet(month, year)

    if not salary_sheet:
        messages.error(request, "No salary data found for the selected month and year.")
        return redirect('core:create_salary')

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Salary Report'

    headers = ['Employee ID', 'Name', 'Total Salary']
    worksheet.append(headers)

    for entry in salary_sheet:
        employee = entry['employee']
        row = [
            employee.employee_code,
            employee.name,
            entry['total_salary']
        ]
        worksheet.append(row)

    excel_file = BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)

    response = HttpResponse(
        excel_file.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=salary_report.xlsx'
    return response





def generate_pay_slip_pdf(employee): 
    buffer = BytesIO()
    envelope_size = (3.625 * 72, 5.5 * 72)  
    pdf_canvas = canvas.Canvas(buffer, pagesize=envelope_size)  
     
    if employee.gender == 'Male':
            prefix = 'Mr.'
            prefix2 = 'his'
    elif employee.gender == 'Female':
            prefix = 'Mrs.'
            prefix2 = 'her'
    else:
            prefix = '' 
            prefix2 =''   
        
    pdf_canvas.setFont("Helvetica", 10)
    pdf_canvas.setFillColor('blue')
    pdf_canvas.drawString(50, 370, f" Mymeplus Technology Limited")

    pdf_canvas.setFont("Helvetica", 10)
    pdf_canvas.setFillColor('green')
    pdf_canvas.drawString(100, 350, f"Pay Slip")


    pdf_canvas.setFont("Helvetica-Bold", 10)
    pdf_canvas.setFillColor('black')
    pdf_canvas.drawString(50, 330, f"Date: {timezone.now().date()}")
    pdf_canvas.setFont("Helvetica", 10)
    pdf_canvas.drawString(50, 300, f"Employee Code: {employee.employee_code}")
    pdf_canvas.drawString(50, 280, f"Name: {employee.name}")
    pdf_canvas.drawString(50, 260, f"Position: {employee.position}")
    pdf_canvas.drawString(50, 240, f"Department: {employee.department}")
    pdf_canvas.drawString(50, 220, f"Employee Level: {employee.employee_level}")   
    pdf_canvas.drawString(50, 200, f"Basic Salary: {employee.salary_structure.basic_salary}")
    pdf_canvas.drawString(50, 180, f"House Allowance: {employee.salary_structure.hra}")
    pdf_canvas.drawString(50, 160, f"Medical Allowance: {employee.salary_structure.medical_allowance}")
    pdf_canvas.drawString(50, 140, f"Transportation Allowance: {employee.salary_structure.conveyance_allowance}")
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(50, 110, f"Pay Slip for {prefix} {employee.first_name} {employee.last_name}")  
    pdf_canvas.setFont("Helvetica", 10)
    cfo_employee = Employee.objects.filter(position__name='CFO').first()
    if cfo_employee:
        pdf_canvas.drawString(50, 70, f"Autorized Signature________________")  
        pdf_canvas.drawString(80, 50, f"Name:{cfo_employee.name}")  
        pdf_canvas.drawString(80, 30, f"Designation:{cfo_employee.position}")  
    else:
        pdf_canvas.drawString(50, 70, f"Autorized Signature________________")  
        pdf_canvas.drawString(80, 50, f"Name:........") 
        pdf_canvas.drawString(80, 30, f"Designation:.....") 
    pdf_canvas.setFont("Helvetica-Bold", 7)
    pdf_canvas.setFillColor('green')
    pdf_canvas.drawString(30, 15, f"Signature is not required due to computerized authorization")  
    pdf_canvas.setFillColor('yellow') 
    pdf_canvas.rect(5, 5, 250,385)
    pdf_canvas.showPage()
    pdf_canvas.save()   

    buffer.seek(0)
    return buffer




@login_required
def  preview_pay_slip(request, employee_id):  
    employee = get_object_or_404(Employee, id=employee_id)
    pdf_buffer = generate_pay_slip_pdf(employee)    
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    return render(request, "core/preview_pay_slip.html", {
        "employee": employee,
        "pdf_preview": pdf_base64,
    })



def send_pay_slip(employee):      
    if not employee.email:
        return f"Employee email not found for {employee.name}."
    pdf_buffer = generate_pay_slip_pdf(employee)   
    message = f'Dear {employee.name} , your requested salary certificate is attached herewith'
    try:
        email = EmailMessage(
            subject="Offer Letter from Our Company",
            body=message,
            from_email="yourcompany@example.com",
            to=[employee.email]
        )
        email.attach(f"Pay slip_{employee.id}.pdf", pdf_buffer.getvalue(), 'application/pdf')
        email.content_subtype = "html"
        email.send()        
      
        return f"Offer letter sent to {employee.name} successfully!"
    except Exception as e:
        return f"Error sending offer letter to {employee.name}: {str(e)}"




@login_required
def generate_and_send_pay_slip(request, employee_id): 
    employee = get_object_or_404(Employee,id=employee_id)
    message = send_pay_slip(employee)
    if "Error" in message:
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect('core:employee_list')




def generate_salary_certificate_pdf(employee):
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)

    # Prefix logic
    if employee.gender == 'Male':
        prefix, prefix2 = 'Mr.', 'his'
    elif employee.gender == 'Female':
        prefix, prefix2 = 'Mrs.', 'her'
    else:
        prefix, prefix2 = '', ''

    # Company details and header
    logo_path = 'D:/SCM/dscm/media/logo.png'
    pdf_canvas.drawImage(logo_path, 50, 750, width=60, height=60)

    y_space = 700
    spacing1 = 15
    pdf_canvas.setFont("Helvetica", 12)
    pdf_canvas.drawString(50, y_space, "mymeplus Technology Limited")
    y_space -= spacing1
    pdf_canvas.drawString(50, y_space, "House#39, Road#15, Block#F, Bashundhara R/A, Dhaka-1229")
    y_space -= spacing1
    pdf_canvas.drawString(50, y_space, "Phone:01842800705")
    y_space -= spacing1
    pdf_canvas.drawString(50, y_space, "Email: hkobir@mymeplus.com")
    y_space -= spacing1
    pdf_canvas.drawString(50, y_space, "Website: www.mymeplus.com")

    # Date and heading
    current_date = datetime.now().strftime("%Y-%m-%d")
    pdf_canvas.drawString(50, 600, f"Date: {current_date}")
    pdf_canvas.drawString(50, 560, f"Salary Certificate for {prefix} {employee.first_name} {employee.last_name}")
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(200, 500, "To Whom It May Concern")

    # Salary details
    pdf_canvas.setFont("Helvetica", 10)
    y_space = 450
    pdf_canvas.drawString(50, y_space, f"This is to certify that {prefix} {employee.name} is working in the {employee.department} department since {employee.joining_date}, {prefix2} monthly remuneration is as follows:")
    y_space -= spacing1
    pdf_canvas.drawString(150, y_space, f"Basic Salary: {employee.salary_structure.basic_salary}")
    y_space -= spacing1
    pdf_canvas.drawString(150, y_space, f"House Allowance: {employee.salary_structure.hra}")
    y_space -= spacing1
    pdf_canvas.drawString(150, y_space, f"Medical Allowance: {employee.salary_structure.medical_allowance}")
    y_space -= spacing1
    pdf_canvas.drawString(150, y_space, f"Transportation Allowance: {employee.salary_structure.conveyance_allowance}")
    y_space -= spacing1
    pdf_canvas.drawString(150, y_space, f"Festival Bonus: {employee.salary_structure.festival_allowance}")
    y_space -= spacing1 + 20
    pdf_canvas.drawString(50, y_space, f"The total monthly remuneration of {employee.name} amounts to {employee.salary_structure.gross_salary()}")
    y_space -= spacing1
    pdf_canvas.drawString(50, y_space, f"This certificate is issued upon request of {employee.name} for {prefix2} intended purpose. Please do not hesitate to contact us if further clarification is required.")

    # Authorized Signature
    pdf_canvas.drawString(50, 250, "Sincerely,")
    cfo_employee = Employee.objects.filter(position__name='CFO').first()
    if cfo_employee:
        pdf_canvas.drawString(50, 150, "Authorized Signature________________")
        pdf_canvas.drawString(50, 135, f"Name: {cfo_employee.name}")
        pdf_canvas.drawString(50, 120, f"Designation: {cfo_employee.position}")
    else:
        pdf_canvas.drawString(50, 150, "Authorized Signature________________")
        pdf_canvas.drawString(50, 135, "Name: ........")
        pdf_canvas.drawString(50, 120, "Designation: .....")

    pdf_canvas.setFont("Helvetica-Bold", 10)
    pdf_canvas.setFillColor('green')
    pdf_canvas.drawString(50, 80, "Signature is not mandatory due to computerized authorization")

    pdf_canvas.showPage()
    pdf_canvas.save()

    buffer.seek(0)
    return buffer



@login_required
def preview_salary_certificate(request, employee_id):  
    employee = get_object_or_404(Employee, id=employee_id)
    pdf_buffer = generate_salary_certificate_pdf(employee)    
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    return render(request, "core/preview_salary_certificate.html", {
        "employee": employee,
        "pdf_preview": pdf_base64,
    })




def send_salary_certificate(employee):      
    if not employee.email:
        return f"Employee email not found for {employee.name}."
    pdf_buffer = generate_salary_certificate_pdf(employee)   
    message = f'Dear {employee.name} , your requested salary certificate is attached herewith'
    try:
        email = EmailMessage(
            subject="Offer Letter from Our Company",
            body=message,
            from_email="yourcompany@example.com",
            to=[employee.email]
        )
        email.attach(f"salary_certificate_{employee.id}.pdf", pdf_buffer.getvalue(), 'application/pdf')
        email.content_subtype = "html"
        email.send()        
      
        return f"Offer letter sent to {employee.name} successfully!"
    except Exception as e:
        return f"Error sending offer letter to {employee.name}: {str(e)}"




@login_required
def generate_and_send_salary_certificate(request, employee_id): 
    employee = get_object_or_404(Employee,id=employee_id)
    message = send_salary_certificate(employee)
    if "Error" in message:
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect('core:employee_list')





def generate_experience_certificate_pdf(employee):   
    buffer = BytesIO() 
    a4_size = A4           
    pdf_canvas = canvas.Canvas(buffer,pagesize=a4_size)

    if employee.gender == 'Male':
            prefix = 'Mr.'
            prefix2 = 'his'
            prefix3 ='him'
    elif employee.gender == 'Female':
            prefix = 'Mrs.'
            prefix2 = 'her'
            prefix3 = 'her'
    else:
            prefix = '' 
            prefix2 =''
            prefix3 =''

    logo_path = 'D:/SCM/dscm/media/logo.png'  
        
    logo_width = 60 
    logo_height = 60  
    pdf_canvas.drawImage(logo_path, 50, 750, width=logo_width, height=logo_height) 

    spacing1 = 15
    y_space = 730
    pdf_canvas.setFont("Helvetica", 12) 
    y_space -= spacing1
    pdf_canvas.drawString(50,  y_space, "mymeplus Technology Limited")
    y_space -= spacing1
    pdf_canvas.drawString(50,  y_space, "House#39, Road#15, Block#F, Bashundhara R/A, Dhaka-1229")
    y_space -= spacing1
    pdf_canvas.drawString(50,  y_space, "Phone:01842800705")
    y_space -= spacing1
    pdf_canvas.drawString(50,  y_space, "email: hkobir@mymeplus.com")
    y_space -= spacing1
    pdf_canvas.drawString(50,  y_space, "website: www.mymeplus.com")
    pdf_canvas.setFont("Helvetica", 12)
    current_date = datetime.now().strftime("%Y-%m-%d")
    pdf_canvas.drawString(50, 570,f"Date: {current_date}")   
    pdf_canvas.drawString(50, 535,  f"Experience Certificate for {prefix} {employee.first_name} {employee.last_name}")
    pdf_canvas.drawString(50, 500, f"This is to certify that {prefix} {employee.first_name}  {employee.last_name} was employed at from {employee.joining_date} to {employee.resignation_date}.")
    pdf_canvas.drawString(50, 485, f"During {prefix2} tenure, {employee.name} held the position of {employee.position} as {prefix2} last designation and performed {prefix2}")
    pdf_canvas.drawString(50, 470, f"duties with dedication and professionalism. We wish {prefix3} all the best for {prefix2} future endeavors.")     
    cfo_employee = Employee.objects.filter(position__name='CFO').first()
    if cfo_employee:
        pdf_canvas.drawString(50, 350, f"Autorized Signature________________")  
        pdf_canvas.drawString(50, 335, f"Name:{cfo_employee.name}")  
        pdf_canvas.drawString(50, 320, f"Designation:{cfo_employee.position}")  
    else:
        pdf_canvas.drawString(50, 350, f"Autorized Signature________________")  
        pdf_canvas.drawString(50, 335, f"Name:........") 
        pdf_canvas.drawString(50, 320, f"Designation:.....")  
    pdf_canvas.setFont("Helvetica-Bold", 10)
    pdf_canvas.setFillColor('green')
    pdf_canvas.drawString(50,280, f"Signature is not mandatory due to computerized authorization")  
    pdf_canvas.showPage()
    pdf_canvas.save()    
    
    buffer.seek(0)
    return buffer




@login_required
def preview_experience_certificate(request, employee_id):  
    employee = get_object_or_404(Employee, id=employee_id)
    pdf_buffer = generate_experience_certificate_pdf(employee)    
    pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
    return render(request, "core/preview_experience_certificate.html", {
        "employee": employee,
        "pdf_preview": pdf_base64,
    })



def send_experience_certificate(employee):      
    if not employee.email:
        return f"Employee email not found for {employee.name}."
    pdf_buffer = generate_experience_certificate_pdf(employee)   
    message = f'Dear {employee.name} , your requested experience certificate is attached herewith'
    try:
        email = EmailMessage(
            subject=f"Experience certificate for {employee.name}",
            body=message,
            from_email="yourcompany@example.com",
            to=[employee.email]
        )
        email.attach(f"experience_certificate_{employee.id}.pdf", pdf_buffer.getvalue(), 'application/pdf')
        email.content_subtype = "html"
        email.send()        
      
        return f"Experience certificate sent to {employee.name} successfully!"
    except Exception as e:
        return f"Error sending Experience certificate  to {employee.name}: {str(e)}"




@login_required
def generate_and_send_experience_certificate(request, employee_id): 
    employee = get_object_or_404(Employee,id=employee_id)
    message = send_experience_certificate(employee)
    if "Error" in message:
        messages.error(request, message)
    else:
        messages.success(request, message)

    return redirect('core:employee_list')





@login_required
def add_notice(request):
    if request.method == 'POST':
        form = NoticeForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('core:view_notices')
    else:
        form = NoticeForm()
    return render(request, 'core/add_notice.html', {'form': form})


@login_required
def view_notices(request):
    notices = Notice.objects.all().order_by('-created_at')
    form = NoticeForm()
    return render(request, 'core/view_notices.html', {'notices': notices, 'form': form})



