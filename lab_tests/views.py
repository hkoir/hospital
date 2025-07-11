from django.http import JsonResponse,HttpResponse
from django.shortcuts import render, get_object_or_404,redirect
from django.conf import settings
import os
from reportlab.platypus import Image, Table, TableStyle, Spacer, Paragraph, KeepTogether
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from django.shortcuts import get_object_or_404
from reportlab.lib.utils import simpleSplit
from django.contrib.auth.decorators import login_required,permission_required,user_passes_test


from.forms import LabTestFilter
from django.core.paginator import Paginator
from django.forms import modelformset_factory
from .models import LabTest,LabTestCategory,LabTestCatalog
from .models import LabTestResult
from .forms import LabTestResultForm
from.models import LabTestResultOrder,LabTestResult,LabTestRequestItem
from .forms import LabTestResultOrderForm
from.models import LabTestResult
from medical_records.models import Prescription,MedicalRecord
from.models import LabTestRequest,LabTestResultOrder
from.forms import LabTestResultFormSet
from django.contrib import messages
from reportlab.lib.utils import simpleSplit


def lab_test_search(request):
    query = request.GET.get("q", "")  
    tests = LabTestCatalog.objects.filter(test_name__icontains=query)[:10]  
    results = [{"id": test.id, "text": test.test_name} for test in tests]
    return JsonResponse({"results": results})



#============ below view is no longer needed as it has been replaced with single formset view , may still keep if result order list associate with it
@login_required
def create_lab_test_result_order(request, medical_record_id):
    if request.method == 'POST':
        form = LabTestResultOrderForm(request.POST)
        if form.is_valid():
            result_order = form.save(commit=False)
            result_order.medical_record_id = medical_record_id
            result_order.save()
            return redirect('lab_tests:add_lab_test_result', result_order_id=result_order.id)
    else:
        form = LabTestResultOrderForm()

    return render(request, 'lab_tests/create_result_order.html', {'form': form})

@login_required
def add_lab_test_result2(request, result_order_id):
    result_order = get_object_or_404(LabTestResultOrder, id=result_order_id)
    lab_test_result_items =result_order.results.all()    
    all_test_done = all(item.test_value for item in lab_test_result_items)
    if all_test_done:
        messages.warning(request, 'All tests are already completed.')
        return redirect('lab_tests:lab_test_order_list') 

    LabTestResultFormSet = modelformset_factory(LabTestResult, form=LabTestResultForm, extra=3)
    if request.method == 'POST':
        formset = LabTestResultFormSet(request.POST, request.FILES, queryset=LabTestResult.objects.none())
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.result_order_id = result_order_id
                instance.save()
            return redirect('lab_tests:lab_test_order_list')
    else:
        formset = LabTestResultFormSet(queryset=LabTestResult.objects.none())

    return render(request, 'lab_tests/add_lab_test_result.html', {
        'formset': formset
    })


@login_required
def add_lab_test_result(request, result_order_id):
    result_order = get_object_or_404(LabTestResultOrder, id=result_order_id)   

    all_requested_test_items = LabTestRequestItem.objects.filter(
        labtest_request__medical_record=result_order.medical_record
    )
    all_requested_test_count = all_requested_test_items.count()

    lab_test_result_items_count = result_order.results.count()

    if lab_test_result_items_count >= all_requested_test_count:
        messages.warning(request, 'All tests are already completed.')
        return redirect('lab_tests:lab_test_order_list')


    LabTestResultFormSet = modelformset_factory(LabTestResult, form=LabTestResultForm, extra=2)
    if request.method == 'POST':
        formset = LabTestResultFormSet(request.POST, request.FILES, queryset=LabTestResult.objects.none())
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.result_order_id = result_order_id
                instance.save()
            return redirect('lab_tests:lab_test_order_list')
    else:
        formset = LabTestResultFormSet(queryset=LabTestResult.objects.none())

    return render(request, 'lab_tests/add_lab_test_result.html', {
        'formset': formset
    })


#============================================================================================


@login_required
def create_lab_test_result_with_items(request, medical_record_id):
    medical_record = get_object_or_404(MedicalRecord, id=medical_record_id)

    lab_test_request = LabTestRequest.objects.filter(medical_record=medical_record).last()

    if request.method == 'POST':
        order_form = LabTestResultOrderForm(request.POST)
        formset = LabTestResultFormSet(request.POST, request.FILES, queryset=LabTestResult.objects.none())
        
        if order_form.is_valid() and formset.is_valid():
            order_data = order_form.cleaned_data
            expected_count = LabTestRequestItem.objects.filter(labtest_request=lab_test_request).count()
            entered_count = sum(1 for form in formset if form.cleaned_data and not form.cleaned_data.get('DELETE', False))

            if entered_count == 0:
                status = 'Pending'
            elif entered_count < expected_count:
                status = 'In Process'
            else:
                status = 'Completed'

            result_order = LabTestResultOrder.objects.create(
                    medical_record=medical_record,
                    lab_test_request=order_data['lab_test_request'],
                    test_doctor=order_data['test_doctor'],
                    test_assistance=order_data['test_assistance'],
                    summary_report=order_data['summary_report'],
                    reviewed_by=order_data['reviewed_by'],
                    approved_by=order_data['approved_by'],
                    patient_type=order_data['patient_type'],
                    status=status
                )

            result_order.results.all().delete()

            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    test = form.save(commit=False)
                    test.result_order = result_order
                    test.patient_type = result_order.patient_type
                    test.status = 'Completed'
                    test.save()

                    try:
                        lab_test_request_item = LabTestRequestItem.objects.get(
                           labtest_request=result_order.lab_test_request,
                            lab_test=test.test_name
                        )
                        lab_test_request_item.status = 'Completed'
                        # After updating all LabTestRequestItems
                        all_items = LabTestRequestItem.objects.filter(labtest_request=lab_test_request)

                        if all_items.exists() and all(item.status == 'Completed' for item in all_items):
                            lab_test_request.status = 'Completed'
                        elif any(item.status == 'Completed' for item in all_items):
                            lab_test_request.status = 'Partially-Completed'
                        else:
                            lab_test_request.status = 'Pending'

                        lab_test_request.save()

                        lab_test_request_item.save()
                    except LabTestRequestItem.DoesNotExist:
                        print("No matching LabTestRequestItem found for test:", test.test_name)

            return redirect('lab_tests:lab_test_order_list')
    else:
        order_form = LabTestResultOrderForm(initial={'medical_record': medical_record})
        formset = LabTestResultFormSet(queryset=LabTestResult.objects.none())

    return render(request, 'lab_tests/create_lab_test_result_with_items.html', {
        'order_form': order_form,
        'formset': formset,
        'medical_record': medical_record,
    })




@login_required
def lab_test_order_list(request):
    lab_test_orders =  LabTestResultOrder.objects.none()
    form = LabTestFilter(request.GET)   
    if form.is_valid():
        medical_record = form.cleaned_data['medical_record']
        lab_test_orders =  LabTestResultOrder.objects.all().order_by('-updated_at')
        if medical_record:
            lab_test_orders = lab_test_orders.filter(medical_record=medical_record)

    datas =lab_test_orders.order_by('-updated_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,'lab_tests/lab_test_result_order_list.html',{'page_obj':page_obj,'form':form})




def draw_justified_paragraph(pdf, text, x, y, max_width=500, pdf_height=800, line_height=15):  
    styles = getSampleStyleSheet()
    justified_style = ParagraphStyle(
        "Justified",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=4,  # Justified
    )

    para = Paragraph(text, justified_style)
    w, h = para.wrap(max_width, pdf_height)  # Get paragraph height

    
    while h > y - 50:  # Ensure at least 50 units remain at the bottom
        # Determine how much text fits in the available space
        available_space = y - 50
        split_text = text
        while True:
            para_temp = Paragraph(split_text, justified_style)
            _, temp_h = para_temp.wrap(max_width, pdf_height)
            if temp_h <= available_space:
                break
            split_text = split_text.rsplit(' ', 10)[0]  # Remove last 10 words and retry

        # Draw the fitting portion of text
        para_fitting = Paragraph(split_text, justified_style)
        para_fitting.wrapOn(pdf, max_width, available_space)
        para_fitting.drawOn(pdf, x, y - temp_h)

        # Move to new page and continue
        pdf.showPage()
        pdf.setFont("Helvetica", 10)
        y = pdf_height - 50  # Reset Y position
        text = text[len(split_text):].lstrip()  # Remove drawn text from original

        # Prepare new paragraph with remaining text
        para = Paragraph(text, justified_style)
        w, h = para.wrap(max_width, pdf_height)

    # Draw remaining text
    para.wrapOn(pdf, max_width, pdf_height)
    para.drawOn(pdf, x, y - h)
    return y - h - line_height  



def check_and_add_page_break(pdf, y_position, content_height, page_height):  
    if y_position - content_height < 50: 
        pdf.showPage()  # Start a new page
        return page_height - 50  
    return y_position - content_height 

def limit_text(text, word_limit=25, char_limit=120):
    words = text.split()
    trimmed_text = ' '.join(words[:word_limit])
    return trimmed_text[:char_limit]  # This ensures it's not more than 300 characters




def generate_test_report_pdf(request, result_order_id):
    result_order = get_object_or_404(LabTestResultOrder, id=result_order_id)
    #prescription = result_order.medical_record.medical_record_prescriptions.first()
    medical_record = result_order.medical_record
    prescription = medical_record.prescriptions.first()
    lab_test_results = result_order.results.all()

    age = medical_record.patient.calculate_age()
    dob_formatted = medical_record.patient.date_of_birth.strftime("%d-%b-%Y")
    gender = medical_record.patient.gender
    date_formatted = medical_record.date.strftime("%d-%b-%Y")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Lab_Report_{medical_record.patient.name}.pdf"'
    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    # --- Header: Logo & Hospital Info ---
    if result_order.test_doctor.company.logo:
        logo_path = os.path.join(settings.MEDIA_ROOT, str(result_order.test_doctor.company.logo))
        if os.path.exists(logo_path):
            pdf.drawImage(ImageReader(logo_path), 40, y - 60, width=80, height=80)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(140, y - 20, str(result_order.test_doctor.company))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(140, y - 35, f"Email: {result_order.test_doctor.company.email} | Phone: {result_order.test_doctor.phone}")
    pdf.drawString(140, y - 50, f"Address: {result_order.test_doctor.location.address} | Web: {result_order.test_doctor.company.website}")

    y -= 100

    # --- Patient Info ---
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Patient Information")
    pdf.setFont("Helvetica", 10)
    y -= 15
    pdf.drawString(40, y, f"Name: {medical_record.patient.name} | Phone: {medical_record.patient.phone}")
    y -= 15
    pdf.drawString(40, y, f"DOB: {dob_formatted} | Age: {age} | Gender: {gender}")
    y -= 15
    pdf.drawString(40, y, f"Patient ID: {medical_record.patient.id}")

    # --- Doctor Info ---
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(360, y + 30, "Doctor Ref:")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(360, y + 15, f"Dr. {medical_record.doctor.name} - {medical_record.doctor.specialization}")
    pdf.drawString(360, y, f"Reg. No: {medical_record.doctor.medical_license_number}")
    pdf.drawString(360, y - 15, f"Date: {date_formatted}")

    y -= 60

    # --- Lab Test Section ---
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, "Lab Test Results")
    y -= 20
    if prescription:
        pdf.setFont("Helvetica", 10)
        pdf.drawString(40, y, f"Prescription Ref: {prescription.prescription_id}")
        y -= 15

    # --- Table Headers ---
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(40, y, "Test Type")
    pdf.drawString(120, y, "Test Name")
    pdf.drawString(240, y, "Result")
    pdf.drawString(300, y, "Standard")
    pdf.drawString(420, y, "Findings")  # Adjusted for larger width
   
    pdf.line(40, y - 2, 650, y - 2)
    y -= 15

    # --- Test Results Loop ---
    pdf.setFont("Helvetica", 10)
    for result in lab_test_results:
        if y < 100:
            pdf.showPage()
            y = height - 50
            # Reprint headers after page break
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(40, y, "Test Type")
            pdf.drawString(120, y, "Test Name")
            pdf.drawString(240, y, "Result")
            pdf.drawString(300, y, "Standard")
            pdf.drawString(420, y, "Findings")  # Adjusted for larger width
          
            pdf.line(40, y - 2, 650, y - 2)  # Adjusted line width to accommodate longer columns
            y -= 15
            pdf.setFont("Helvetica", 10)

        test_type = result.test_name.test_type
        test_name = result.test_name.test_name
        test_value = result.test_value
        standard_value = result.standard_value
        findings = result.findings or "-"
        findings = limit_text(findings)
        findings_lines = simpleSplit(findings, 'Helvetica', 10, 180)

        # Draw the values, adjusting the length for findings and remarks
        pdf.drawString(50, y, test_type if test_type else "-")
        pdf.drawString(110, y, test_name if test_name else "-")
        pdf.drawString(250, y, test_value if test_value else "-")
        pdf.drawString(320, y, standard_value if standard_value else "-")
      
        for i, line in enumerate(findings_lines):
            pdf.drawString(400, y - i * 12, line)  # Adjust Y value to accommodate each line of findings
        y -= len(findings_lines) * 12 + 20 
       
        y -= 20        

        # --- Digital Report Section ---
    if result_order.summary_report:
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, "Report Summary")
        y -= 20
        pdf.setFont("Helvetica", 10)

        # Split long paragraphs into lines to fit in the PDF
        lines = simpleSplit(result_order.summary_report, 'Helvetica', 10, 500)
        for line in lines:
            if y < 100:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 10)
            pdf.drawString(40, y, line)
            y -= 15


    # --- Footer Section ---
    y -= 20
    pdf.setFont("Helvetica-Bold", 10)  
    pdf.drawString(40, y, f"Reviewed by:{medical_record.test_results.first().test_doctor}.")
    pdf.drawString(350, y, f"Approved by:{medical_record.test_results.first().test_assistance}.")
    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, "Get well soon! Follow your doctor's advice.")
    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, "Doctor's Signature: ____________________")
    y -= 20
    pdf.drawString(50, y, f"{medical_record.doctor.name} - {medical_record.doctor.specialization}")
    y -= 15
    pdf.drawString(50, y, str(medical_record.doctor.medical_license_number))

    # --- QR Code ---
    qr_buffer = BytesIO()
    generate_qr_code("https://xyzhospital.com/verify-prescription", qr_buffer)
    qr_image = Image(qr_buffer, 0.8 * inch, 0.8 * inch)
    qr_image.wrapOn(pdf, width, height)
    qr_image.drawOn(pdf, 400, y - 30)

    pdf.save()
    return response





@login_required
def download_test_report(request, result_order_id):
    return generate_test_report_pdf(request,result_order_id)




def generate_qr_code(data, filename):
    qr = qrcode.make(data)
    qr.save(filename)






#================================ external lab test ============================

from .forms import ExternalLabVisitForm
from billing.models import BillingInvoice,Payment,LabTestBill
from billing.forms import LabTestBillForm
from django.utils import timezone
from django.forms import modelformset_factory
import json
from django.db import transaction
from django.views.generic import ListView
from .models import ExternalLabVisit




@login_required
def create_external_lab_visit(request):
    LabTestBillFormSet = modelformset_factory(LabTestBill, form=LabTestBillForm, extra=1, can_delete=True)

    if request.method == 'POST':
        lab_visit_form = ExternalLabVisitForm(request.POST, request.FILES)
        formset = LabTestBillFormSet(request.POST)

        if lab_visit_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Save lab visit (without medical_record or invoice yet)
                lab_visit = lab_visit_form.save(commit=False)
                patient = lab_visit.patient

                # Create medical record
                medical_record = MedicalRecord.objects.create(
                    patient=patient,
                    doctor=lab_visit.doctor,  # fallback to some default if needed
                    diagnosis='External lab test request',
                    treatment_plan='',
                    date=timezone.now()
                )

                # Calculate total amount
                total_amount = 0
                instances = formset.save(commit=False)
                for instance, form in zip(instances, formset.forms):
                    if form.cleaned_data.get('DELETE'):
                        continue
                    total_amount += instance.lab_test.test.price or 0

                # Create invoice
                invoice = BillingInvoice.objects.create(
                    patient=patient,
                    total_amount=total_amount,
                    total_paid=total_amount,
                    medical_record=medical_record,
                    invoice_type='External-Lab-Test'
                )

                # Link medical record and invoice to lab visit
                lab_visit.medical_record = medical_record
                lab_visit.invoice = invoice
                lab_visit.save()

                # Save lab test bills with invoice link
                for instance, form in zip(instances, formset.forms):
                    if form.cleaned_data.get('DELETE'):
                        continue
                    instance.invoice = invoice
                    instance.save()

                    # Ensure lab test request record exists
                    LabTestRequest.objects.get_or_create(
                        medical_record=medical_record,
                        lab_test=instance.lab_test,
                        patient_type='External-Lab-Test'
                    )

                # Record payment
                Payment.objects.create(
                    invoice=invoice,
                    amount_paid=invoice.total_amount,
                    payment_type='External-Lab-Test',
                    payment_method='Card',
                    remarks='Payment for external patient lab test only',
                    patient_type='External-Lab-Test'
                )

                # Update invoice payment status
                invoice.update_totals()
                if invoice.total_paid >= invoice.total_amount:
                    invoice.status = 'Paid'
                elif invoice.total_paid == 0:
                    invoice.status = 'Unpaid'
                else:
                    invoice.status = 'Partially Paid'
                invoice.save(update_fields=['status'])

                return redirect('lab_tests:external_lab_visit_detail', lab_visit.id)

    else:
        lab_visit_form = ExternalLabVisitForm()
        formset = LabTestBillFormSet(queryset=LabTestBill.objects.none())

    lab_tests = LabTest.objects.all()
    test_prices = {
        str(test.id): float(test.test.price) if test.test.price else 0
        for test in lab_tests
    }
    test_prices_json = json.dumps(test_prices)

    return render(request, 'lab_tests/create_external_lab_visit.html', {
        'lab_visit_form': lab_visit_form,
        'formset': formset,
        'test_prices': test_prices_json
    })





class ExternalLabVisitListView(ListView):
    model = ExternalLabVisit
    template_name = 'lab_tests/external_lab_visit_list.html'
    context_object_name = 'lab_visits'
    paginate_by = 20  # optional pagination
    ordering = ['-created_at']  # show most recent first



def external_lab_visit_detail(request, pk):
    lab_visit = get_object_or_404(ExternalLabVisit, pk=pk)
    medical_record = lab_visit.medical_record
    patient = lab_visit.patient
    doctor = lab_visit.doctor

    # Get related lab test requests (if you want to show them)
    lab_test_requests = medical_record.lab_tests_records.all() if medical_record else []
    total_amount =0
    for test in lab_test_requests:        
        total_amount += test.lab_test.test.price

    return render(request, 'lab_tests/external_lab_visit_detail.html', {
        'lab_visit': lab_visit,
        'medical_record': medical_record,
        'patient': patient,
        'doctor': doctor,
        'lab_test_requests': lab_test_requests,
        'total_amount':total_amount
    })










def lab_test_status_list(request):
    result_orders = LabTestResultOrder.objects.select_related(
        'medical_record__patient'
    ).prefetch_related(
        'results'
    ).order_by('-recorded_at')  # newest first

    context = {
        'result_orders': result_orders
    }
    return render(request, 'lab_tests/lab_test_status_list.html', context)





@login_required
def deliver_lab_tests(request, result_order_id):
    result_order = get_object_or_404(LabTestResultOrder, id=result_order_id)

    # Only allow delivery if already completed
    if result_order.status == 'Completed':
        result_order.status = 'Delivered'
        result_order.save()

        # Optional: Mark individual results as delivered too
        result_order.results.update(status='Completed')  # or 'Delivered' if that’s a valid status

    return redirect('lab_tests:lab_test_status_list')  # Update with your actual URL name




def pending_lab_test_deliveries(request):
    invoices = BillingInvoice.objects.prefetch_related('lab_test_bills', 'medical_record')\
        .filter(lab_test_bills__status='Paid').distinct()    

    invoice_data = []
    for invoice in invoices:
        lab_test_bills = invoice.lab_test_bills.filter(status='Paid')
        lab_test_total = sum([bill.test_fee for bill in lab_test_bills])
        invoice_data.append((invoice, lab_test_total ))  

    return render(request, 'lab_tests/pending_lab_test_deliveries.html', {'invoices': invoices,'invoice_data':invoice_data})



