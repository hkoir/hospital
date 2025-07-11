from django.shortcuts import render,get_object_or_404,redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required,permission_required,user_passes_test

from.models import AllExpenses,Asset
from django.contrib import messages
from.forms import AssetForm,ExpenseForm
from core.models import Shareholder,Employee
from datetime import date
from decimal import Decimal
from billing.models import DoctorPayment
from django.shortcuts import render
from django.db.models import Sum
from billing.models import BillingInvoice
import json





@login_required
def manage_asset(request, id=None):  
    instance = get_object_or_404(Asset, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form =AssetForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('finance:create_asset') 

    datas = Asset.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'expense/manage_asset.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_asset(request, id):
    instance = get_object_or_404(Asset, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('finance:create_asset')

    messages.warning(request, "Invalid delete request!")
    return redirect('finance:create_asset')





@login_required
def manage_expense(request, id=None):  
    instance = get_object_or_404(AllExpenses, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form =ExpenseForm(request.POST or None, request.FILES or None, instance=instance)

    assets = Asset.objects.all()
    for asset in assets:
        asset.apply_asset_depreciation()    
        print('...................................depreciation applied')

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('finance:create_expense') 

    datas = AllExpenses.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'expense/manage_expense.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_expense(request, id):
    instance = get_object_or_404(AllExpenses, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('finance:create_expense')

    messages.warning(request, "Invalid delete request!")
    return redirect('fiance:create_expense')






def revenue_report(request): 
    data = (
        BillingInvoice.objects.values('invoice_type')
        .annotate(total_amount=Sum('total_amount'))
    )

    # Prepare data for chart
    labels = []
    amounts = []
    total_revenue = 0
    labels_amounts = []
    for item in data:
        label = item['invoice_type']
        amount = float(item['total_amount'] or 0)
        total_revenue += amount
        labels.append(label)
        amounts.append(amount)
        labels_amounts.append((label, amount))

    context = {
        'labels': json.dumps(labels),   
        'amounts': json.dumps(amounts), 
       'labels_amounts': labels_amounts,
       'total_revenue':total_revenue 
    }
    return render(request, 'finance/revenue_report.html', context)




def top_expenses_head(request):
    expense_data = AllExpenses.objects.values('expense_head').annotate(total_amount=Sum('amount')).order_by('-total_amount')[:10]
    total_amount =0

    expense_heads = [data['expense_head'] for data in expense_data]
    amounts = [float(data['total_amount']) for data in expense_data]

    total_amount = sum(amounts) 


    combined = zip(expense_heads, amounts) 
    
    return render(request, 'finance/top_expense_head.html', {
        'expense_heads': json.dumps(expense_heads),   
        'amounts': json.dumps(amounts), 
        'combined_data': combined,
        'total_amount':total_amount
    })



def shareholder_dashboard(request):
    estimated_salary_paid = None
    total_income = BillingInvoice.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    total_doctor_payment = DoctorPayment.objects.aggregate(total=Sum('total_paid_amount'))['total'] or Decimal('0.00')
    other_expenses = AllExpenses.objects.aggregate(total=Sum('amount'))['total'] or Decimal(0.00)
   
    Asset_value = Asset.objects.aggregate(total=Sum('current_value'))['total'] or Decimal(0.00)

    today = date.today()
    months_passed = today.month 
    employees = Employee.objects.all()
    for emp in employees:   
        print(f'employee name{emp.name} salary/month{emp.salary_structure.net_salary()}')    
        estimated_salary_paid = emp.salary_structure.net_salary() * months_passed or Decimal(0.00)

    
       

    net_profit = total_income - (total_doctor_payment + other_expenses + estimated_salary_paid)

    shareholders = Shareholder.objects.all()
    for shareholder in shareholders:
        shareholder.profit_share = round((shareholder.percentage_share / 100) * net_profit, 2)

    context = {
        'total_income': total_income,
        'asset_current_value': Asset_value,
        'total_doctor_payment': total_doctor_payment,   
        'total_other_expenses': other_expenses,       
        'estimated_salary_paid': estimated_salary_paid ,    
        'net_profit': net_profit,
        'shareholders': shareholders
    }

    return render(request, 'finance/shareholder_dashboard.html', context)










