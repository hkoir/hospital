from django.shortcuts import render,redirect,get_object_or_404
from.models import SupplierPerformance
from django.core.paginator import PageNotAnInteger,Paginator,EmptyPage,Page
from django.contrib import messages
from.forms import SupplierPerformanceForm,AddLocationForm,AddSupplierForm
from.models import Supplier,SupplierPerformance,Location
from django.contrib.auth.decorators import login_required,permission_required


@login_required
def supplier_dashboard(request):
    return render(request,'supplier/supplier_dashboard.html')



@login_required
def create_supplier(request, id=None):  
    instance = get_object_or_404(Supplier, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddSupplierForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('supplier:create_supplier')  

    datas = Supplier.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'supplier/create_supplier.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_supplier(request, id):
    instance = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('supplier:create_supplier')  

    messages.warning(request, "Invalid delete request!")
    return redirect('supplier:create_supplier') 



@login_required
def create_location(request, id=None):  
    instance = get_object_or_404(Location, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddLocationForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('supplier:create_location')  

    datas = Location.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'supplier/create_location.html', {
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
        return redirect('supplier:create_location')   

    messages.warning(request, "Invalid delete request!")
    return redirect('supplier:create_location')   



@login_required
def supplier_performance_list(request):
    performances = SupplierPerformance.objects.all().order_by('-created_at')
    paginator = Paginator(performances, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'supplier/supplier_performance_list.html', {'page_obj': page_obj})


@login_required
def add_or_update_performance(request, performance_id=None):
    if performance_id:
        performance = get_object_or_404(SupplierPerformance, id=performance_id)
        message_text = "Performance updated successfully!"
    else:
        performance = None
        message_text = "Performance added successfully!"
        
    form = SupplierPerformanceForm(request.POST or None, instance=performance)

    if request.method == 'POST':
        if form.is_valid():
            form_instance = form.save(commit=False)
            form_instance.user = request.user
            form_instance.save()           
            messages.success(request, message_text)
            return redirect('supplier:supplier_performance_list')

    return render(request, 'supplier/create_or_update_performance.html', {'form': form, 'performance': performance})


