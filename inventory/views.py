
from django.shortcuts import render, redirect,get_object_or_404
from django.db.models import F
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib import messages
import json
from django.db.models import Sum
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Inventory
# from inventory.models import Batch,Product,ProductCategory
from product.models import Product,Category
from purchase.models import Batch

from.forms import BatchForm,AddProductForm,AddCategoryForm,CommonFilterForm
from.forms import ProductSearchForm,InventoryTransactionForm


from django.utils import timezone
from django.db import transaction
from django.forms import modelformset_factory
from .forms import MedicineSaleOnlyForm, MedicineSaleItemForm
from.models import MedicineSaleItem,MedicineSaleOnly,Product
from medical_records.models import MedicalRecord
from billing.models import BillingInvoice,Payment
from billing.models import MedicineBill




from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView,TemplateView
from .models import Warehouse, Location
from .forms import WarehouseForm, LocationForm, ProductTypeForm

from product.models import ProductType

# -------------------
# Warehouse Views
# -------------------
from django.core.paginator import Paginator

class WarehouseCreateView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/warehouse_form_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = WarehouseForm()

        # Paginate warehouses
        warehouses = Warehouse.objects.all().order_by("-created_at")
        paginator = Paginator(warehouses, 10)
        page_number = self.request.GET.get("page")
        context['page_obj'] = paginator.get_page(page_number)
        return context

    def post(self, request, *args, **kwargs):
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save(commit=False)
            if not warehouse.user:
                warehouse.user = request.user
            warehouse.save()
            return redirect(request.path)
        return self.get(request, *args, **kwargs)



class WarehouseUpdateView(LoginRequiredMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = "inventory/warehouse_form_card.html"
    success_url = reverse_lazy("inventory:inventory_dashboard")

# -------------------
# Location Views
# -------------------

class WarehouseLocationCreateView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/wh_location_form_card.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LocationForm()

        # Paginate warehouses
        locations = Location.objects.all().order_by("-created_at")
        paginator = Paginator(locations, 10)
        page_number = self.request.GET.get("page")
        context['page_obj'] = paginator.get_page(page_number)
        return context

    def post(self, request, *args, **kwargs):
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            if not location.user:
                location.user = request.user
            location.save()
            return redirect(request.path)
        return self.get(request, *args, **kwargs)


class WarehouseLocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = "inventory/wh_location_form_card.html"
    success_url = reverse_lazy("inventory:inventory_dashboard")

# -------------------
# ProductType Views
# -------------------
class ProductTypeCreateView(LoginRequiredMixin, TemplateView):
    template_name = "inventory/product_type_form_card.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProductTypeForm()

        # Paginate warehouses
        p_types = ProductType.objects.all().order_by("-id")
        paginator = Paginator(p_types, 10)
        page_number = self.request.GET.get("page")
        context['page_obj'] = paginator.get_page(page_number)
        return context

    def post(self, request, *args, **kwargs):
        form = ProductTypeForm(request.POST)
        if form.is_valid():
            p_type_form= form.save(commit=False)
            if not p_type_form.user:
                p_type_form.user = request.user
            p_type_form.save()
            return redirect(request.path)
        return self.get(request, *args, **kwargs)


class ProductTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductType
    form_class = ProductTypeForm
    template_name = "inventory/product_type_form_card.html"
    success_url = reverse_lazy("inventory:inventory_dashboard")


@login_required
def product_dashboard(request):
    return render(request,'inventory/product_dashboard.html')



@login_required
def product_list(request):
    product = None
    products = Product.objects.all().order_by('-created_at')
    form = CommonFilterForm(request.GET or None)  
    if form.is_valid():
        product = form.cleaned_data.get('product_name')
        if product:
            products = products.filter(name__icontains=product.name)  
    
    paginator = Paginator(products, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form=CommonFilterForm()

    return render(request, 'inventory/product_list.html', {
        'products': products,
        'page_obj': page_obj,
        'product': product,
        'form': form,
    })



@login_required
def manage_category(request, id=None):  
    instance = get_object_or_404(ProductCategory, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = AddCategoryForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        form_intance.user = request.user
        form_intance.save()        
        messages.success(request, message_text)
        return redirect('inventory:create_category')

    datas = Category.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_category.html', {
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
        return redirect('inventory:create_category')

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_category')




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
        return redirect('inventory:create_product') 

    datas = Product.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_product.html', {
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
        return redirect('inventory:create_product')

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_product')


@login_required
def product_data(request,product_id):
    product_instance = get_object_or_404(Product,id=product_id)
    return render(request,'inventory/product_data.html',{'product_instance':product_instance})




@login_required
def manage_batch(request, id=None):  
    instance = get_object_or_404(Batch, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = BatchForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        product = form.cleaned_data['product']
        manufacture_date = form.cleaned_data['manufacture_date']
        expiry_date = form.cleaned_data['expiry_date']
        quantity = form.cleaned_data['quantity']
        unit_price = form.cleaned_data['purchase_price']
        product_type= form.cleaned_data['product_type']  

        existing_batch = Batch.objects.filter(product=product, manufacture_date=manufacture_date).first()
        if existing_batch:              
            existing_batch.quantity += quantity
            existing_batch.remaining_quantity = F('remaining_quantity') + quantity
            #existing_batch.unit_price = unit_price  # Decide if price should be updated
        else:
            batch = form.save(commit=False)
            batch.user = request.user          
            batch.remaining_quantity = quantity
            batch.save()          
           
        messages.success(request, message_text)
        return redirect('inventory:create_batch')  

    datas = Batch.objects.all().order_by('-updated_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_batch.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



@login_required
def delete_batch(request, id):
    instance = get_object_or_404(Batch, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('inventory:create_batch')      

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_batch') 






from inventory.services.inventory import process_transaction

def create_inventory_transaction(request):
    if request.method == "POST":
        form = InventoryTransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()

            # Call the service to apply business rules
            try:
                process_transaction(
                    transaction,
                    user=request.user,
                    target_warehouse=form.cleaned_data.get('target_warehouse'),
                    target_location=form.cleaned_data.get('target_location')
                )
                messages.success(request, "Transaction processed successfully.")
            except Exception as e:
                messages.error(request, f"Transaction failed: {str(e)}")
                # Optional: rollback transaction if needed

            return redirect("inventory:inventory_dashboard")
    else:
        form = InventoryTransactionForm(user=request.user)
    return render(request, "inventory/inventory_transaction.html", {"form": form})




@login_required
def inventory_dashboard(request):
    table_data = Inventory.objects.select_related('product', 'warehouse', 'location', 'batch')
    product=None
    warehouse=None
    location=None
    batch=None

    form = ProductSearchForm(request.GET or None)
    if request.method == 'GET':
        form = ProductSearchForm(request.GET or None)
        if form.is_valid():
            product=form.cleaned_data['product']
            batch=form.cleaned_data['batch']
            warehouse=form.cleaned_data['warehouse']
            location=form.cleaned_data['location']

            if product:
                table_data = table_data.filter(product__name__icontains=product)

            if batch:
                table_data = table_data.filter(batch__batch_number__icontains=batch)
            if warehouse:
                table_data = table_data.filter(warehouse__name__icontains=warehouse)
            if location:
                table_data = table_data.filter(location__name__icontains=location)

        else:
            print(form.errors)
          
    
    form = ProductSearchForm()
    datas = table_data 
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('inventory/partials/inventory_table.html', {'page_obj': page_obj})
        return JsonResponse({'html': html})


    inventory_data = table_data.values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        reorder_level=Sum('reorder_level')
    ).order_by('total_quantity')[:10]


    labels = [item['product__name'] for item in inventory_data]
    quantities = [item['total_quantity'] for item in inventory_data]
    reorder_levels = [item['reorder_level'] for item in inventory_data]

  

    context = {
        'labels': json.dumps(labels),
        'quantities': json.dumps(quantities),
        'reorder_levels': json.dumps(reorder_levels),
        'page_obj': page_obj,
        'form':form,
        'product':product,
        'warehouse':warehouse,
        'location':location,
        'batch':batch,
    }
  
    
    return render(request, 'inventory/inventory_dashboard.html', context)





@login_required
def get_medicines(request, category_id):
    medicines = Product.objects.filter(category_id=category_id).values('id', 'name')
    print('trigerring ajax')
    return JsonResponse(list(medicines), safe=False)


@login_required
def get_batches(request, product_id):
    batches = Batch.objects.filter(product_id=product_id)
    data = [
        {
            "id": b.id,
            "product_name": b.product.name, 
            "remaining_quantity": b.remaining_quantity,
            "batch_number": b.batch_number
        }
        for b in batches
    ]
    return JsonResponse(data, safe=False)






from billing.models import ReferralCommissionTransaction
from billing.utils import create_referral_transaction_for_service
from django.core.files.base import ContentFile
import base64,uuid



@login_required
def create_medicine_sale_only(request):
    MedicineSaleItemFormSet = modelformset_factory(
        MedicineSaleItem, form=MedicineSaleItemForm, extra=1, can_delete=True
    )

    if request.method == 'POST':
        sale_form = MedicineSaleOnlyForm(request.POST, request.FILES)
        formset = MedicineSaleItemFormSet(request.POST)

        if sale_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                sale = sale_form.save(commit=False)
                patient = sale.patient

                image_data = request.POST.get("prescription_image_base64")
                if image_data:
                    fmt, imgstr = image_data.split(";base64,")
                    ext = fmt.split("/")[-1]
                    filename = f"prescription_{uuid.uuid4()}.{ext}"
                    sale.prescription_file.save(
                        filename, ContentFile(base64.b64decode(imgstr)), save=False
                    )
                medical_record = MedicalRecord.objects.create(
                    patient=patient,
                    doctor=getattr(sale, "doctor", None),
                    external_doctor=getattr(sale, "doctor_ref", None),
                    diagnosis="Medicine Sale Only",
                    treatment_plan="Medicine Sale Only",
                    date=timezone.now(),
                )

                total_amount = 0
                instances = formset.save(commit=False)

                for instance, form in zip(instances, formset.forms):
                    if form.cleaned_data.get("DELETE"):
                        continue

                    qty = instance.quantity
                    batch = instance.batch
                    total_amount += batch.sale_price * qty

                invoice = BillingInvoice.objects.create(
                    patient=patient,
                    total_amount=total_amount,
                    total_paid=total_amount,
                    invoice_type="Medicine-Sale-Only",
                )

                sale.medical_record = medical_record
                sale.invoice = invoice
                sale.total_amount = total_amount
                sale.save()

                for instance, form in zip(instances, formset.forms):
                    if form.cleaned_data.get("DELETE"):
                        continue

                    instance.medicine_sale_only = sale
                    instance.save()

                    batch = instance.batch
                    batch.remaining_quantity -= instance.quantity
                    batch.save(update_fields=["remaining_quantity"])

                    MedicineBill.objects.create(
                        invoice=invoice,
                        medicine=instance.medicine,
                        quantity=instance.quantity,
                        price_per_unit=batch.sale_price,
                        service_type=instance.medicine.product_category.service_type,
                        status="Paid",
                        patient_type="OPD",
                    )
           
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount_paid=invoice.total_amount,
                    payment_type="Medicine-Sale-Only",
                    payment_method="Cash", 
                    remarks="Payment for Medicine Sale Only",
                    patient_type="OPD",
                )
                referral_source = sale.referral_source or (
                    patient.referral_source if patient else None
                )
                from billing.utils import create_referral_transaction_for_service
                from accounting.utils import create_journal_entry,create_referral_commission_expense_journal
                if referral_source:                   
                    txn=create_referral_transaction_for_service(
                        invoice=invoice,
                        referral_source=referral_source,
                        service_type="medicine",
                        service_id=invoice.id,
                        service_amount=invoice.total_amount,
                    )
                    if txn:
                        create_referral_commission_expense_journal(
                        invoice=invoice, 
                        commission_amount=txn.commission_amount, 
                        created_by=None)
                        print("Referral Creation Result:", txn)
                else:
                    print("No referral source available")      

                create_journal_entry(
                    payment,
                    breakdown=[{'amount': total_amount, 'revenue_type': 'Medicine'}],
                    description=f"Medicine sale to  {patient.name}",
                    created_by=request.user
                )

                invoice.update_totals()
                return redirect("appointments:appointment_list")
        else:
            print("Form Errors:", sale_form.errors)
            print("Formset Errors:", formset.errors)

    else:
        sale_form = MedicineSaleOnlyForm()
        formset = MedicineSaleItemFormSet(queryset=MedicineSaleItem.objects.none())

    medicine_prices = {
        str(batch.id): float(batch.sale_price or 0)
        for batch in Batch.objects.all()
    }

    return render(request, "inventory/create_medicine_sale_only.html", {
        "lab_visit_form": sale_form,
        "formset": formset,
        "medicine_prices": json.dumps(medicine_prices),
    })




import qrcode
from io import BytesIO
import base64
from django.urls import reverse

@login_required
def medicine_sale_invoice_print(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    medicine_bills = MedicineBill.objects.filter(invoice=invoice)
    medical_record = getattr(invoice, " medical_record", None)
    patient = invoice.patient

    total_medicine_amount = medicine_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    total_medicine_paid = medicine_bills.aggregate(total=Sum('total_paid'))['total'] or 0
    qr_data = request.build_absolute_uri(
        reverse('inventory:medicine_sale_invoice_print', args=[invoice.id])
    )
    
    qr_img = qrcode.make(qr_data)
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        "invoice": invoice,
        "patient": patient,
        "medical_record": medical_record,
        "medicine_bills": medicine_bills,
        "print_date": timezone.now(),
        "qr_code": qr_code_base64,
	'total_medicine_amount':total_medicine_amount,
        'total_medicine_paid': total_medicine_paid 

    }
    
    return render(request, "inventory/print_medicine_sale_invoice.html", context)




@login_required
def pending_medicine_deliveries(request):
    invoice_id = request.GET.get('invoice')
    search_query = request.GET.get('search', '')

    if invoice_id:       
        invoices = BillingInvoice.objects.filter(id=invoice_id)
    else:        
        invoices = BillingInvoice.objects.filter(
            medicine_bills__status='Paid'
        ).exclude(
            medicine_bills__status='Delivered'
        ).distinct()

    if search_query:
        invoices = invoices.filter(
            Q(medical_record__patient__name__icontains=search_query) |
            Q(medical_record__patient__patient_id__icontains=search_query) |
            Q(medical_record__patient__phone__icontains=search_query) |
            Q(lab_test_bills__lab_test_request_order__requested_lab_test_code__icontains=search_query)
        ).distinct()

    if not invoice_id:
        paginator = Paginator(invoices, 5)
        page_number = request.GET.get('page')   
        invoices_page = paginator.get_page(page_number)
    else:
        invoices_page = invoices  

    invoice_data = []
    for invoice in invoices_page:
        medicine_bills = invoice.medicine_bills.exclude(status='Delivered')
        medicine_total = sum([bill.total_price() for bill in medicine_bills])
        invoice_data.append((invoice, medicine_total))

    return render(request, 'inventory/pending_medicine_deliveries.html', {
        'invoices': invoices_page,
        'invoice_data': invoice_data,
        'search_query': search_query
    })





from inventory.models import Inventory,InventoryTransaction

@login_required
@transaction.atomic
def deliver_invoice_medicines(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    medicine_bills = invoice.medicine_bills.filter(status='Paid')

    for bill in medicine_bills:
        product = bill.medicine
        qty_needed = bill.quantity

        # 1. Get FIFO batch
        batch = Batch.objects.filter(
            product=product,
            quantity__gte=qty_needed
        ).order_by('expiry_date').first()

        if not batch:
            messages.error(request, f"Insufficient batch stock for {product.name}.")
            return redirect('billing:invoice_detail', pk=invoice_id)

        batch.quantity -= qty_needed
        batch.save()

        inventory = Inventory.objects.filter(product=product).first()
        if not inventory:
            messages.error(request, f"No inventory record found for {product.name}.")
            return redirect('billing:invoice_detail', pk=invoice_id)

        if inventory.quantity < qty_needed:
            messages.error(request, f"Inventory mismatch! Stock is lower than batch stock for {product.name}.")
            raise ValueError("Inventory corruption detected")

        inventory.quantity -= qty_needed
        inventory.save()

        InventoryTransaction.objects.create(
            inventory_transaction=inventory,
            user=request.user,
            product=product,
            batch=batch, 
            transaction_type='OUTBOUND',
            quantity=qty_needed,
            remarks=f"Delivered for Invoice #{invoice.id}"
        )

        bill.status = 'Delivered'
        bill.delivered_by = request.user
        bill.delivered_at = timezone.now()
        bill.save()

    messages.success(request, "Medicines delivered successfully and inventory updated.")
    return redirect('inventory:pending_medicine_deliveries')




######################################################################

from.models import Warehouse,Location
from.forms import AddWarehouseForm,AddLocationForm,QualityControlCompletionForm
from .utils import get_warehouse_stock,calculate_stock_value,calculate_stock_value2
from .utils import update_purchase_order,update_purchase_request_order,update_shipment_status 

@login_required
def manage_warehouse(request, id=None):  
    instance = get_object_or_404(Warehouse, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"
    form = AddWarehouseForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_instance=form.save(commit=False)
        form_instance.user=request.user
        form_instance.save()
        messages.success(request, message_text)
        return redirect('inventory:create_warehouse')

    datas = Warehouse.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_inventory/manage_warehouse.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })

@login_required
def delete_warehouse(request, id):
    instance = get_object_or_404(Warehouse, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('inventory:create_warehouse')

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_warehouse')



@login_required
def manage_location(request, id=None):   

    instance = get_object_or_404(Location, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"
    form = AddLocationForm(request.POST or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_instance = form.save(commit=False)
        form_instance.user=request.user
        form_instance.save()
        messages.success(request, message_text)
        return redirect('inventory:create_location')

    datas = Location.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/manage_inventory/manage_location.html', {
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
        return redirect('inventory:create_location')

    messages.warning(request, "Invalid delete request!")
    return redirect('inventory:create_location')


@login_required
def get_locations(request):
    warehouse_id = request.GET.get('warehouse_id')
    locations = Location.objects.filter(warehouse_id=warehouse_id)

    options = '<option value="">Select Location</option>'  
    for location in locations:
        options += f'<option value="{location.id}">{location.name}</option>'
    return JsonResponse(options, safe=False)





@login_required
def complete_quality_control(request, qc_id):
    quality_control = get_object_or_404(QualityControl, id=qc_id)    
    good_quantity = quality_control.good_quantity
    purchase_dispatch_item = quality_control.purchase_dispatch_item
    purchase_shipment = purchase_dispatch_item.purchase_shipment
    purchase_order = purchase_shipment.purchase_order
    purchase_request_order = purchase_order.purchase_request_order
    purchase_order_item = purchase_dispatch_item.dispatch_item
    batch_fetch = purchase_order_item.batch
  
    if request.method == 'POST':
        selected_warehouse_id = request.POST.get('warehouse')
        selected_warehouse = Warehouse.objects.get(id=selected_warehouse_id) if selected_warehouse_id else None

        form = QualityControlCompletionForm(request.POST, warehouse=selected_warehouse)
        if form.is_valid():
            warehouse = form.cleaned_data['warehouse']
            location = form.cleaned_data['location']
           
            try:
                with transaction.atomic():

                    inventory_transaction = InventoryTransaction.objects.create(
                        user=request.user,
                        warehouse=warehouse,
                        location=location,
                        product=quality_control.product,
                        batch = batch_fetch,
                        transaction_type='INBOUND',
                        quantity=good_quantity,
                        purchase_order=purchase_dispatch_item.dispatch_item.purchase_order
                    )

                    inventory, created = Inventory.objects.get_or_create(
                        warehouse=warehouse,
                        location=location,
                        product=quality_control.product,
                        batch = batch_fetch,
                        user=request.user,
                        defaults={
                            'quantity': good_quantity 
                        }
                    )
        
                    if not created:
                        inventory.quantity += good_quantity
                        inventory.save()
                        messages.success(request, "Inventory updated successfully.")
                    else:
                        messages.success(request, "Inventory created successfully.")

                    inventory_transaction.inventory = inventory
                    inventory_transaction.save()
                    messages.success(request, "Inventory and inventory_transaction linking created successfully.")
                    

            except Exception as e: 
                logger.error("Error creating delivery: %s", e)
                messages.error(request, f"An error occurred {str(e)}")
                return redirect('purchase:qc_dashboard')
                 
            purchase_dispatch_item.status = 'DELIVERED'
            purchase_dispatch_item.save()   

            update_purchase_order(purchase_order.id)      
            update_shipment_status(purchase_shipment.id)
            update_purchase_request_order(purchase_request_order.id)  
            purchase_shipment.update_shipment_status()
       
            messages.success(request, "Quality control completed and product added to inventory.")
            return redirect('purchase:qc_dashboard')
        else:      
            print(form.errors)    
            messages.error(request, "Failed to update inventory. Form is not valid.")
  

    form = QualityControlCompletionForm(initial={'batch':batch_fetch})
    return render(request, 'inventory/complete_quality_control.html', {
        'form': form,
        'quality_control': quality_control,
    })
