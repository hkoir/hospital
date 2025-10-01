
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required,permission_required,user_passes_test

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,Image,KeepTogether
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.lib.pagesizes import LETTER,A4
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.units import inch

import qrcode
from django.utils import timezone
from django.db import transaction

from django.contrib import messages
from django.conf import settings
import os
import json
from io import BytesIO
from django.http import HttpResponse,JsonResponse
from math import ceil
from django.utils.timezone import now as tz_now, is_naive, make_aware,now
from datetime import datetime, date, timedelta,time

from django.core.paginator import Paginator
from decimal import Decimal
from django.db import models
from django.db.models import Q

from medical_records.forms import MedicalRecordForm, PrescriptionForm
from django.forms import modelformset_factory
from lab_tests.models import LabTest,LabTestRequest,LabTestCatalog
from lab_tests.forms import LabTestForm
from appointments.models import Appointment
from medical_records.models import MedicalRecord, Prescription
from billing.models import WardBill,BillingInvoice
from billing.forms import CommonFilterForm
from facilities.models import BedAssignmentHistory
from.models import PatientAdmission
from .forms import PatientAdmissionForm, BedAssignmentForm,PatientForm


from .models import Patient
from lab_tests.models import SuggestedLabTestRequest
from .models import DischargeReport
from.forms import DischargeReportForm
from facilities.models import Bed

from patients.utils import calculate_billed_days,update_room_occupancy,update_ward_occupancy


from medical_records.models import PrescribedMedicine

PrescriptionFormSet = modelformset_factory(
    PrescribedMedicine, 
    form=PrescriptionForm, 
    extra=1, 
    can_delete=True 
)




def patient_list(request):
    search_query = request.GET.get('search', '')
    patients = Patient.objects.all()

    if search_query:
        patients = patients.filter(
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone__icontains=search_query)|
            Q(name__icontains=search_query)
        )

    datas = patients
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'patients': patients,
        'page_obj':page_obj
    }
    return render(request, 'patients/all_patient_list.html', context)




@login_required
def patient_admission_create(request):
    if request.method == 'POST':
        form = PatientAdmissionForm(request.POST,request.FILES)
        if form.is_valid():
            with transaction.atomic():
                admission = form.save(commit=False)
                now = timezone.now()
                bed_instance = form.cleaned_data['assigned_bed']
                patient_photo = form.cleaned_data.get('patient_photo')

                admission.admission_date = now
                admission.bed_assignment_date = now
                admission.save()
                patient = admission.patient
                doctor = admission.admitting_doctor

                if patient_photo:
                    patient.patient_photo = patient_photo
                    patient.save()

                # Assign billing invoice first
                billing_invoice, created = BillingInvoice.objects.get_or_create(
                    patient=patient,
                    admission=admission,
                    invoice_type='IPD',
                    patient_type='IPD',
                    defaults={'status': 'Unpaid'}
                )
                if not created and billing_invoice.status != 'Unpaid':
                    billing_invoice.status = 'Unpaid'
                    billing_invoice.save(update_fields=['status'])

                bed_instance.is_occupied = True
                bed_instance.save(update_fields=["is_occupied"])

                update_room_occupancy(bed_instance.room)
                update_ward_occupancy(bed_instance.ward)

                BedAssignmentHistory.objects.create(
                    patient=patient,
                    ward=bed_instance.ward,
                    room=bed_instance.room,
                    bed=bed_instance,
                    assigned_at=now,
                )

                WardBill.objects.create(
                    invoice=billing_invoice,
                    patient_admission=admission,
                    bed=bed_instance,
                    room=bed_instance.room,
                    ward=bed_instance.ward,
                    charge_per_day=bed_instance.daily_charge,
                    assigned_at=now
                )

                medical_record=MedicalRecord.objects.create(
                    patient=patient,
                    doctor=doctor,
                    diagnosis='TBD',
                    treatment_plan='TBD'
                )
                billing_invoice.medical_record = medical_record
                billing_invoice.save(update_fields=['medical_record'])

            return redirect('patients:patient_admission_detail', admission_id=admission.id)

    else:
        form = PatientAdmissionForm()

    return render(request, 'patients/patient_admission_create.html', {
        'form': form
    })










@login_required
def patient_admission_list(request):
    form = CommonFilterForm(request.GET)
    admissions = PatientAdmission.objects.none()

    if request.method == 'GET':    
        if form.is_valid():
            entity_id = form.cleaned_data['entity_id']
            patient_name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            patient_id = form.cleaned_data['patient_id']

            admissions = (
                PatientAdmission.objects
                .select_related('patient', 'admitting_doctor', 'assigned_ward', 'assigned_bed')
                .order_by('-admission_date')
            )

            if entity_id:
                admissions = admissions.filter(admission_code__icontains=entity_id)
            if patient_name:
               admissions = admissions.filter(patient__name__icontains=patient_name)
            if phone_number:
                admissions = admissions.filter(patient__phone=phone_number)
            if email:
                admissions =admissions.filter(patient__email=email)
            if patient_id:
               admissions = admissions.filter(patient__patient_id__icontains=patient_id)

    datas = admissions
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'patients/patient_admission_list.html', {'form': form, 'page_obj': page_obj})



@login_required
def patient_admission_detail(request, admission_id): 
    admission = get_object_or_404(PatientAdmission, id=admission_id)
    assigned_bed = None
    assigned_ward = None
    assigned_room = None

    current_assignment = BedAssignmentHistory.objects.filter(
        patient=admission.patient,
        released_at__isnull=True
    ).first()

    if current_assignment:
        assigned_bed = current_assignment.bed
        assigned_room = current_assignment.bed.room
        assigned_ward = current_assignment.ward
    else:
        assigned_bed = None
        assigned_ward = None
        assigned_room = None

    print(assigned_ward,assigned_room,assigned_bed)

    return render(request, 'patients/patient_admission_details.html', {
        'admission': admission,
        'assigned_bed': assigned_bed,
        'assigned_room': assigned_room,
        'assigned_ward': assigned_ward
    })


@login_required
def patients_details(request):
    if request.method == "POST":
        data = json.loads(request.body)
        form = PatientForm(data)
        if form.is_valid():
            patient = form.save()  
            redirect_url = reverse('appointments:available_doctors') + f"?patient_id={patient.id}"
            return JsonResponse({"success": True, "redirect_url": redirect_url})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    form = PatientForm()
    return render(request, "patients/patient_details.html", {"form": form})







from django.forms import modelformset_factory
from medical_records.models import PrescribedMedicine

PrescriptionFormSet = modelformset_factory(
    PrescribedMedicine,
    form=PrescriptionForm,
    extra=1,
    can_delete=True,
)


@login_required
def doctor_consultation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)       
    medical_record = appointment.medical_record
    if request.user != appointment.doctor.user:
        messages.warning(request,'You are not assigned for this patient to consult')

    if request.method == 'POST':
        print('post/get=', request.method)
        medical_form = MedicalRecordForm(request.POST, request.FILES, instance=medical_record)
        prescription_formset = PrescriptionFormSet(request.POST, queryset=PrescribedMedicine.objects.none())
        lab_test_form = LabTestForm(request.POST)

        if medical_form.is_valid() and prescription_formset.is_valid() and lab_test_form.is_valid():           
            updated_record = medical_form.save(commit=False)
            updated_record.patient = appointment.patient
            updated_record.doctor = appointment.doctor
            updated_record.save()

            prescription = Prescription.objects.create(
                medical_record=updated_record,  # Use updated_record here!
                created_by=request.user,
                notes=request.POST.get("notes", ""),
                patient_type="OPD",
            )

            for form in prescription_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    prescribed_medicine = form.save(commit=False)
                    prescribed_medicine.prescription = prescription
                    prescribed_medicine.save()
                else:
                    print(form.errors)

            selected_lab_tests = request.POST.getlist('lab_tests')
            if selected_lab_tests:
                suggested_labtest = SuggestedLabTestRequest.objects.create(
                    patient_type=appointment.patient_type,
                    medical_record=updated_record,
		    appointment = appointment,
                    suggested_by=appointment.doctor,
                    status='Pending'
                )

                for test_id in selected_lab_tests:
                    try:
                        lab_test_catalog = LabTestCatalog.objects.get(id=test_id)
                        SuggestedLabTestItem.objects.create(
                            suggested_labtest=suggested_labtest,
                            lab_test=lab_test_catalog,
                            status='Pending'
                        )
                    except LabTestCatalog.DoesNotExist:
                        print(f"LabTestCatalog with ID {test_id} does not exist.")


            appointment.status = 'Prescription-Given'
            appointment.save(update_fields=['status'])

            messages.success(request, 'Prescription has been successfully created and is downloadable on the appointment list page')
            return redirect('appointments:appointment_list')
        else:
            for form in prescription_formset:
                print("Form errors:", form.errors)

            return render(request, 'patients/doctor_consultation.html', {
                'appointment': appointment,
                'medical_form': medical_form,
                'prescription_formset': prescription_formset,
                'lab_test_form': lab_test_form,
            })

    else:
        medical_form = MedicalRecordForm(instance=medical_record)
        prescription_formset = PrescriptionFormSet(queryset=PrescribedMedicine.objects.none())
        lab_test_form = LabTestForm()

    return render(request, 'patients/doctor_consultation.html', {
        'appointment': appointment,
        'medical_form': medical_form,
        'prescription_formset': prescription_formset,
        'lab_test_form': lab_test_form,
    })








from lab_tests.models import LabTestRequestItem
from billing.models import LabTestBill,MedicineBill,ConsultationBill,DoctorServiceRate,DoctorServiceLog

@login_required
def ipd_doctor_consultation(request, medical_record_id):
    medical_record = get_object_or_404(MedicalRecord, id=medical_record_id)  
    doctor = medical_record.doctor
    doctor_service_fee =0    
    doctor_service_rate = DoctorServiceRate.objects.filter(doctor=doctor,service_type="Consultation").first()
    if doctor_service_rate:
        doctor_service_fee = doctor_service_rate.rate

  
    if request.user != medical_record.doctor.user:
        messages.warning(request,'You are not assigned for this patient to consult')

    if request.method == 'POST':
        print('post/get=', request.method)       
        prescription_formset = PrescriptionFormSet(request.POST, queryset=PrescribedMedicine.objects.none())
        lab_test_form = LabTestForm(request.POST)

        if prescription_formset.is_valid() and lab_test_form.is_valid():   
            with transaction.atomic():   

                prescription = Prescription.objects.create(
                medical_record=medical_record,  # Use updated_record here!
                created_by=request.user,
                notes=request.POST.get("notes", ""),
                patient_type="IPD",
                )
                consultation_bill = ConsultationBill.objects.create(
                    user=request.user,
                    invoice=medical_record.billing_medical_record,
                    doctor=medical_record.doctor,
                    #appointment=medical_record.appointment if hasattr(medical_record, 'appointment') else None,
                    consultation_fee=doctor_service_fee,  # Assuming doctor has a fee field
                    patient_type='IPD',
                    consultation_type='Follow-Up',
                    status='Unpaid'
                )
                DoctorServiceLog.objects.create(
                    invoice=medical_record.billing_medical_record,
                    medical_record = medical_record,
                    doctor=doctor,
                    service_type='Consultation',
                    patient=medical_record.patient,
                    service_date=prescription.created_at,
                    service_fee = doctor_service_fee
                )

                for form in prescription_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        prescribed_medicine = form.save(commit=False)
                        prescribed_medicine.prescription = prescription
                        prescribed_medicine.save()

                        MedicineBill.objects.create(                            
                            invoice=medical_record.billing_medical_record,
                            medicine=prescribed_medicine.medication_name,                                                       
                            quantity=prescribed_medicine.quantity,
                            price_per_unit= prescribed_medicine.medication_name.base_unit_price or 0,                           
                            patient_type="IPD",
                            status="Unpaid"
                        )
                    else:
                        print(form.errors)


                selected_lab_tests = request.POST.getlist('lab_tests')
                if selected_lab_tests:
                    requested_labtest = LabTestRequest.objects.create(
                        patient_type=medical_record.billing_medical_record.patient_type,
                        medical_record=medical_record,
                        requested_by=medical_record.doctor,
                        status='Pending'
                    )

                    for test_id in selected_lab_tests:
                        try:
                            lab_test_catalog = LabTestCatalog.objects.get(id=test_id)
                            LabTestRequestItem.objects.create(
                                labtest_request=requested_labtest,
                                lab_test=lab_test_catalog,                           
                                notes='IPD prescription',
                                status='Pending'
                            )
                            LabTestBill.objects.create(                             
                                invoice=medical_record.billing_medical_record,
                                lab_test_catelogue=lab_test_catalog,
                                test_fee=lab_test_catalog.price,
                                patient_type="IPD",
                                status="Unpaid"
                            )
                        except LabTestCatalog.DoesNotExist:
                            print(f"LabTestCatalog with ID {test_id} does not exist.")         

                messages.success(request, 'Prescription has been successfully created and is downloadable')
                return redirect('appointments:appointment_list')
        else:
            for form in prescription_formset:
                print("Form errors:", form.errors)

            return render(request, 'patients/doctor_consultation.html', {              
                'prescription_formset': prescription_formset,
                'lab_test_form': lab_test_form,
                'medical_record': medical_record,
            })

    else:      
        prescription_formset = PrescriptionFormSet(queryset=PrescribedMedicine.objects.none())
        lab_test_form = LabTestForm()

    return render(request, 'patients/doctor_consultation.html', {         
        'prescription_formset': prescription_formset,
        'lab_test_form': lab_test_form,
        'medical_record': medical_record,
    })




def medical_record_prescriptions_view(request, record_id):
    medical_record = get_object_or_404(MedicalRecord, id=record_id)
    prescriptions = medical_record.prescriptions.select_related('created_by').prefetch_related('medicines')

    context = {
        'medical_record': medical_record,
        'prescriptions': prescriptions,
    }
    return render(request, 'patients/medical_record_prescriptions.html', context)









def draw_justified_paragraph(pdf, text, x, y, max_width=500, pdf_height=800, line_height=15):  
    styles = getSampleStyleSheet()
    justified_style = ParagraphStyle(
        "Justified",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=4, 
    )

    para = Paragraph(text, justified_style)
    w, h = para.wrap(max_width, pdf_height) 

    
    while h > y - 50: 
        available_space = y - 50
        split_text = text
        while True:
            para_temp = Paragraph(split_text, justified_style)
            _, temp_h = para_temp.wrap(max_width, pdf_height)
            if temp_h <= available_space:
                break
            split_text = split_text.rsplit(' ', 10)[0]  
 
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






from lab_tests.models import SuggestedLabTestRequest,SuggestedLabTestItem
from medical_records.models import PrescribedMedicine

def generate_prescription_pdf(request, medical_record_id):
    medical_record = MedicalRecord.objects.get(id=medical_record_id)
    prescriptions = PrescribedMedicine.objects.filter(prescription__medical_record=medical_record)
    prescriptions = PrescribedMedicine.objects.filter(prescription__medical_record=medical_record).order_by('-date_issued')

    appointment = medical_record.medical_record_appointments.first()

    lab_tests= []

    if appointment:
        try:
            suggested_lab_test = appointment.appointment_labtest
            lab_tests = suggested_lab_test.suggested_items.all()
        except SuggestedLabTestRequest.DoesNotExist:
            lab_tests = []
    else:
        lab_tests = []  
    
    age = medical_record.patient.calculate_age()
    dob_formatted = medical_record.patient.date_of_birth.strftime("%d-%b-%Y")
    gender = medical_record.patient.gender

    date_formatted = medical_record.date.strftime("%d-%b-%Y")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Prescription_{medical_record.patient.name}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y_position = height - 50  # Start position from the top
  

    # **Header: Hospital Logo & Details**
    logo_x, logo_y = 40, y_position - 40
    if medical_record.doctor.company.logo:
        logo_path = os.path.join(settings.MEDIA_ROOT, str(medical_record.doctor.company.logo))
        if os.path.exists(logo_path):
            pdf.drawImage(ImageReader(logo_path), logo_x, logo_y, width=80, height=80)
    
    details_x, details_y = logo_x, logo_y - 20

    email=medical_record.doctor.company.email
    phone=medical_record.doctor.phone
    address=medical_record.doctor.location.address if medical_record.doctor.location else medical_record.doctor.doctor_location
    web=medical_record.doctor.company.website

    # Company Information Section
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(details_x, details_y, str(medical_record.doctor.company))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(details_x, details_y - 15, f"Email: {email}||Phone:{phone}")
    pdf.drawString(details_x, details_y - 30, f"Address: {address}||web:{web}")
    

    y_position -= 150
    # Patient Information Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Patient Information")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y_position - 15, f"Name: {medical_record.patient.name}||Phone:{medical_record.patient.phone}")
    pdf.drawString(40, y_position - 30, f"DOB: {dob_formatted} || Age: {age} || Gender: {gender}")
    pdf.drawString(40, y_position - 45, f"UUID: {medical_record.patient.id}")

    # Doctor Information Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(370, y_position, "Doctor Information")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(370, y_position - 15, f"Dr. {medical_record.doctor.name} - {medical_record.doctor.specialization}")
    pdf.drawString(370, y_position - 30, f"Reg. No: {medical_record.doctor.medical_license_number}")
    pdf.drawString(370, y_position - 45, f"Date: {date_formatted}")

    y_position -= 100

    # **Diagnosis (Justified)**
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Diagnosis:")
    y_position -= 20   
    y_position = draw_justified_paragraph(pdf, medical_record.diagnosis or '', 40, y_position, max_width=530, pdf_height=height)
   
    y_position -= 20

    # **Treatment Plan (Justified)**
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Treatment Plan:")
    y_position -= 20    
    y_position = draw_justified_paragraph(pdf, medical_record.treatment_plan or '', 40, y_position, max_width=530, pdf_height=height)

    y_position -= 30

    # **Prescribed Medications Table**
    if prescriptions.exists():
        if y_position < 100:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y_position = height - 50

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y_position, "Prescribed Medications:")
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y_position, "Medicine Name")
        pdf.drawString(200, y_position, "Dosage")
        pdf.drawString(300, y_position, "Schedule")
        pdf.drawString(400, y_position, "Instructions")
        pdf.line(40, y_position - 5, 550, y_position - 5)
        y_position -= 15

        pdf.setFont("Helvetica", 10)
        for prescription in prescriptions:
            if y_position < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_position = height - 50
            pdf.drawString(40, y_position, prescription.medication_name.name)
            pdf.drawString(200, y_position, prescription.dosage if prescription.dosage else 'None')
            pdf.drawString(300, y_position, prescription.dosage_schedule)
            pdf.drawString(400, y_position, prescription.additional_instructions)
            y_position -= 15
         


      # **Lab Test Requests**
        y_position -= 15
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y_position, "Lab Test Requests:")
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y_position, "Test Type")
        pdf.drawString(200, y_position, "Test Name")
        pdf.drawString(400, y_position, "Status")
        pdf.line(40, y_position - 5, 550, y_position - 5)
        y_position -= 15

        pdf.setFont("Helvetica", 10)
        for lab_test in lab_tests:
            if y_position < 150:  
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_position = height - 50  # Reset position after page break

                # Re-add table headers after page break
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(40, y_position, "Test Type")
                pdf.drawString(200, y_position, "Test Name")
                pdf.drawString(400, y_position, "Status")
                pdf.line(40, y_position - 5, 550, y_position - 5)
                y_position -= 15  # Move below header

            pdf.drawString(40, y_position, lab_test.lab_test.test_type)
            pdf.drawString(200, y_position, lab_test.lab_test.test_name)
            pdf.drawString(400, y_position, lab_test.status)
            y_position -= 20  # Move to next line



    y_position -= 40
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(40, y_position, "Get well soon! Follow your doctor's advice.")
    y_position -= 40
    pdf.drawString(50,  y_position, "Doctor's Signature: ______________")
    y_position -= 20

    pdf.drawString(50,  y_position, f"{medical_record.doctor.name} - {medical_record.doctor.specialization}")
    y_position -= 20
    pdf.drawString(50,  y_position, str(medical_record.doctor.medical_license_number))
    y_position -= 20
    pdf.drawString(360, y_position+30 , "Scan for Digital Verification")
  
    
    # Generate QR Code
    qr_filename = "qr_code.png"
    generate_qr_code_prescription("https://xyzhospital.com/verify-prescription", qr_filename)
    qr_image = Image(qr_filename, 0.8*inch, 0.8*inch)
    qr_image.wrapOn(pdf, width, height)
    qr_image.drawOn(pdf,300, y_position)  # Adjust position if needed


    pdf.save()
    return response

@login_required
def download_prescription(request, medical_record_id):
    return generate_prescription_pdf(request, medical_record_id)


def generate_qr_code_prescription(data, filename):
    qr = qrcode.make(data)
    qr.save(filename)




def download_prescription(request, medical_record_id):
    return generate_prescription_pdf(request, medical_record_id)


def generate_qr_code_prescription(data, filename):
    qr = qrcode.make(data)
    qr.save(filename)








def generate_ipd_lab_test_pdf(request, lab_request_id):
    lab_request = get_object_or_404(LabTestRequest,id=lab_request_id)
    medical_record = lab_request.medical_record
    lab_tests = lab_request.test_items.all()
  
    
    age = medical_record.patient.calculate_age()
    dob_formatted = medical_record.patient.date_of_birth.strftime("%d-%b-%Y")
    gender = medical_record.patient.gender

    date_formatted = medical_record.date.strftime("%d-%b-%Y")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Prescription_{medical_record.patient.name}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y_position = height - 50  # Start position from the top
  

    # **Header: Hospital Logo & Details**
    logo_x, logo_y = 40, y_position - 40
    if medical_record.doctor.company.logo:
        logo_path = os.path.join(settings.MEDIA_ROOT, str(medical_record.doctor.company.logo))
        if os.path.exists(logo_path):
            pdf.drawImage(ImageReader(logo_path), logo_x, logo_y, width=80, height=80)
    
    details_x, details_y = logo_x, logo_y - 20

    email=medical_record.doctor.company.email
    phone=medical_record.doctor.phone
    address=medical_record.doctor.location.address if medical_record.doctor.location else medical_record.doctor.doctor_location
    web=medical_record.doctor.company.website

    # Company Information Section
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(details_x, details_y, str(medical_record.doctor.company))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(details_x, details_y - 15, f"Email: {email}||Phone:{phone}")
    pdf.drawString(details_x, details_y - 30, f"Address: {address}||web:{web}")
    

    y_position -= 150
    # Patient Information Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Patient Information")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y_position - 15, f"Name: {medical_record.patient.name}||Phone:{medical_record.patient.phone}")
    pdf.drawString(40, y_position - 30, f"DOB: {dob_formatted} || Age: {age} || Gender: {gender}")
    pdf.drawString(40, y_position - 45, f"UUID: {medical_record.patient.id}")

    # Doctor Information Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(370, y_position, "Doctor Information")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(370, y_position - 15, f"Dr. {medical_record.doctor.name} - {medical_record.doctor.specialization}")
    pdf.drawString(370, y_position - 30, f"Reg. No: {medical_record.doctor.medical_license_number}")
    pdf.drawString(370, y_position - 45, f"Date: {date_formatted}")

    y_position -= 100

    # **Diagnosis (Justified)**
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Diagnosis:")
    y_position -= 20   
    if medical_record.progress_notes.exists():  
        y_position = draw_justified_paragraph(pdf, medical_record.progress_notes.first().diagnosis or '', 40, y_position, max_width=530, pdf_height=height)
    else:
        y_position = draw_justified_paragraph(pdf, medical_record.diagnosis or '', 40, y_position, max_width=530, pdf_height=height)

    y_position -= 20

    # **Treatment Plan (Justified)**
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Treatment Plan:")
    y_position -= 20    
    if medical_record.progress_notes.exists(): 
        y_position = draw_justified_paragraph(pdf, medical_record.progress_notes.first().treatment_plan or '', 40, y_position, max_width=530, pdf_height=height)
    else:
        y_position = draw_justified_paragraph(pdf, medical_record.treatment_plan or '', 40, y_position, max_width=530, pdf_height=height)

    y_position -= 30

    # **Prescribed Medications Table**
    if lab_tests.exists():
        if y_position < 100:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y_position = height - 50

        pdf.setFont("Helvetica-Bold", 12)
      


      # **Lab Test Requests**
        y_position -= 15
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y_position, "Lab Test Requests:")
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y_position, "Test Type")
        pdf.drawString(200, y_position, "Test Name")
        pdf.drawString(400, y_position, "Status")
        pdf.line(40, y_position - 5, 550, y_position - 5)
        y_position -= 15

        pdf.setFont("Helvetica", 10)
        for lab_test in lab_tests:
            if y_position < 150:  
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_position = height - 50  # Reset position after page break

                # Re-add table headers after page break
                pdf.setFont("Helvetica-Bold", 10)
                pdf.drawString(40, y_position, "Test Type")
                pdf.drawString(200, y_position, "Test Name")
                pdf.drawString(400, y_position, "Status")
                pdf.line(40, y_position - 5, 550, y_position - 5)
                y_position -= 15  # Move below header

            pdf.drawString(40, y_position, lab_test.lab_test.test_type)
            pdf.drawString(200, y_position, lab_test.lab_test.test_name)
            pdf.drawString(400, y_position, lab_test.status)
            y_position -= 20  # Move to next line



    y_position -= 40
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(40, y_position, "Get well soon! Follow your doctor's advice.")
    y_position -= 40
    pdf.drawString(50,  y_position, "Doctor's Signature: ______________")
    y_position -= 20

    pdf.drawString(50,  y_position, f"{medical_record.doctor.name} - {medical_record.doctor.specialization}")
    y_position -= 20
    pdf.drawString(50,  y_position, str(medical_record.doctor.medical_license_number))
    y_position -= 20
    pdf.drawString(360, y_position+30 , "Scan for Digital Verification")
  
    
    # Generate QR Code
    qr_filename = "qr_code.png"
    generate_qr_code_prescription("https://xyzhospital.com/verify-prescription", qr_filename)
    qr_image = Image(qr_filename, 0.8*inch, 0.8*inch)
    qr_image.wrapOn(pdf, width, height)
    qr_image.drawOn(pdf,300, y_position)  # Adjust position if needed


    pdf.save()
    return response

@login_required
def download_ipd_lab_test(request, lab_request_id):
    return generate_ipd_lab_test_pdf(request, lab_request_id)




from lab_tests.models import SuggestedLabTestRequest,SuggestedLabTestItem
from medical_records.models import PrescribedMedicine

def generate_ipd_prescription_pdf(request, prescription_id):   
    prescription = get_object_or_404(Prescription,id=prescription_id)
    medical_record = prescription.medical_record  
      
    age = medical_record.patient.calculate_age()
    dob_formatted = medical_record.patient.date_of_birth.strftime("%d-%b-%Y")
    gender = medical_record.patient.gender

    date_formatted = medical_record.date.strftime("%d-%b-%Y")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Prescription_{medical_record.patient.name}.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y_position = height - 50  # Start position from the top
  

    # **Header: Hospital Logo & Details**
    logo_x, logo_y = 40, y_position - 40
    if medical_record.doctor.company.logo:
        logo_path = os.path.join(settings.MEDIA_ROOT, str(medical_record.doctor.company.logo))
        if os.path.exists(logo_path):
            pdf.drawImage(ImageReader(logo_path), logo_x, logo_y, width=80, height=80)
    
    details_x, details_y = logo_x, logo_y - 20

    email=medical_record.doctor.company.email
    phone=medical_record.doctor.phone
    address=medical_record.doctor.location.address if medical_record.doctor.location else medical_record.doctor.doctor_location
    web=medical_record.doctor.company.website

    # Company Information Section
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(details_x, details_y, str(medical_record.doctor.company))
    pdf.setFont("Helvetica", 10)
    pdf.drawString(details_x, details_y - 15, f"Email: {email}||Phone:{phone}")
    pdf.drawString(details_x, details_y - 30, f"Address: {address}||web:{web}")
    

    y_position -= 150
    # Patient Information Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Patient Information")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y_position - 15, f"Name: {medical_record.patient.name}||Phone:{medical_record.patient.phone}")
    pdf.drawString(40, y_position - 30, f"DOB: {dob_formatted} || Age: {age} || Gender: {gender}")
    pdf.drawString(40, y_position - 45, f"UUID: {medical_record.patient.id}")

    # Doctor Information Section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(370, y_position, "Doctor Information")

    pdf.setFont("Helvetica", 10)
    pdf.drawString(370, y_position - 15, f"Dr. {medical_record.doctor.name} - {medical_record.doctor.specialization}")
    pdf.drawString(370, y_position - 30, f"Reg. No: {medical_record.doctor.medical_license_number}")
    pdf.drawString(370, y_position - 45, f"Date: {date_formatted}")

    y_position -= 100

    # **Diagnosis (Justified)**
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Diagnosis:")
    y_position -= 20   
    if medical_record.progress_notes.exists():       
        y_position = draw_justified_paragraph(pdf, medical_record.progress_notes.first().diagnosis or '', 40, y_position, max_width=530, pdf_height=height)
    else:
        y_position = draw_justified_paragraph(pdf, medical_record.diagnosis or '', 40, y_position, max_width=530, pdf_height=height)

    y_position -= 20

    # **Treatment Plan (Justified)**
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y_position, "Treatment Plan:")
    y_position -= 20    
    if medical_record.progress_notes.exists():   
        y_position = draw_justified_paragraph(pdf, medical_record.progress_notes.first().treatment_plan or '', 40, y_position, max_width=530, pdf_height=height)
    else:
        y_position = draw_justified_paragraph(pdf, medical_record.treatment_plan or '', 40, y_position, max_width=530, pdf_height=height)

    y_position -= 30

    # **Prescribed Medications Table**
    if prescription.medicines.exists():
        if y_position < 100:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y_position = height - 50

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y_position, "Prescribed Medications:")
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y_position, "Medicine Name")
        pdf.drawString(200, y_position, "Dosage")
        pdf.drawString(300, y_position, "Schedule")
        pdf.drawString(400, y_position, "Instructions")
        pdf.line(40, y_position - 5, 550, y_position - 5)
        y_position -= 15

        pdf.setFont("Helvetica", 10)
        for prescription in prescription.medicines.all():
            if y_position < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_position = height - 50
            pdf.drawString(40, y_position, prescription.medication_name.name)
            pdf.drawString(200, y_position, prescription.dosage if prescription.dosage else 'None')
            pdf.drawString(300, y_position, prescription.dosage_schedule)
            pdf.drawString(400, y_position, prescription.additional_instructions)
            y_position -= 15
          

    y_position -= 40
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(40, y_position, "Get well soon! Follow your doctor's advice.")
    y_position -= 40
    pdf.drawString(50,  y_position, "Doctor's Signature: ______________")
    y_position -= 20

    pdf.drawString(50,  y_position, f"{medical_record.doctor.name} - {medical_record.doctor.specialization}")
    y_position -= 20
    pdf.drawString(50,  y_position, str(medical_record.doctor.medical_license_number))
    y_position -= 20
    pdf.drawString(360, y_position+30 , "Scan for Digital Verification")
  
    
    # Generate QR Code
    qr_filename = "qr_code.png"
    generate_qr_code_prescription("https://xyzhospital.com/verify-prescription", qr_filename)
    qr_image = Image(qr_filename, 0.8*inch, 0.8*inch)
    qr_image.wrapOn(pdf, width, height)
    qr_image.drawOn(pdf,300, y_position)  # Adjust position if needed


    pdf.save()
    return response




@login_required
def download_ipd_prescription(request,prescription_id):
    return generate_ipd_prescription_pdf(request,prescription_id)






@login_required
def change_bed(request, admission_id):
    admission = get_object_or_404(PatientAdmission, id=admission_id)
    invoice = admission.billing_admission

    if request.method == 'POST':
        form = BedAssignmentForm(request.POST)
        if form.is_valid():
            new_bed = form.cleaned_data['bed']
            new_room = form.cleaned_data['room']
            now = tz_now()

            with transaction.atomic():
                last_assignment = BedAssignmentHistory.objects.filter(
                    patient=admission.patient,
                    patient_admission=admission,
                    released_at__isnull=True
                ).latest('assigned_at')

                # Mark last assignment as released
                last_assignment.released_at = now
                last_assignment.save()

                old_bed = last_assignment.bed
                old_room = old_bed.room
                old_ward = old_bed.ward

                # Free old bed
                old_bed.is_occupied = False
                old_bed.save(update_fields=['is_occupied'])

                # Free room if all beds are free
                if not old_room.room_beds.filter(is_occupied=True).exists():
                    old_room.is_occupied = False
                    old_room.save(update_fields=['is_occupied'])

                # Free ward if all rooms are free
                if not old_ward.ward_rooms.filter(room_beds__is_occupied=True).exists():
                    old_ward.is_occupied = False
                    old_ward.save(update_fields=['is_occupied'])

                # Update old WardBill if exists
                old_bill = WardBill.objects.filter(
                    patient_admission=admission,
                    bed=old_bed,
                    released_at__isnull=True
                ).first()

                if old_bill:
                    assigned_dt = last_assignment.assigned_at
                    released_dt = last_assignment.released_at

                    if is_naive(assigned_dt):
                        assigned_dt = make_aware(assigned_dt)
                    if is_naive(released_dt):
                        released_dt = make_aware(released_dt)

                    num_days = calculate_billed_days(assigned_dt, released_dt)
                    daily_rate = old_bed.daily_charge
                    total_bill = num_days * daily_rate                  
                    old_bill.total_bill = total_bill
                    old_bill.assigned_at = assigned_dt
                    old_bill.released_at = released_dt    
                    old_bill.days_stayed = num_days          
                    old_bill.save()

                # ALWAYS handle new bed assignment
                new_bed.is_occupied = True
                new_bed.save(update_fields=['is_occupied'])

                update_room_occupancy(new_bed.room)
                update_ward_occupancy(new_bed.ward)

                # Create new BedAssignmentHistory
                BedAssignmentHistory.objects.create(
                    ward=new_bed.ward,
                    room=new_bed.room,
                    bed=new_bed,
                    patient=admission.patient,
                    assigned_at=now,
                    patient_admission=admission,
                )

                # Create new WardBill
                WardBill.objects.create(
                    invoice=invoice,
                    patient_admission=admission,
                    bed=new_bed,
                    room=new_bed.room,
                    ward=new_bed.ward,
                    charge_per_day=new_bed.daily_charge,
                    assigned_at=now,
                    total_bill=0.0,
                )
                print(f"Creating WardBill: bed={new_bed}, room={new_bed.room}, ward={new_bed.ward}")

            # Update admission info
            admission.bed_assignment_date = now
            admission.assigned_bed = new_bed
            admission.assigned_room = new_room
            admission.assigned_ward = new_bed.ward
            admission.save(update_fields=['bed_assignment_date', 'assigned_bed', 'assigned_room', 'assigned_ward'])

            # Recalculate invoice
            invoice.update_totals()
            invoice.save()

            return redirect('patients:patient_admission_detail', admission_id=admission.id)

    else:
        form = BedAssignmentForm()

    return render(request, 'patients/assign_bed_to_patient.html', {
        'form': form,
        'admission': admission
    })







def calculate_discharged_billed_days(assigned_at, released_at):
    if not assigned_at or not released_at:
        return 0

    assigned_date = assigned_at.date()
    released_date = released_at.date()
    delta_days = (released_date - assigned_date).days + 1
    return max(delta_days, 1)



@login_required
def discharge_patient(request, admission_id):
    admission = get_object_or_404(PatientAdmission, id=admission_id)

    if request.method == 'POST':
        invoice = admission.billing_admission

        with transaction.atomic():
            # Close current bed assignment
            last_assignment = BedAssignmentHistory.objects.filter(
                patient=admission.patient,
                released_at__isnull=True
            ).order_by('-assigned_at').first()

            release_time = tz_now()
            last_assignment.released_at = release_time
            last_assignment.save()

            old_bed = last_assignment.bed
            old_room = old_bed.room
            old_ward = old_bed.ward

            old_bed.is_occupied = False
            old_bed.save(update_fields=['is_occupied'])

            if not old_room.room_beds.filter(is_occupied=True).exists():
                old_room.is_occupied = False
                old_room.save(update_fields=['is_occupied'])

            if not old_ward.ward_rooms.filter(room_beds__is_occupied=True).exists():
                old_ward.is_occupied = False
                old_ward.save(update_fields=['is_occupied'])

            ward_bill = WardBill.objects.filter(
                patient_admission=admission,
                bed=old_bed,
                released_at__isnull=True
            ).first()

            if ward_bill:
                assigned_dt = last_assignment.assigned_at
                released_dt = last_assignment.released_at

                if is_naive(assigned_dt):
                    assigned_dt = make_aware(assigned_dt)
                if is_naive(released_dt):
                    released_dt = make_aware(released_dt)

                num_days = calculate_discharged_billed_days(assigned_dt, released_dt)
                total_bill = num_days * old_bed.daily_charge

                ward_bill.assigned_at = assigned_dt
                ward_bill.released_at = released_dt
                ward_bill.days_stayed = num_days
                ward_bill.total_bill = total_bill
                ward_bill.save()

            admission.status = 'Discharged'
            admission.discharge_date = release_time
            admission.save(update_fields=['status', 'discharge_date'])

            invoice.update_total_wardbill()
            invoice.update_totals()
            invoice.save()

        return redirect('patients:create_discharge_report', admission_id=admission.id)

    # GET request — show confirmation page
    return render(request, 'patients/confirm_discharge.html', {
        'admission': admission
    })



@login_required
def create_discharge_report(request, admission_id):
    admission = get_object_or_404(PatientAdmission, id=admission_id)

    # Check if discharge report already exists
    discharge_report, created = DischargeReport.objects.get_or_create(
        patient_admission=admission,
        defaults={
            'doctor': admission.admitting_doctor,
            'summary': '',  # or some default text
        }
    )

    form = DischargeReportForm(request.POST or None, instance=discharge_report)

    if form.is_valid():
        discharge_report = form.save(commit=False)
        discharge_report.doctor = admission.admitting_doctor  # ensure doctor is set/updated
        discharge_report.save()

        admission.discharge_date = timezone.now()
        admission.status = 'Discharged'
        admission.save()

        open_hist = BedAssignmentHistory.objects.filter(
            patient=admission.patient,
            released_at__isnull=True
        ).first()
        if open_hist:
            open_hist.released_at = timezone.now()
            open_hist.save()
            open_hist.bed.is_occupied = False
            open_hist.bed.save(update_fields=['is_occupied'])

        return redirect('patients:generate_discharge_pdf', discharge_report.id)

    return render(request, 'patients/create_discharge_report.html', {'form': form, 'admission': admission})



def generate_qr_code_discharge_report(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return buffer






@login_required
def generate_discharge_pdf(request, discharge_report_id):
    report = get_object_or_404(DischargeReport, id=discharge_report_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=.5*inch,
        leftMargin=.5*inch,
        topMargin=.1*inch,
        bottomMargin=.3*inch
    )


    styles = getSampleStyleSheet()

    header_style  = styles['Heading3']
    address_style = styles['Normal']
 
    logo = Image(report.doctor.company.logo, width=.8*inch, height=.8*inch)
    name = Paragraph("<b>Hospital Name</b>", header_style)

    logo_name_table = Table(
        [[logo],
        [name]],
        colWidths=[1.2*inch], 
        rowHeights=[.8*inch, .4*inch]  # Y
    )
    logo_name_table.setStyle(TableStyle([     
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),   
    ('BOTTOMPADDING', (0, 0), (0, 0), 2), 
    ('TOPPADDING', (0, 1), (0, 1), 2),  
    ('LEFTPADDING', (0, 0), (0, 1), 0),
    ('RIGHTPADDING', (0, 0), (0, 1), 0),
    ]))

    hospital_address = (
        "123 Main St, City, Country<br/>"
        "Phone: +123456789<br/>"
        "Email: info@hospital.com"
    )
    address_para = Paragraph(hospital_address, address_style)

    header_table = Table(
        [[ logo_name_table, address_para ]],
        colWidths=[9*inch, 5.5*inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',  (0,0), (0,0), 'CENTER'),
        ('ALIGN',  (1,0), (1,0), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING',    (0,0), (-1,-1), 12),
        # no borders
    ]))


    h1 = styles['Heading1']
    h1.alignment = TA_CENTER

    h2 = styles['Heading2']
    h2.alignment = TA_LEFT

    normal = styles['BodyText']
    normal.alignment = TA_JUSTIFY
    normal.fontSize = 11
    normal.leading = 14  


    italic = ParagraphStyle(
        'Italic',
        parent=styles['BodyText'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER
    )

    story = []
    story.append(header_table)

 
    story.append(Paragraph("Patient Discharge Summary", h1))
    story.append(Spacer(1, 0.25*inch))

    compact = ParagraphStyle(
    "Compact",
    parent=styles["BodyText"],
    fontName   = "Helvetica",
    fontSize   = 11,
    leading    = 12,  
    spaceBefore= 0,
    spaceAfter = 0,
)

    story.append(Paragraph("Patient Information", h2))
    story.append(Paragraph(f"<b>Name:</b> {report.patient_admission.patient.name}", compact))
    story.append(Paragraph(f"<b>Doctor:</b> {report.doctor.name if report.doctor else 'N/A'}", compact))
    story.append(Paragraph(f"<b>Admission Date:</b> {report.patient_admission.admission_date:%d %b, %Y}", compact))
    story.append(Paragraph(f"<b>Discharge Date:</b> {report.patient_admission.discharge_date:%d %b, %Y}", compact))
    
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Medical Information", h2))
    if report.reason_for_admission:
        story.append(Paragraph(f"<b>Reason for Admission:</b> {report.reason_for_admission}", normal))
    if report.diagnosis:
        story.append(Paragraph(f"<b>Diagnosis:</b> {report.diagnosis}", normal))
    if report.investigations :
        story.append(Paragraph(f"<b>Investigations :</b> {report.investigations }", normal))
    if report.treatment_given:
        story.append(Paragraph(f"<b>Treatment Given:</b> {report.treatment_given}", normal))
    if report.summary:
        story.append(Paragraph(f"<b>Summary:</b> {report.summary}", normal))

    if report.condition_at_discharge:
        story.append(Paragraph(f"<b> Condition at discharge:</b> {report.condition_at_discharge}", normal))
    if report.follow_up_instructions:
        story.append(Paragraph(f"<b> Follow up instructions:</b> {report.follow_up_instructions}", normal))
        story.append(Spacer(1, 0.2*inch))

    if report.follow_up_date:
        story.append(Paragraph("follow up date", h2))
        story.append(Paragraph(report.follow_up_date.strftime('%B %d, %Y'), normal))
        story.append(Spacer(1, 0.2*inch))
    if report.additional_notes:
        story.append(Paragraph("Additiona notes", h2))
        story.append(Paragraph(report.additional_notes, normal))
        story.append(Spacer(1, 0.2*inch))
   

    qr_data = f"Discharge Report for {report.patient_admission.patient.name}"
    qr_buf  = generate_qr_code_discharge_report(qr_data)
    qr_img  = Image(qr_buf, width=inch, height=inch)

    sig_para = Paragraph("Authorized Signature<br/><br/>......................", italic)
    footer   = Paragraph("Generated by Hospital Management System", italic)

    row = [qr_img, sig_para, footer]
    table = Table([row], colWidths=[1.5*inch, 2.5*inch, 2.5*inch])

    table.setStyle(TableStyle([
        ('VALIGN',    (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',     (0,0), (-1,-1), 'CENTER'),
        ('INNERGRID', (0,0), (-1,-1), 0, colors.white),
        ('BOX',       (0,0), (-1,-1), 0, colors.white),
    ]))

    story.append(Spacer(1, 0.5*inch))
    story.append(table)

    header_block = KeepTogether(story)
    block_data = [header_block]

    doc.build(block_data)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="discharge_report_{discharge_report_id}.pdf"'
    return response



