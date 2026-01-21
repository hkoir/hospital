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



from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView,TemplateView
from.forms import LabtestCategoryForm,LabtestCatelogueForm
from .models import LabTestCategory,LabTestCatalog
from django.urls import reverse,reverse_lazy



class LabtestCategoryCreateView(LoginRequiredMixin, TemplateView):
    template_name = "lab_tests/labtest_category_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LabtestCategoryForm()

        # Paginate warehouses
        categories = LabTestCategory.objects.all().order_by("-created_at")
        paginator = Paginator(categories, 10)
        page_number = self.request.GET.get("page")
        context['page_obj'] = paginator.get_page(page_number)
        return context

    def post(self, request, *args, **kwargs):
        form = LabtestCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            if not category.user:
                category.user = request.user
            category.save()
            return redirect(request.path)
        return self.get(request, *args, **kwargs)



class LabtestCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = LabTestCategory
    form_class = LabtestCategoryForm
    template_name = "lab_tests/labtest_category_form.html"
    success_url = reverse_lazy("lab_tests:pending_lab_test_deliveries")


class LabtestCatelogueCreateView(LoginRequiredMixin, TemplateView):
    template_name = "lab_tests/labtest_catelogue_form.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LabtestCatelogueForm()

        # Paginate warehouses
        catelogues = LabTestCatalog.objects.all().order_by("-created_at")
        paginator = Paginator(catelogues, 10)
        page_number = self.request.GET.get("page")
        context['page_obj'] = paginator.get_page(page_number)
        return context

    def post(self, request, *args, **kwargs):
        form = LabtestCatelogueForm(request.POST)
        if form.is_valid():
            catelogue = form.save(commit=False)
            if not catelogue.user:
                catelogue.user = request.user
            catelogue.save()
            return redirect(request.path)
        return self.get(request, *args, **kwargs)


class LabtestCatelogueUpdateView(LoginRequiredMixin, UpdateView):
    model =LabTestCatalog
    form_class = LabtestCatelogueForm
    template_name = "lab_tests/labtest_catelogue_form.html"
    success_url = reverse_lazy("lab_tests:pending_lab_test_deliveries")




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



######################################### Sample collection ####################

from .models import LabSampleCollection
import qrcode,base64
from io import BytesIO
from django.core.files.base import ContentFile
from .forms import LabSampleCollectionForm


def all_request_order_list(request):
    requests = LabTestRequest.objects.all().order_by("-id")

    paginator = Paginator(requests, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "lab_tests/sample/labtest_request_order_list.html", {
        "requests": requests,
        'page_obj':page_obj
    })


def request_order_items(request, request_id):
    lab_request = get_object_or_404(LabTestRequest, id=request_id)
    items = lab_request.test_items.all()
    context = {
        "lab_request": lab_request,
        "items": items
    }
    return render(request, "lab_tests/sample/labtest_request_order_items.html", context)



@login_required
def collect_sample(request, request_item_id):
    request_item = get_object_or_404(LabTestRequestItem, id=request_item_id)
    form = LabSampleCollectionForm() 
    if request.method == "POST":
        form = LabSampleCollectionForm(request.POST, request.FILES)
        if form.is_valid(): 
            sample = form.save(commit=False)
            sample.collected_by = request.user
            sample.status = 'collected'
            sample.request_item = request_item
            sample.request_order = request_item.labtest_request
            sample.collected_at = timezone.now()
            sample.save()                 
            return redirect("lab_tests:print_sample_label", sample_id=sample.id)
    return render(request, "lab_tests/sample/collect_sample.html", {
        "item": request_item,
        "form": form, 
    })

@login_required
def final_lab_report(request, order_id):
    order = get_object_or_404(LabTestResultOrder, id=order_id)
    results = order.results.all() 
    context = {
        "order": order,
        "results": results,
    }
    return render(request, "lab_tests/sample/final_lab_report.html", context)


@login_required
def print_sample_label(request, sample_id):
    sample = get_object_or_404(LabSampleCollection, id=sample_id)

    # Generate QR
    qr = qrcode.make(sample.sample_id)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_image = base64.b64encode(buffer.getvalue()).decode()

    context = {
        "sample": sample,
        "qr_image": qr_image,
    }
    return render(request, "lab_tests/sample/print_sample_label.html", context)






from django.db.models import Q

def sample_list(request):
    q = request.GET.get("q")
    samples = LabSampleCollection.objects.select_related(
        "request_order",
        "request_order__medical_record",

    )

    if q:
        samples = samples.filter(
            Q(request_order__id__icontains=q) |
            Q(request_order__medical_record__patient__name__icontains=q) |
            Q(request_order__medical_record__patient__phone__icontains=q) |
            Q(request_order__medical_record__id__icontains=q) |
            Q(request_order__test_items__lab_test__test_name__icontains=q)
        ).distinct()  
       
    samples = samples.order_by("-id") 
    return render(
        request,
        "lab_tests/sample/sample_list.html",
        {"samples": samples, "q": q}
    )


def request_sample_list(request,request_id):
    request_order = get_object_or_404(LabTestRequest,id=request_id)    
    return render(request,    
        "lab_tests/sample/request_sample_list.html",
       { 'request_order':request_order}
       
    )




@login_required
def mark_sample_receive(request, sample_id):
    sample = get_object_or_404(LabSampleCollection, id=sample_id)   
    if sample.status != "received":
        sample.status = "received"
        sample.save()
        messages.success(request, f"Sample '{sample.sample_id}' marked as RECEIVED successfully.")
    else:
        messages.warning(request, f"Sample '{sample.sample_id}' is already marked as RECEIVED.")

    return redirect("lab_tests:sample_list")

@login_required
def mark_sample_processing(request, sample_id):
    sample = get_object_or_404(LabSampleCollection, id=sample_id)   
    if sample.status != "processing":
        sample.status = "processing"
        sample.save()
        messages.success(request, f"Sample '{sample.sample_id}' marked as RECEIVED successfully.")
    else:
        messages.warning(request, f"Sample '{sample.sample_id}' is already marked as RECEIVED.")

    return redirect("lab_tests:sample_list")

@login_required
def mark_sample_completed(request, sample_id):
    sample = get_object_or_404(LabSampleCollection, id=sample_id)   
    if sample.status != "completed":
        sample.status = "completed"
        sample.save()
        messages.success(request, f"Sample '{sample.sample_id}' marked as RECEIVED successfully.")
    else:
        messages.warning(request, f"Sample '{sample.sample_id}' is already marked as RECEIVED.")

    return redirect("lab_tests:sample_list")



from appointments.models import Appointment
from medical_records.models import MedicalRecordProgress

@login_required
def create_lab_test_result_with_items(request, medical_record_id,appointment_id):
    medical_record = get_object_or_404(MedicalRecord, id=medical_record_id)

    appointment = get_object_or_404(Appointment, id=appointment_id, medical_record=medical_record)
    progress = MedicalRecordProgress.objects.filter(
        medical_record=medical_record,

    ).last()
  
    prescription = Prescription.objects.filter(
        medical_record=medical_record,
        progress=progress
    ).last()

    lab_test_request = LabTestRequest.objects.filter(
        medical_record=medical_record,
        appointment=appointment,
        progress=progress
    ).last()


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
                        test.prescription = lab_test_request_item.prescription
                        test.save(update_fields=['prescription'])

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
        order_form = LabTestResultOrderForm(initial={'medical_record': medical_record,'lab_test_request':lab_test_request,'patient_type':'OPD'})
        formset = LabTestResultFormSet(queryset=LabTestResult.objects.none())

    return render(request, 'lab_tests/create_lab_test_result_with_items.html', {
        'order_form': order_form,
        'formset': formset,
        'medical_record': medical_record,
        'lab_test_request':lab_test_request
    })







@login_required
def lab_test_order_list(request):
    search_query = request.GET.get('search', '')
    lab_test_orders =  LabTestResultOrder.objects.all().order_by('-id')
    if search_query:
        lab_test_orders = lab_test_orders.filter(
            Q(lab_test_request__requested_lab_test_code__icontains=search_query) |
            Q(medical_record__medical_record_code__icontains=search_query) |
            Q(medical_record__patient__name__icontains=search_query)|
            Q(medical_record__patient__phone__icontains=search_query) |
            Q(medical_record__patient__patient_id__icontains=search_query)
        )

    datas =lab_test_orders
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,'lab_tests/lab_test_result_order_list.html',{'page_obj':page_obj})


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
    if result_order.test_doctor:
        if result_order.test_doctor.company:
            if result_order.test_doctor.company.logo:
                logo_path = os.path.join(settings.MEDIA_ROOT, str(result_order.test_doctor.company.logo))
                if os.path.exists(logo_path):
                    pdf.drawImage(ImageReader(logo_path), 40, y - 60, width=80, height=80)

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(140, y - 20, str(result_order.test_doctor.company))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(140, y - 35, f"Email: {result_order.test_doctor.company.email} | Phone: {result_order.test_doctor.phone}")
    address = (
    result_order.test_doctor.location.address 
    if result_order.test_doctor.location 
    else result_order.test_doctor.doctor_location or "N/A")
    website = getattr(result_order.test_doctor.company, "website", "N/A")

    pdf.drawString(140, y - 50, f"Address: {address}")
    pdf.drawString(140, y - 65, f"Web: {website}")
    #pdf.drawString(140, y - 50, f"Address: {result_order.test_doctor.location.address} | Web: {result_order.test_doctor.company.website}")

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

        test_type = result.test_name.category.name
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
    pdf.drawString(40, y, f"Reviewed by:{result_order.reviewed_by}.")
    pdf.drawString(350, y, f"Approved by:{result_order.approved_by}.")
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



@login_required
def print_lab_test_order(request, order_id):
    order = get_object_or_404(LabTestResultOrder, id=order_id)
    results = order.results.all().order_by('id')
    return render(request, "lab_tests/printable_report.html", {
        "order": order,
        "results": results,
    })



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
import logging
logger = logging.getLogger(__name__)




from lab_tests.models import LabTestCatalog
import logging
logger = logging.getLogger(__name__)



@login_required
def create_external_lab_visit(request):

    LabTestBillFormSet = modelformset_factory(
        LabTestBill,
        form=LabTestBillForm,
        extra=1,
        can_delete=True
    )

    if request.method == 'POST':
        lab_visit_form = ExternalLabVisitForm(request.POST, request.FILES)
        formset = LabTestBillFormSet(request.POST)

        if lab_visit_form.is_valid() and formset.is_valid():
            with transaction.atomic():
           
                lab_visit = lab_visit_form.save(commit=False)
                patient = lab_visit.patient
                referral_source = patient.referral_source

                # Create Medical Record
                medical_record = MedicalRecord.objects.create(
                    patient=patient,
                    doctor=lab_visit.doctor if lab_visit.doctor else None,
                    external_doctor=lab_visit.doctor_ref if lab_visit.doctor_ref else None,
                    diagnosis='External lab test request',
                    treatment_plan='',
                    date=timezone.now()
                )

                valid_items = [
                    instance
                    for instance, form in zip(formset.save(commit=False), formset.forms)
                    if not form.cleaned_data.get('DELETE')
                ]

                total_amount = sum((item.lab_test_catelogue.price or 0) for item in valid_items)

                invoice = BillingInvoice.objects.create(
                    patient=patient,
                    medical_record=medical_record,
                    total_amount=total_amount,
                    total_paid=total_amount,
                    invoice_type='External-Lab-Test',
                    is_locked = True
                )

                lab_visit.medical_record = medical_record
                lab_visit.invoice = invoice
                lab_visit.save()
              
                lab_test_request, _ = LabTestRequest.objects.get_or_create(
                    medical_record=medical_record,
                    patient_type='External-Lab-Test',
                    requested_by=lab_visit.doctor,
                    external_ref = lab_visit.doctor_ref,
                    status='Unpaid'
                )
                lab_visit.lab_test_request = lab_test_request              
                lab_visit.save(update_fields=['lab_test_request'])
                

                # ====================================================
                # 4. Loop Each Test → Save + Referral Commission
                # ====================================================
                from accounting.utils import create_referral_commission_expense_journal
                from billing.utils import create_referral_transaction_for_service

                for item in valid_items:
               
                    item.invoice = invoice
                    item.status = 'Paid'
                    item.patient_type = 'External-Lab-Test'
                    item.lab_test_request_order =lab_test_request
                    item.save()
                 
                    LabTestRequestItem.objects.get_or_create(
                        labtest_request=lab_test_request,
                        lab_test=item.lab_test_catelogue, 
                        notes= item.notes,                      
                        defaults={'status': 'Pending'}

                    )

                    tx = create_referral_transaction_for_service(
                        invoice=invoice,
                        service_type='lab',
                        service_id=item.lab_test_catelogue.id,
                        service_amount=item.lab_test_catelogue.price,
                        referral_source= referral_source
                    )

                    # Create Journal entry for referral expense
                    if tx:
                        create_referral_commission_expense_journal(
                            invoice=invoice,
                            commission_amount=tx.commission_amount,
                            created_by=request.user
                        )

           
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount_paid=invoice.total_amount,
                    payment_type='External-Lab-Test',
                    payment_method='Card',
                    remarks='Payment for external patient lab tests',
                    patient_type='External-Lab-Test'
                )

           
                from accounting.utils import create_journal_entry

                create_journal_entry(
                    payment,
                    breakdown=[{'amount': invoice.total_amount, 'revenue_type': 'Lab'}],
                    description=f"Direct lab test payment by {patient.name}",
                    created_by=request.user
                )

                invoice.update_totals()
                invoice.status = (
                    'Paid' if invoice.total_paid >= invoice.total_amount else
                    'Unpaid' if invoice.total_paid == 0 else
                    'Partially Paid'
                )
                invoice.save(update_fields=['status'])

                return redirect('billing:finalize_invoice', invoice.id)
        else:
            logger.error("External Lab Visit Form Errors: %s", lab_visit_form.errors)
            logger.error("External Lab Visit Formset Errors: %s", formset.errors)
            logger.error("External Lab Visit Non-Field Errors: %s", formset.non_form_errors())
            print(f'lab visit form error {lab_visit_form.errors}')  
            print(f'formset form erros {formset.errors}')        
            messages.error(request, "There were errors in the form. Please check and try again.")

    else:
        lab_visit_form = ExternalLabVisitForm()
        formset = LabTestBillFormSet(queryset=LabTestBill.objects.none())

   
    lab_tests = LabTestCatalog.objects.all()
    test_prices = {
        str(test.id): float(test.price) if test.price else 0
        for test in lab_tests
    }

    return render(request, 'lab_tests/create_external_lab_visit.html', {
        'lab_visit_form': lab_visit_form,
        'formset': formset,
        'test_prices': json.dumps(test_prices)
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
def deliver_lab_tests(request, pk):
    result_order = get_object_or_404(LabTestResultOrder, id=pk)

    if request.method == "GET":
        return render(request, "lab_tests/deliver_confirmation.html", {
            "result_order": result_order
        })

    if request.method == "POST":
        if result_order.status == 'Completed':
            result_order.status = 'Delivered'
            result_order.save()
            result_order.results.update(status='Completed')

        messages.success(request, "Lab test successfully delivered!")
        return redirect('lab_tests:lab_test_status_list')





@login_required
def pending_lab_test_deliveries(request):
    invoice_id = request.GET.get('invoice')
    search_query = request.GET.get('search', '')

    if invoice_id:       
        invoices = BillingInvoice.objects.filter(id=invoice_id)
    else:       
        invoices = BillingInvoice.objects.filter(
            lab_test_bills__status='Paid'
        ).exclude(
            lab_test_bills__status='Delivered'
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
        lab_test_bills = invoice.lab_test_bills.exclude(status='Delivered')
        lab_test_total = sum([bill.test_fee for bill in lab_test_bills])
        invoice_data.append((invoice, lab_test_total))

    return render(request, 'lab_tests/pending_lab_test_deliveries.html', {
        'invoices': invoices_page,
        'invoice_data': invoice_data,
        'search_query': search_query
    })




