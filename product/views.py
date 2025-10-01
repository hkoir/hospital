from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from.forms import AddCategoryForm,AddProductForm

from.models import Category,Product
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import ProgrammingError
from django.contrib.auth.decorators import login_required,permission_required

from purchase.models import Batch


@login_required
def product_dashboard(request):
    return render(request,'product/product_dashboard.html')

@login_required
def print_unit_labels(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    units = batch.units.all().order_by('serial_number')

    # Handle user input for quantity
    quantity_to_print = units.count()  # default all units
    if request.method == "POST":
        qty = request.POST.get("quantity")
        try:
            qty = int(qty)
            if qty > 0:
                quantity_to_print = min(qty, units.count())
        except (ValueError, TypeError):
            pass  # keep default if invalid input

    units = units[:quantity_to_print]

    return render(request, "product/unit_labels.html", {
        "units": units,
        "batch": batch,
        "max_quantity": batch.quantity
    })


@login_required
def manage_category(request, id=None):  
    instance = get_object_or_404(Category, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddCategoryForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('product:create_category')

    datas = Category.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'product/manage_category.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_category(request, id):
    instance = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('product:create_category')

    messages.warning(request, "Invalid delete request!")
    return redirect('product:create_category')


@login_required
def manage_product(request, id=None):  
    instance = get_object_or_404(Product, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddProductForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('product:create_product') 

    datas = Product.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'product/manage_product.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_product(request, id):
    instance = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('product:create_product')

    messages.warning(request, "Invalid delete request!")
    return redirect('product:create_product')


@login_required
def product_data(request,product_id):
    product_instance = get_object_or_404(Product,id=product_id)
    return render(request,'product/product_data.html',{'product_instance':product_instance})
