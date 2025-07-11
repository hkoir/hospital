
from datetime import datetime, time, timedelta
from django.shortcuts import render, get_object_or_404,redirect
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.utils.timezone import make_aware
from django.db.models import Count
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
import io
import base64
from io import BytesIO
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from num2words import num2words
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reportlab.lib.pagesizes import LETTER,A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
import qrcode
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,Image,KeepTogether
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from patients.models import DischargeReport
from reportlab.platypus import PageBreak
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction


from billing.models import BillingInvoice
from billing.forms import CommonFilterForm
from lab_tests.models import LabTestResultOrder
from core.forms import NoticeForm
from messaging.models import Notification
from core.models import Doctor,Specialization,Notice,Location
from patients.models import Patient,PatientAdmission
from medical_records.models import MedicalRecord,Prescription
from appointments.models import AppointmentSlot,Appointment



@login_required
def visitor_landing_page(request):
    notifications = Notification.objects.all()
    for noti in notifications:
        print(noti.is_read,f'user={request.user}')
        print(f'patinet={noti.patient}')
    return render(request,'visitors/visitor_landing_page.html')




@login_required
def view_notices(request):
    notices = Notice.objects.all().order_by('-created_at')
    form = NoticeForm()
    return render(request, 'visitors/view_notices.html', {'notices': notices, 'form': form})




@login_required
def available_doctors(request):
    appointments = Appointment.objects.select_related("patient", "timeslot").all()
    query = request.GET.get("query", "").strip()
    specialization_filter = request.GET.get("specialization", "").strip()
    doctors = Doctor.objects.all()
    if query:
        doctors = doctors.filter(name__icontains=query)
    
    if specialization_filter:
        doctors = doctors.filter(specialization__name__icontains=specialization_filter)  # ✅ Correct


    categorized_doctors = {}
    for doctor in doctors:
        if doctor.specialization not in categorized_doctors:
            categorized_doctors[doctor.specialization] = []
        categorized_doctors[doctor.specialization].append(doctor)

    return render(request, "visitors/available_doctors.html", {
        "categorized_doctors": categorized_doctors,
        "query": query,
        "specialization_filter": specialization_filter,
        'appointments': appointments
    })



def get_timeslots(request):
    doctor_id = request.GET.get("doctor_id")
    date = request.GET.get("date")
    slots = AppointmentSlot.objects.filter(doctor_id=doctor_id, date=date)

    slots_list = [
        {
            "id": slot.id,  
            "start_time": str(slot.start_time),
            "end_time": str(slot.end_time),
            "is_booked": slot.is_booked,  # Include booking status
        }
        for slot in slots
    ]

    return JsonResponse({"slots": slots_list})




def view_available_slots(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    date = request.GET.get('date')

    slots = []
    if date:
        # Filter or generate slots for that doctor on that date
        slots = AppointmentSlot.objects.filter(doctor=doctor, date=date)

    return render(request, 'visitors/available_slots.html', {
        'doctor': doctor,
        'slots': slots,
        'selected_date': date,
    })





@csrf_exempt
@login_required
def book_slot(request):
    if request.method == "POST":
        with transaction.atomic():
            try:
                data = json.loads(request.body)
                slot_id = data.get("slot_id")
                doctor_id = data.get("doctor_id")  
                name = data.get("name")
                email = data.get("email")
                phone = data.get("phone")
                date_of_birth = data.get("date_of_birth")
                address = data.get("address")
                medical_history = data.get("medical_history")
                gender = data.get("gender")

                if not all([slot_id, doctor_id, name, email, phone]):
                    return JsonResponse({"success": False, "error": "All fields are required."})       
                patient, created = Patient.objects.get_or_create(
                    name=name,
                    phone=phone,  
                    date_of_birth = date_of_birth,         
                    defaults={
                        'email':email,                     
                        'gender': gender,
                        'address': address,
                        'medical_history': medical_history,
                        'patient_photo': photo,
                        'user': request.user,

                    }
                )

                if not created:
                    message = f"Welcome back, {patient.name}! Your previous details have been used for this booking."
                else:
                    message = f"Thank you {patient.name}, your appointment is successfully booked."



                slot = AppointmentSlot.objects.get(id=slot_id, is_booked=False)
                doctor = Doctor.objects.get(id=doctor_id)               

                appointment = Appointment.objects.create(
                    timeslot=slot,
                    patient=patient,
                    doctor=doctor,      
                    user=request.user,
                    patient_type = 'OPD'      
                )

                slot.is_booked = True
                slot.save()
                return JsonResponse({
                    "success": True,
                    "message": f"{message} Appointment with Dr.{doctor.name} on {slot.date} from {slot.start_time} to {slot.end_time} has been confirmed."
                })
                
            except AppointmentSlot.DoesNotExist:
                return JsonResponse({"success": False, "error": "Slot is already booked or does not exist."})
            except Doctor.DoesNotExist:
                return JsonResponse({"success": False, "error": "Doctor does not exist."})
            except Exception as e:
                print(f"Error: {str(e)}")  
                return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


@csrf_exempt
@login_required
def book_slot2(request):
    if request.method == "POST":
        with transaction.atomic():
            try:
                data = json.loads(request.body)
                slot_id = data.get("slot_id")
                doctor_id = data.get("doctor_id")  
                name = data.get("name")
                email = data.get("email")
                phone = data.get("phone")
                date_of_birth = data.get("date_of_birth")
                address = data.get("address")
                medical_history = data.get("medical_history")
                gender = data.get("gender")

                if not all([slot_id, doctor_id, name, email, phone]):
                    return JsonResponse({"success": False, "error": "All fields are required."})       

                patient, created = Patient.objects.get_or_create(
                    user=request.user,                   
                    defaults={
                        "email": email,
                        "name": name, 
                        "phone": phone,
                        'date_of_birth':date_of_birth,
                        'address':address,
                        'medical_history':medical_history,
                        'gender':gender,
                        'user':request.user
                        }
                )


                if not created:
                    patient.name = name
                    patient.phone = phone
                    patient.save()

                slot = AppointmentSlot.objects.get(id=slot_id, is_booked=False)
                doctor = Doctor.objects.get(id=doctor_id)               

                appointment = Appointment.objects.create(
                    timeslot=slot,
                    patient=patient,
                    doctor=doctor,      
                    user=request.user          
                )

                slot.is_booked = True
                slot.save()
                return JsonResponse({
                    "success": True,
                    "message": f"Your appointment with Dr.{doctor.name} on {slot.date} from {slot.start_time} to {slot.end_time} has been booked successfully."
                })
                                
            except AppointmentSlot.DoesNotExist:
                return JsonResponse({"success": False, "error": "Slot is already booked or does not exist."})
            except Doctor.DoesNotExist:
                return JsonResponse({"success": False, "error": "Doctor does not exist."})
            except Exception as e:
                print(f"Error: {str(e)}")  
                return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})




@login_required
def specialization_detail(request, specialization_id):
    appointments = Appointment.objects.select_related("patient", "timeslot").all()
    specialization = get_object_or_404(Specialization, id=specialization_id)   
    specializations = Specialization.objects.all()


    query = request.GET.get("query", "").strip() 
    doctors = specialization.specialized_doctors.all()  

    if query:
        doctors = doctors.filter(name__icontains=query)  

    return render(request, "visitors/specialization_details.html", {
        "specialization": specialization,
        "doctors": doctors,
        "query": query, 
        'appointments':  appointments,
        'specializations':specializations
        
    })



def get_doctors_by_specialization(request):
    specialization = request.GET.get("specialization", None)

    if specialization and specialization != "all":
        doctors = Doctor.objects.filter(specialization=specialization)
    else:
        doctors = Doctor.objects.all()

    doctor_data = [
        {
            "id": doctor.id,
            "name": doctor.name,
            "specialization": doctor.specialization,
            "experience_years": doctor.experience_years,
            "employee_photo_ID": doctor.employee_photo_ID.url if doctor.employee_photo_ID else "",
        }
        for doctor in doctors
    ]
    return JsonResponse({"doctors": doctor_data})



@login_required
def appointment_list(request):
    doctors = Doctor.objects.all()
    patients = Patient.objects.all()
    doctor_appointment_counts = []
    today = timezone.now().date()

    # Base queryset
    appointments = Appointment.objects.filter(user=request.user)

    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    doctor_id = request.GET.get('doctor')

    if start_date and end_date:
        appointments = appointments.filter(date__range=[start_date, end_date])

    if doctor_id:
        appointments = appointments.filter(doctor=doctor_id)

    # Enhance each appointment with related data
    for appointment in appointments:
        # Get medical record for appointment
        medical_record = MedicalRecord.objects.filter(
            doctor=appointment.doctor,
            patient=appointment.patient
        ).first()
        
        # Attach medical record as a temporary attribute
        appointment.medical_record_obj = medical_record

        # If medical record exists, fetch prescriptions
        if medical_record:
            appointment.prescriptions = medical_record.prescriptions.all()
            appointment.first_prescription = medical_record.prescriptions.first()
        else:
            appointment.prescriptions = []
            appointment.first_prescription = None

    return render(request, "visitors/appointment_list.html", {
        "appointments": appointments,
        "doctor_appointment_counts": doctor_appointment_counts,
        "today": today,
        "doctors": doctors,
        "patients": patients,
    })






@csrf_exempt
@login_required
def cancel_appointment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            appointment_id = data.get("appointment_id")

            if not appointment_id:
                return JsonResponse({"success": False, "error": "Appointment ID is required."})

            appointment = Appointment.objects.get(id=appointment_id)
            slot = appointment.timeslot 

            slot.is_booked = False
            slot.save()
            appointment.status = 'Cancelled'
            appointment.save()
            return JsonResponse({"success": True, "message": "Appointment cancelled successfully!"})
        except Appointment.DoesNotExist:
            return JsonResponse({"success": False, "error": "Appointment does not exist."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})





@login_required
def patient_admission_list(request):
    admissions = (
        PatientAdmission.objects
        .select_related('patient', 'admitting_doctor', 'assigned_ward', 'assigned_bed')
        .order_by('-admission_date')
    )

    if not request.user.is_superuser:  
        admissions = admissions.filter(patient__user=request.user)
 
    patient_id = request.GET.get('patient')
    if patient_id:
        admissions = admissions.filter(patient_id=patient_id)

    paginator = Paginator(admissions, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'visitors/patient_admission_list.html', {'page_obj': page_obj})





@login_required
def ipd_invoice_list(request):
    #invoices = BillingInvoice.objects.none()
    #if not request.user.is_superuser:  
    invoices = BillingInvoice.objects.filter(patient__user=request.user)  

    datas = invoices
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'visitors/ipd_invoice_list.html', {'page_obj': page_obj})


@login_required
def opd_invoice_list(request):
    invoices = BillingInvoice.objects.none()
    if not request.user.is_superuser:  
        invoices = BillingInvoice.objects.filter(patient__user=request.user,invoice_type='OPD')  

    datas = invoices
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    datas = invoices
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'visitors/opd_invoice_list.html', {'page_obj': page_obj})




from django.utils.timezone import now
from decimal import Decimal
from datetime import datetime, date, timedelta,time

def calculate_billed_days(assigned_at, released_at):
    if not assigned_at or not released_at:
        return 0

    same_day = assigned_at.date() == released_at.date()    
    if same_day:
        return 1   
    days = (released_at.date() - assigned_at.date()).days
    if released_at.time() > time(12, 0):
        days += 1  
    return days



def calculate_instant_wardbill(admission):    
    current_time = now()
    latest_bed_history = admission.patient.patient_bed_histories.filter(
        released_at__isnull=True
    ).first()

    total_running_bill= Decimal('0.00')
    bed = None
    assigned_at = None
    days_stayed = 0

    if latest_bed_history:
        bed = latest_bed_history.bed
        assigned_at = latest_bed_history.assigned_at
        daily_rate = bed.daily_charge if bed and bed.daily_charge else 0
        days_stayed = calculate_billed_days(assigned_at, current_time)
        total_running_bill = round(Decimal(days_stayed * daily_rate), 2)      
      
    return total_running_bill




@login_required
def finalize_invoice(request, invoice_id):
    invoice = BillingInvoice.objects.get(id=invoice_id)
    qr_code = generate_invoice_qr(invoice)
 

    hospital = Location.objects.first()
    triger_total_calculation = invoice.update_total_wardbill()

    consultation_subtotal = invoice.consultation_bills.aggregate(
        total=Sum('consultation_fee')
    )['total'] or 0

    lab_subtotal = invoice.lab_test_bills.aggregate(
        total=Sum('test_fee')
    )['total'] or 0

    medicine_subtotal = invoice.medicine_bills.aggregate(
        total=Sum(ExpressionWrapper(
            F('quantity') * F('price_per_unit'),
            output_field=DecimalField()
        ))
    )['total'] or 0

    ward_subtotal = invoice.ward_bills.aggregate(
            total=Sum('total_bill')
        )['total'] or 0

    admission = None
    ward_running_bill = 0
    grand_total_ward_bill = 0

    if invoice.invoice_type == 'IPD' and invoice.admission:
        admission = invoice.admission  # directly from the invoice FK
        ward_running_bill = calculate_instant_wardbill(admission)
        grand_total_ward_bill = ward_running_bill + ward_subtotal       


    ot_subtotal = invoice.ot_bills.aggregate(
        total=Sum('total_charge')
    )['total'] or 0


    misc_subtotal = invoice.misc_bills.aggregate(
        total=Sum('amount')
    )['total'] or 0


    grand_total_bill = invoice.total_amount + ward_running_bill
    grand_total_paid = invoice.total_paid
    grand_total_remaining = grand_total_bill - grand_total_paid 

    context = {
        'invoice': invoice,
        'consultation_subtotal': consultation_subtotal,
        'lab_subtotal': lab_subtotal,
        'medicine_subtotal': medicine_subtotal,
        'ward_subtotal': ward_subtotal,
        'ot_subtotal': ot_subtotal,
        'misc_subtotal': misc_subtotal,
        "qr_code": qr_code,
        'hospital':hospital,

	'ward_running_bill':ward_running_bill,
        'grand_total_ward_bill':grand_total_ward_bill,
        'grand_total_bill':grand_total_bill,
        'grand_total_paid':grand_total_paid,
        'grand_total_remaining':grand_total_remaining
    }

    return render(request, 'visitors/finalize_invoice.html', context)




def generate_invoice_qr(invoice):  
    invoice_url = f"http://care.ecare.support/billing/finalize_invoice/{invoice.id}/"

    qr = qrcode.make(invoice_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return qr_base64


def check_page_break(canvas, y_position, height, margin=50):
    if y_position < margin:
        canvas.showPage()
        canvas.setFont("Helvetica", 10)
        return height - margin
    return y_position



@login_required
def download_invoice(request, invoice_id):  
    invoice = BillingInvoice.objects.get(id=invoice_id)
    hospital = Location.objects.first()
    consultation_subtotal = invoice.consultation_bills.aggregate(total=Sum('consultation_fee'))['total'] or 0
    qr_code_base64 = generate_invoice_qr(invoice) 

    ward_subtotal = invoice.ward_bills.aggregate(
        total=Sum(ExpressionWrapper(
            F('charge_per_day') * F('days_stayed'),
            output_field=DecimalField()
        ))
    )['total'] or 0

    pdf = generate_invoice_pdf(invoice, hospital, consultation_subtotal,ward_subtotal, qr_code_base64)

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"invoice_{invoice.invoice_id}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'

    return response





def generate_invoice_pdf(invoice, hospital, consultation_subtotal,ward_subtotal, qr_code_base64):   
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=10, bottomMargin=30)
    
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, fontSize=12, spaceAfter=10))
    styles.add(ParagraphStyle(name='Heading', fontSize=16, alignment=1, spaceAfter=10, spaceBefore=10))
    styles.add(ParagraphStyle(name='SubHeading', fontSize=14, spaceAfter=8, spaceBefore=8))
    styles.add(ParagraphStyle(name='NormalBold', fontSize=12, spaceAfter=6, spaceBefore=6, leading=14, fontName='Helvetica-Bold'))
    
    # Logo and Header
    logo = "static/images/Logo.png"  # path to your hospital logo
    elements.append(Image(logo, width=60, height=60))
    elements.append(Paragraph(f"<b>Patient Invoice</b>", styles['Heading']))
    elements.append(Paragraph(f"{hospital.address} | {hospital.company.phone}", styles['Center']))
    elements.append(Spacer(1, 20))

    # Provisional Bill Title
    elements.append(Paragraph("🧾 Provisional Bill", styles['Heading']))
    triger_total_calculation = invoice.update_total_wardbill()

    # Patient Information
    if invoice.invoice_type == 'OPD':
        patient_id = invoice.patient.patient_id
        patient_name = invoice.patient.name
        doctor = invoice.patient.patient_appointments.first().doctor
        invoice_no = invoice.invoice_id
    else:
        patient_id = invoice.admission.patient.patient_id
        patient_name = invoice.admission.patient.name
        doctor = invoice.admission.admitting_doctor
        admission_no = invoice.admission.admission_code
        ward = invoice.admission.assigned_ward.name
        bed_room = f"{invoice.admission.assigned_bed.bed_number} / {invoice.admission.assigned_room.number}"

    patient_info = []
    patient_info.append([Paragraph("<b>Patient ID:</b>", styles['Normal']), patient_id])
    patient_info.append([Paragraph("<b>Name:</b>", styles['Normal']), patient_name])
    patient_info.append([Paragraph("<b>Doctor:</b>", styles['Normal']), doctor])

    if invoice.invoice_type != 'OPD':
        patient_info.append([Paragraph("<b>Admission No:</b>", styles['Normal']), admission_no])
        patient_info.append([Paragraph("<b>Ward:</b>", styles['Normal']), ward])
        patient_info.append([Paragraph("<b>Bed / Room:</b>", styles['Normal']), bed_room])

    patient_info.append([Paragraph("<b>Invoice No:</b>", styles['Normal']), invoice.invoice_id])
    patient_info.append([Paragraph("<b>Patient Contact:</b>", styles['Normal']), invoice.patient.email])

  
    patient_table = Table(patient_info, colWidths=[120, 200])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 20))


#===========================================================================================
    # ==============Consultation bill section=============80/170/80/100
  
    col_widths = [80, 170, 100, 80, 100]

    if invoice.consultation_bills.exists():
        data = []     
        data.append([
            Paragraph("<b>Consultation Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])
   
        data.append(["Appointment", "Doctor", "Consultation Date", "Patient Type", "Consultation Fee"])

        for bill in invoice.consultation_bills.all():
            if bill.appointment:
                code = bill.appointment.appointment_code
            elif bill.invoice.admission:
                code = bill.invoice.admission.admission_code
            else:
                code = 'unknown'
            data.append([
		code,
                str(bill.doctor),
                bill.consultation_date.strftime("%Y-%m-%d"),
                bill.patient_type,
                f"{bill.consultation_fee:.2f}"
            ])

        data.append(["", "", "", "Subtotal", f"{consultation_subtotal:.2f}"])

        consultation_table = Table(data, colWidths=col_widths)

        consultation_table.setStyle(TableStyle([         
           ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),       # 👈 Increase padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),    # 👈 Increase padding
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        elements.append(consultation_table)
        elements.append(Spacer(1, 20))
  
    #===========================================================================================

    # ==============Ward bill section=============
    col_widths = [60, 60, 60, 100, 200]
    if invoice.ward_bills.exists():
        data = []     
        data.append([
            Paragraph("<b>Ward Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])
   
        data.append( ["Ward", "Bed/Room", "Charge/day", "Days stayed", "Total"])      

        for bill in invoice.ward_bills.all():
            data.append([
                bill.patient_admission.assigned_ward.name,
                bill.patient_admission.assigned_bed.bed_number,
                bill.charge_per_day,              
                bill.days_stayed,
                bill.total_charge()
            ])        

        data.append(["", "", "", "Subtotal", f"{ward_subtotal:.2f}"])

        ward_table = Table(data, colWidths=col_widths)        

        ward_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),       # 👈 Increase padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),    # 👈 Increase padding
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(ward_table)
        elements.append(Spacer(1, 20))


    #===========================================================================================
    # ==============Medicine bill section=============

    medicine_subtotal = invoice.medicine_bills.aggregate(
        total=Sum(ExpressionWrapper(
            F('price_per_unit') * F('quantity'),
            output_field=DecimalField()
        ))
    )['total'] or 0


    col_widths = [180, 60, 60, 100]
    if invoice.medicine_bills.exists():
        data = []     
        data.append([
            Paragraph("<b>Medicine Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])

        data.append(["Medicine", "Quantity", "Unit price","Total"])

        for bill in invoice.medicine_bills.all():
            data.append([
                bill.medicine,
                bill.quantity,
                bill.price_per_unit,             
                bill.total_price()
            ])        

        data.append(["", "", "Subtotal", f"{medicine_subtotal:.2f}"])

        medicine_table = Table(data, colWidths=col_widths)        

        medicine_table.setStyle(TableStyle([
          ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),       # 👈 Increase padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),    # 👈 Increase padding
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(medicine_table)
        elements.append(Spacer(1, 20))


 # ==============Lab test  bill section=============invoice/lab_test/test_fee/test?date/
    lab_sub_total = invoice.lab_test_bills.aggregate(
            total=Sum('test_fee'))['total'] or 0


    col_widths = [180, 60, 60, 100]
    if invoice.lab_test_bills.exists():
        data = []     
        data.append([
            Paragraph("<b>Labtest Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])

        data.append(["Test Name", "Test Date", "Test Charge"])          

        for bill in invoice.lab_test_bills.all():
            data.append([
                bill.lab_test,
                bill.test_date.strftime('%d-%m-%Y'),
                bill.test_fee,             
               
            ])        

        data.append(["", "Subtotal", f"{lab_sub_total :.2f}"])

        lab_table = Table(data, colWidths=col_widths)        

        lab_table.setStyle(TableStyle([
           ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),       # 👈 Increase padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),    # 👈 Increase padding
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(lab_table)
        elements.append(Spacer(1, 20))



 # ============== OT  bill section=============#
    ot_sub_total = invoice.ot_bills.aggregate(
            total=Sum('total_charge'))['total'] or 0

    col_widths = [120, 120, 80, 100]

    if invoice.ot_bills.exists():
        data = []     
        data.append([
            Paragraph("<b>OT Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])
   
        data.append(["Operation Theatre", "Procedure Name", "Duration Hour", "Charge Per Hour", "Total"])

        for bill in invoice.ot_bills.all():
            data.append([
                bill.operation_theatre.name,
                bill.procedure_name,
                bill.duration_hours,
                bill.charge_per_hour,
                bill.total_charge
            ])

        data.append(["", "", "", "Subtotal", f"{ot_sub_total:.2f}"])

        ot_table = Table(data, colWidths=col_widths)

        ot_table.setStyle(TableStyle([         
           ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),       # 👈 Increase padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),    # 👈 Increase padding
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        elements.append(ot_table)
        elements.append(Spacer(1, 20))


    
 # ============== Misc  bill section=============##misc_bills.all//service_name/amount/crated-at
    misc_sub_total = invoice.misc_bills.aggregate(
            total=Sum('amount'))['total'] or 0


    col_widths = [180, 60, 60, 100]
    if invoice.misc_bills.exists():
        data = []     
        data.append([
            Paragraph("<b>Misc Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])
   
        data.append(["Service name", "Service Date", "Amount"])
         
        for bill in invoice.ot_bills.all():
            data.append([
                bill.service_name,
                bill.created_at,
                bill.amount,                     
               
            ])        

        data.append(["", "", "Subtotal", f"{misc_sub_total :.2f}"])

        misc_table = Table(data, colWidths=col_widths)        

        misc_table.setStyle(TableStyle([
             ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),       # 👈 Increase padding
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),    # 👈 Increase padding
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(lab_table)
        elements.append(Spacer(1, 20))

       
    grand_total_text = f"""
    <b>Grand Total:</b> {invoice.total_amount:.2f} &nbsp;&nbsp; || &nbsp;&nbsp; 
    <b>Total Paid:</b> {invoice.total_paid:.2f} &nbsp;&nbsp; || &nbsp;&nbsp;
    <b>Total Due:</b> {invoice.remaining_amount:.2f}<br/>       
    """
    elements.append(Paragraph(grand_total_text, styles['Normal']))
    elements.append(Spacer(1, 20))

    grand_total_due_text = f"""          
    <b>Total Due Bill in Words:</b> {num2words(invoice.remaining_amount, to='currency', lang='en_IN')}
    """
    elements.append(Paragraph(grand_total_due_text, styles['Normal']))
    elements.append(Spacer(1, 20))
        
      

    # Payment Status
    if invoice.status == "Paid":
        status_color = colors.green
        status_text = "PAID"
    elif invoice.status == "Partially Paid":
        status_color = colors.orange
        status_text = "PARTIALLY PAID"
    else:
        status_color = colors.red
        status_text = "DUE"

    status_paragraph = Paragraph(f"<para align=center><font size=24 color={status_color.hexval()}><b>{status_text}</b></font></para>", styles['Center'])
    elements.append(status_paragraph)
    elements.append(Spacer(1, 40))

    # QR Code and Signature
    qr_image_data = base64.b64decode(qr_code_base64)
    qr_image = Image(io.BytesIO(qr_image_data), width=100, height=100)

    qr_table = Table([
        [qr_image,'',Paragraph("Authorized Signature<br/>...............", styles['Center'])]
    ], colWidths=[150, 150, 150])

    elements.append(qr_table)
    
    # Build PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf





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
    logo = None
    if report.doctor and report.doctor.company and report.doctor.company.logo:
        logo = Image(report.doctor.company.logo, width=.8*inch, height=.8*inch)
    else:        
        logo = Paragraph("<b>Hospital Logo Missing</b>", styles['Normal'])

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
    if report.treatment_given:
        story.append(Paragraph(f"<b>Treatment Given:</b> {report.treatment_given}", normal))
    if report.summary:
        story.append(Paragraph(f"<b>Summary:</b> {report.summary}", normal))
    story.append(Spacer(1, 0.2*inch))

    if report.follow_up_instructions:
        story.append(Paragraph("Follow-up Instructions", h2))
        story.append(Paragraph(report.follow_up_instructions, normal))
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




