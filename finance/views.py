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



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
from django.utils import timezone
from num2words import num2words


from core.models import Employee,Company
from supplier.models import Supplier
from logistics.models import PurchaseShipment,PurchaseDispatchItem
from purchase.models import PurchaseOrder
from .models import PurchaseInvoice,PurchasePayment,PurchaseInvoiceAttachment
from .forms import PurchaseInvoiceForm, PurchasePaymentForm
from core.forms import CommonFilterForm
from django.core.paginator import Paginator
from .forms import PurchaseInvoiceAttachmentForm,PurchasePaymentAttachmentForm
from accounting.models import JournalEntry, JournalEntryLine, Account,FiscalYear







def money_receipt(request):
    return render(request,'finance/money_receipt.html')


@login_required
def create_purchase_invoice(request, order_id):
    purchase_shipment = get_object_or_404(PurchaseShipment, id=order_id) 

    if purchase_shipment.shipment_invoices.count() > 0:
        if purchase_shipment.shipment_invoices.filter(status__in=['SUBMITTED', 'PARTIALLY_PAYMENT', 'FULLY_PAYMENT']).count() == purchase_shipment.shipment_invoices.count():
            messages.error(request, "All invoices for this shipment have already been submitted or paid.")
            return redirect('purchase:purchase_order_list')
    else:
         pass     

    try:       
        if purchase_shipment.status != 'DELIVERED':
            messages.error(request, "Cannot create an invoice: Shipment status is not 'Delivered yet'.")
            return redirect('purchase:purchase_order_list') 
    except PurchaseShipment.DoesNotExist:
        messages.error(request, "Cannot create an invoice: No shipment found for this order.")
        return redirect('purchase:purchase_order_list') 

    initial_data = {
        'purchase_shipment': purchase_shipment,
        'amount_due': purchase_shipment.purchase_order.total_amount
    }

    if request.method == 'POST':
        form = PurchaseInvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.user = request.user
            invoice.status ='SUBMITTED'
            invoice.save()
            messages.success(request, "Invoice created and submitted successfully.")
            return redirect('purchase:purchase_order_list')  
        else:
            messages.error(request, "Error creating invoice.")
    else:
        form = PurchaseInvoiceForm(initial=initial_data)
    return render(request, 'finance/purchase/create_invoice.html', {'form': form})


@login_required
def add_purchase_invoice_attachment(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)    
    if request.method == 'POST':
        form = PurchaseInvoiceAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.purchase_invoice = invoice  
            attachment.user=request.user
            attachment.save()
            return redirect('purchase:purchase_order_list')
    else:
        form = PurchaseInvoiceAttachmentForm()

    return render(request, 'finance/attachmenet/add_invoice_attachment.html', {'form': form, 'invoice': invoice})





@login_required
def create_purchase_payment(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)

    if invoice.status not in ["SUBMITTED", "PARTIALLY_PAID",]:
        messages.error(request, "Cannot create a payment: Invoice is not submitted or submitted and fully paid.")
        return redirect('purchase:purchase_order_list')

    remaining_balance = invoice.remaining_balance

    if request.method == 'POST':
        form = PurchasePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.purchase_invoice = invoice
            payment.user = request.user

            if payment.amount > remaining_balance:
                messages.error(request, f"Payment cannot exceed the remaining balance of {remaining_balance}.")
                return redirect('finance:create_purchase_payment', invoice_id=invoice.id)
            
            if payment.amount < remaining_balance:
                payment.status = "PARTIALLY_PAID"
            else:
                payment.status = "FULLY_PAID"

            payment.save()

            # ---------------------------
            # Create Journal Entry
            # ---------------------------       
            fiscal_year = FiscalYear.get_active()

            journal_entry = JournalEntry.objects.create(
            date=timezone.now().date(),
            fiscal_year=fiscal_year,
            description=f"Purchase Payment for Invoice {invoice.invoice_number}",
            reference=f"Purchase invoice-{invoice.id}",
        )

            # Accounts
            ap_account = Account.objects.get(code="2110")    # Accounts Payable
            cash_account = Account.objects.get(code="1110")  # Cash/Bank
            vat_account = Account.objects.get(code="2131")   # VAT Payable (liability)
            ait_account = Account.objects.get(code="1150")   # AIT Receivable (asset)
            purchase_account = Account.objects.get(code="5140")  # Purchase Expense

            # Amounts
            amount_due = invoice.amount_due
            vat_amount = invoice.vat_amount or 0
            ait_amount = invoice.ait_amount or 0
            net_due_amount = invoice.net_due_amount or amount_due   # after tax adjustments

            # --- Purchases Debit (Net of VAT if exclusive) ---
            JournalEntryLine.objects.create(
                entry=journal_entry,
                account=purchase_account,
                debit=amount_due,
                credit=0
            )

            # --- VAT Handling ---
            if vat_amount > 0:
                if invoice.VAT_type == "exclusive":
                    # Debit VAT receivable / Input VAT (treated as asset until credited later)
                    JournalEntryLine.objects.create(
                        entry=journal_entry,
                        account=vat_account,
                        debit=vat_amount,
                        credit=0
                    )
                else:
                    # inclusive → already included in amount_due, no extra entry needed
                    pass

            # --- AIT Handling ---
            if ait_amount > 0:
                if invoice.AIT_type == "exclusive":
                    # Debit AIT receivable (advance tax paid)
                    JournalEntryLine.objects.create(
                        entry=journal_entry,
                        account=ait_account,
                        debit=ait_amount,
                        credit=0
                    )
                else:
                    # inclusive → already inside amount_due, split required
                    JournalEntryLine.objects.create(
                        entry=journal_entry,
                        account=ait_account,
                        debit=ait_amount,
                        credit=0
                    )

            # --- Credit Accounts Payable ---
            JournalEntryLine.objects.create(
                entry=journal_entry,
                account=ap_account,
                debit=0,
                credit=amount_due + vat_amount - ait_amount
            )

            # --- Payment (Cash/Bank) ---
            JournalEntryLine.objects.create(
                entry=journal_entry,
                account=cash_account,
                debit=0,
                credit=net_due_amount
            )


            # ---------------------------
            # Update Invoice Status
            # ---------------------------
            if invoice.is_fully_paid:
                invoice.status = "FULLY_PAID"
            elif invoice.remaining_balance > 0:
                invoice.status = "PARTIALLY_PAID"
            invoice.save()

            messages.success(request, "Payment created successfully with journal entry.")
            return redirect('finance:purchase_invoice_list')
    else:       
        form = PurchasePaymentForm(initial={
            'purchase_invoice': invoice,  
            'amount': remaining_balance
        })

    return render(request, 'finance/purchase/create_payment.html', {
        'form': form,
        'purchase_invoice': invoice.invoice_number,
        'remaining_balance': remaining_balance
    })




@login_required
def add_purchase_payment_attachment(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)    
    if request.method == 'POST':
        form = PurchasePaymentAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.purchase_invoice = invoice  
            attachment.user=request.user
            attachment.save()
            messages.success(request,'attachement success')
            return redirect('purchase:purchase_order_list')
    else:
        form = PurchasePaymentAttachmentForm()
    return render(request, 'finance/attachmenet/add_invoice_attachment.html', {'form': form, 'invoice': invoice})


from django.db.models import Sum, F, Q

@login_required
def generate_purchase_invoice(purchase_order):
    valid_shipments = PurchaseShipment.objects.filter(
        purchase_order=purchase_order, status='DELIVERED'
    )

    valid_dispatch_items = PurchaseDispatchItem.objects.filter(
        purchase_shipment__in=valid_shipments, status='DELIVERED'
    )

    unpaid_invoices = PurchaseInvoice.objects.filter(
        purchase_shipment__in=valid_shipments
    ).exclude(status__in=['CANCELLED']) 

    if not unpaid_invoices.exists():
        return {
            "error": "No pending invoices for this purchase order",
            "purchase_order": purchase_order,
            "valid_shipments": valid_shipments,
            "valid_dispatch_items": valid_dispatch_items,
            "product_summary": [],
            "grand_total": 0,
            "vat_amount": 0,
            "ait_amount": 0,
            "net_payable": 0,
            "paid_amount": 0,
            "due_amount": 0,
            "invoice_status": [],
        }

    # --- your existing calculations ---
    invoice_summary = unpaid_invoices.aggregate(
        total_vat=Sum('vat_amount'),
        total_ait=Sum('ait_amount'),
        total_net=Sum('net_due_amount'),
        total_paid=Sum('purchase_payment_invoice__amount'),
        total_due=Sum(F('net_due_amount') - F('purchase_payment_invoice__amount'))
    )

    product_data = valid_dispatch_items.values(
        'dispatch_item__product__name',
        'dispatch_item__product__unit_price',
        'dispatch_item__batch__purchase_price'
    ).annotate(
        total_quantity=Sum('dispatch_quantity'),
        total_amount=Sum(
            F('dispatch_quantity') * F('dispatch_item__batch__purchase_price')  
        )
    )

    product_summary = [
        {
            "product_name": item['dispatch_item__product__name'],
            "unit_price": item['dispatch_item__batch__purchase_price'],
            "quantity": item['total_quantity'],
            "amount": item['total_amount']
        }
        for item in product_data
    ]

    grand_total = sum(item['amount'] for item in product_summary)

    return {
        "purchase_order": purchase_order,
        "valid_shipments": valid_shipments,
        "valid_dispatch_items": valid_dispatch_items,
        "product_summary": product_summary,
        "grand_total": grand_total,
        "vat_amount": invoice_summary['total_vat'] or 0,
        "ait_amount": invoice_summary['total_ait'] or 0,
        "net_payable": invoice_summary['total_net'] or 0,
        "paid_amount": invoice_summary['total_paid'] or 0,
        "due_amount": invoice_summary['total_due'] or 0, 
        "invoice_status": list(unpaid_invoices.values_list('status', flat=True).distinct())  
    }



@login_required
def generate_purchase_invoice_pdf(purchase_order, mode="download"):
    supplier = purchase_order.supplier
    supplier_address = 'Unknown'
    supplier_info = Supplier.objects.filter(id=purchase_order.supplier_id).first()
    if supplier_info:
        supplier_name = supplier_info.name
        supplier_phone = supplier_info.phone
        supplier_email = supplier_info.email
        supplier_website = supplier_info.website
        if supplier_info.supplier_locations.first():
            supplier_address = supplier_info.supplier_locations.first().address
        supplier_logo_path = supplier_info.logo.path if supplier_info.logo else 'D:/SCM/dscm/media/company_logo/Logo.png'

    company_name = None
    company_address = None
    company_email = None
    company_phone = None
    company_website = None
    logo_path = None

    cfo_data = Employee.objects.filter(position__name='CFO').first()
    if cfo_data:
        location = cfo_data.location.name
        company_name = cfo_data.location.company.name
        company_address = cfo_data.location.address
        company_email = cfo_data.location.email
        company_phone = cfo_data.location.phone
        company_website = cfo_data.location.company.website
        company_logo_path = cfo_data.location.company.logo.path if cfo_data.location.company.logo else 'D:/SCM/dscm/media/company_logo/Logo.png'

    invoice_data = generate_purchase_invoice(purchase_order)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']

    if supplier_logo_path:
        logo_width, logo_height = 60, 60
        c.drawImage(supplier_logo_path, 50, 710, width=logo_width, height=logo_height)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(130, 750, f'{supplier_name}')
    c.setFont("Helvetica", 10)
    c.drawString(130, 735, f' Address:{supplier_address}')
    c.drawString(130, 720, f' Phone: {supplier_phone} | Email: {supplier_email}')
    c.drawString(130, 705, f"Website: {supplier_website}")

    # Customer Info
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 670, "Customer Information:")
    c.setFont("Helvetica", 10)
    c.drawString(50, 655, f"Customer: {company_name}")
    c.drawString(50, 640, f"Phone: {company_phone}")
    c.drawString(50, 625, f"Website: {company_website}")

    PO_updated_at_date = purchase_order.updated_at.strftime("%Y-%m-%d")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 600, f"PO: {purchase_order.order_id} | Date: {PO_updated_at_date}")
    shipment_id = purchase_order.purchase_shipment.first().shipment_id if purchase_order.purchase_shipment.exists() else "N/A"
    c.drawString(50, 585, f"Shipment ID: {shipment_id}")
    c.drawString(50, 570, f"Invoice Date: {timezone.now().date()}")

    c.line(30, 550, 580, 550)
    y_position = 530
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, y_position, "Product Name")
    c.drawString(200, y_position, "Unit Price")
    c.drawString(350, y_position, "Quantity")
    c.drawString(450, y_position, "Amount")
    y_position -= 10
    c.line(30, y_position, 580, y_position)

    y_position -= 20
    c.setFont("Helvetica", 10)
    for item in invoice_data['product_summary']:
        if y_position < 100:
            c.showPage()
            y_position = 750  

        c.drawString(30, y_position, item["product_name"])
        c.drawString(200, y_position, f"${item['unit_price']:.2f}")
        c.drawString(350, y_position, str(item['quantity']))
        c.drawString(450, y_position, f"${item['amount']:.2f}")
        y_position -= 20

    # Adding VAT, AIT, and Net Due to the PDF
    y_position -= 30
    c.setFont("Helvetica-Bold", 12)

    c.drawString(350, y_position,"Grand Total:")
    c.drawString(450, y_position, f"${invoice_data['grand_total']:.2f}")

    y_position -= 20
    c.setFont("Helvetica-Bold", 12)

    c.drawString(350, y_position, "AIT:")
    c.drawString(450, y_position, f"${invoice_data['ait_amount']:.2f}")

    y_position -= 20
    c.setFont("Helvetica-Bold", 12)
    
    c.drawString(350, y_position, "VAT:")
    c.drawString(450, y_position, f"${invoice_data['vat_amount']:.2f}")
    
    y_position -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, y_position, "Net Due:")
    c.drawString(450, y_position, f"${invoice_data['net_payable']:.2f}")

    y_position -= 20
    c.setFont("Helvetica", 10)
    Net_total = num2words(invoice_data['net_payable'], to='currency', lang='en').replace("euro", "Taka").replace("cents", "paisa").capitalize()
    c.drawString(50, y_position, f"Amount in Words: {Net_total}")

    y_position -= 60
    c.setFont("Helvetica", 12)
    c.drawString(50, y_position, "Authorized Signature: ___________________")
    y_position -= 20
    c.drawString(50, y_position, f"Name: {cfo_data.name if cfo_data else '...............'}")
    y_position -= 20
    c.drawString(50, y_position, f"Designation: {cfo_data.position.name if cfo_data else '...............'}")

    y_position -= 40
    c.setFont("Helvetica", 9)
    c.setFillColor('gray')
    c.drawString(50, y_position, "Note: Signature not mandatory due to computerized authorization.")
    c.drawString(50, y_position - 15, "For inquiries, contact: support@mymeplus.com | Phone: 01743800705")
    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    if mode == 'preview':
        response['Content-Disposition'] = f'inline; filename="invoice_{purchase_order.id}.pdf"'
    else:  # Default to download
        response['Content-Disposition'] = f'attachment; filename="invoice_{purchase_order.id}.pdf"'
    return response



@login_required
def download_purchase_invoice(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)   
    mode = request.GET.get('mode', 'download')     
    return generate_purchase_invoice_pdf(purchase_order,mode=mode)




@login_required
def purchase_invoice_list(request):
    invoice_number = None
    invoice_list = PurchaseInvoice.objects.all().order_by('-created_at')
    invoices = invoice_list.annotate(total_paid=Sum('purchase_payment_invoice__amount'))
    form = CommonFilterForm(request.GET or None)
    if form.is_valid():
        invoice_number = form.cleaned_data['purchase_invoice_id']
        if invoice_number:
            invoices = invoices.filter(invoice_number = invoice_number)

    paginator = Paginator(invoices, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    form=CommonFilterForm()

    return render(request, 'finance/purchase/invoice_list.html',
     {
      'invoices': invoices,
      'page_obj':page_obj,
      'form':form,
      'invoice_number':invoice_number

    })


@login_required
def purchase_invoice_detail(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    payments = invoice.purchase_payment_invoice.all() 
    return render(request, 'finance/purchase/invoice_details.html', {
        'invoice': invoice,
        'payments': payments,
    })



###########################################################################################


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





from billing.models import BillingInvoice, ConsultationBill, MedicineBill, LabTestBill, OTBill,WardBill
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.dateparse import parse_date
from datetime import datetime




from django.utils.timezone import now
from datetime import timedelta


def revenue_report(request):
    today = now().date()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    today_param = request.GET.get('today')
    month_param = request.GET.get('this_month')

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today.replace(month=1, day=1)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today

    if today_param:
        start_date = end_date = today
    elif month_param:
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = (next_month - timedelta(days=next_month.day))

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    invoice_filters = {}
  
    invoice_filters['created_at__date__range'] = (start_date, end_date)

    summary_data = BillingInvoice.objects.filter(**invoice_filters).values('invoice_type').annotate(
        total_amount=Sum('total_amount')
    )

    labels = []
    amounts = []
    total_revenue = 0
    labels_amounts = []

    for item in summary_data:
        label = item['invoice_type']
        amount = float(item['total_amount'] or 0)
        total_revenue += amount
        labels.append(label)
        amounts.append(amount)
        labels_amounts.append((label, amount))

    revenue_sections = []
    consultation_total = ConsultationBill.objects.filter(invoice__in=BillingInvoice.objects.filter(**invoice_filters)).aggregate(
        total=Sum('consultation_fee')
    )['total'] or 0
    revenue_sections.append({'name': 'Consultation', 'total': float(consultation_total)})

    medicine_total = MedicineBill.objects.filter(invoice__in=BillingInvoice.objects.filter(**invoice_filters)).annotate(
        total_price=ExpressionWrapper(F('price_per_unit') * F('quantity'), output_field=DecimalField())
    ).aggregate(total=Sum('total_price'))['total'] or 0
    revenue_sections.append({'name': 'Medicine', 'total': float(medicine_total)})

    lab_total = LabTestBill.objects.filter(invoice__in=BillingInvoice.objects.filter(**invoice_filters)).aggregate(
        total=Sum('test_fee')
    )['total'] or 0
    revenue_sections.append({'name': 'Lab Test', 'total': float(lab_total)})
    ward_total = WardBill.objects.filter(invoice__in=BillingInvoice.objects.filter(**invoice_filters)).aggregate(
        total=Sum('total_bill')
    )['total'] or 0
    revenue_sections.append({'name': 'Ward', 'total': float(ward_total)})

    try:
        from billing.models import OTBill
        ot_total = OTBill.objects.filter(invoice__in=BillingInvoice.objects.filter(**invoice_filters)).aggregate(
            total=Sum('total_charge')
        )['total'] or 0
        revenue_sections.append({'name': 'OT', 'total': float(ot_total)})
    except ImportError:
        pass

    context = {
        'labels': json.dumps(labels),
        'amounts': json.dumps(amounts),
        'labels_amounts': labels_amounts,
        'total_revenue': total_revenue,
        'revenue_sections': json.dumps(revenue_sections),  # For JS
        'revenue_section_data': revenue_sections,          # For table display
        'start_date': start_date,
        'end_date': end_date,       
      
        "today": bool(today_param),
        "this_month": bool(month_param),
    }

    return render(request, 'finance/revenue_report.html', context)






def top_expenses_head(request):
    today = now().date()
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    today_param = request.GET.get('today')
    month_param = request.GET.get('this_month')

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else today.replace(month=1, day=1)
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else today

    if today_param:
        start_date = end_date = today
    elif month_param:
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = (next_month - timedelta(days=next_month.day))

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    expenses_qs = AllExpenses.objects.all()    
    expenses_qs = expenses_qs.filter(created_at__range=(start_date,end_date))  

    expense_data = (
        expenses_qs.values('expense_head')
        .annotate(total_amount=Sum('amount'))
        .order_by('-total_amount')[:10]
    )

    all_expenses = expenses_qs.order_by('-id')

    expense_heads = [data['expense_head'] for data in expense_data]
    amounts = [float(data['total_amount']) for data in expense_data]
    total_amount = sum(amounts)

    combined = zip(expense_heads, amounts)

    paginator = Paginator(all_expenses, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'finance/top_expense_head.html', {
        'expense_heads': json.dumps(expense_heads),
        'amounts': json.dumps(amounts),
        'combined_data': combined,
        'page_obj': page_obj,
        'total_amount': total_amount,
        'start_date': start_date,
        'end_date': end_date,
      
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
        estimated_salary_paid = (emp.salary_structure.net_salary() * months_passed
                         if emp.salary_structure else Decimal(0.00))

    total_income = total_income or Decimal("0")
    total_doctor_payment = total_doctor_payment or Decimal("0")
    other_expenses = other_expenses or Decimal("0")
    estimated_salary_paid = estimated_salary_paid or Decimal("0")
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





