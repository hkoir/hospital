from django.contrib.auth.decorators import login_required
from datetime import datetime, time, timedelta
from .forms import DoctorForm
from django.shortcuts import render, get_object_or_404,redirect
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.utils.timezone import make_aware
from django.db.models import Count
from datetime import date
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator

from core.models import Doctor,Specialization
from .models import AppointmentSlot,Appointment
from patients.models import Patient
from medical_records.models import MedicalRecord,Prescription
from .forms import TimeSlotForm
from billing.models import BillingInvoice,Payment,ConsultationBill

from django.db.models import Q
from.models import AppointmentSlot



def generate_time_slots(doctor, slot_duration, start_date, end_date):   
    slot_delta = timedelta(minutes=slot_duration)   
    if start_date > end_date:
        return False

    for single_date in (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1)):
        current_time = doctor.start_time

        while current_time < doctor.end_time:
            slot_end_time = (datetime.combine(single_date, current_time) + slot_delta).time()
            AppointmentSlot.objects.create(
                doctor=doctor,
                date=single_date,
                start_time=current_time,
                end_time=slot_end_time,
                slot_duration = slot_duration,
                is_booked=False
            )
            current_time = slot_end_time  # Move to the next slot
    return True



 
def generate_monthly_timeslots(doctor_id, year, month, start_time="09:00", end_time="17:00", slot_duration=30):
  
    doctor = Doctor.objects.get(id=doctor_id)
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month + 1, 1) - timedelta(days=1)  # Last day of the month

    current_date = first_day
    slots_created = 0

    while current_date <= last_day:       
        if current_date.weekday() not in [5, 6]:           
            aware_date = make_aware(datetime.combine(current_date, datetime.min.time()))           
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")

            current_time = start_dt
            while current_time < end_dt:
                slot_start = make_aware(datetime.combine(current_date, current_time.time()))
                slot_end = make_aware(datetime.combine(current_date, (current_time + timedelta(minutes=slot_duration)).time()))

                # Create timeslot entry
                AppointmentSlot.objects.create(
                    doctor=doctor,
                    date=aware_date.date(),
                    start_time=slot_start.time(),
                    end_time=slot_end.time(),
                    is_booked=False
                )

                slots_created += 1
                current_time += timedelta(minutes=slot_duration)  # Move to next slot
        current_date += timedelta(days=1)  # Move to next day
    print(f"{slots_created} timeslots generated for Doctor {doctor_id} (excluding weekends).")




def create_doctor_timeslots(request, id=None):  
    instance = get_object_or_404(AppointmentSlot, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = TimeSlotForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)
        doctor = form.cleaned_data["doctor"]
        slot_duration = form.cleaned_data["slot_duration"]
        start_date = form.cleaned_data["start_date"]
        end_date = form.cleaned_data["end_date"]

        success = generate_time_slots(doctor, slot_duration, start_date, end_date)
        if success:
            return redirect("appointments:create_doctor_timeslots")  # Redirect after success
        else:
            form.add_error(None, "End date must be after start date.")           
        messages.success(request, message_text)
        return redirect('appointments:create_doctor_timeslots')  

    datas = AppointmentSlot.objects.all().order_by('-date')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    form = TimeSlotForm( instance=instance)
    return render(request, 'appointments/manage_doctor_timeslots.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })



def delete_doctor_timeslots(request, id):
    instance = get_object_or_404(AppointmentSlot, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('appointments:create_doctor_timeslots')  

    messages.warning(request, "Invalid delete request!")
    return redirect('appointments:create_doctor_timeslots')  




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

    return render(request, "appointments/available_doctors.html", {
        "categorized_doctors": categorized_doctors,
        "query": query,
        "specialization_filter": specialization_filter,
        'appointments': appointments
    })





def view_available_slots(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    date = request.GET.get('date')

    slots = []
    if date:
        # Filter or generate slots for that doctor on that date
        slots = AppointmentSlot.objects.filter(doctor=doctor, date=date)

    return render(request, 'appointments/available_slots.html', {
        'doctor': doctor,
        'slots': slots,
        'selected_date': date,
    })





def doctor_list(request):
    query = request.GET.get('q', '')
    doctors = Doctor.objects.all()

    if query:
        doctors = doctors.filter(
            Q(name__icontains=query) | 
            Q(specialization__name__icontains=query)
        )

    doctors = doctors.order_by('name')
    return render(request, 'appointments/doctor_list.html', {'doctors': doctors, 'query': query})


from billing.models import DoctorServiceRate
def get_timeslots(request):
    doctor_id = request.GET.get("doctor_id")
    date = request.GET.get("date")
    slots = AppointmentSlot.objects.filter(doctor_id=doctor_id, date=date,is_booked = False)
    consultation_rate = DoctorServiceRate.objects.filter(doctor_id = doctor_id).first()

    fee = float(consultation_rate.rate) if consultation_rate else 0.00
    slots_list = [
        {
            "id": slot.id,  
            "start_time": str(slot.start_time),
            "end_time": str(slot.end_time),
            "is_booked": slot.is_booked,
	    "consultation_fee":fee
        }
        for slot in slots
    ]

    return JsonResponse({"slots": slots_list})




@csrf_exempt
@login_required
def book_slot(request):
    if request.method == "POST":
        with transaction.atomic():
            try:
                # Use request.POST instead of JSON
                slot_id = request.POST.get("slot_id")
                doctor_id = request.POST.get("doctor_id")
                name = request.POST.get("name")
                email = request.POST.get("email")
                phone = request.POST.get("phone")
                gender = request.POST.get("gender")
                date_of_birth = request.POST.get("date_of_birth")
                address = request.POST.get("address")
                medical_history = request.POST.get("medical_history")
                photo = request.FILES.get("patient_photo")

                if not all([slot_id, doctor_id, name, email, phone]):
                    return JsonResponse({"success": False, "error": "All required fields must be filled."})

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
                    patient_type="OPD"
                )

                slot.is_booked = True
                slot.save()

                return JsonResponse({
                    "success": True,
                    "message": f"{message} Appointment with Dr.{doctor.name} on {slot.date} from {slot.start_time} to {slot.end_time} has been confirmed."
                })

            except AppointmentSlot.DoesNotExist:
                return JsonResponse({"success": False, "error": "Slot does not exist or is already booked."})
            except Doctor.DoesNotExist:
                return JsonResponse({"success": False, "error": "Doctor does not exist."})
            except Exception as e:
                print(f"Error: {str(e)}")
                return JsonResponse({"success": False, "error": "An unexpected error occurred."})

    return JsonResponse({"success": False, "error": "Invalid request method."})






@login_required
def general_appointment(request):
    doctors = Doctor.objects.all()
    patients = Patient.objects.all()

    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        slot_id = request.POST.get("slot_id")
        patient_id = request.POST.get("patient_id")
        appointment_date = request.POST.get("appointment_date")
        consultation_fee = request.POST.get("consultation_fee")
        patient_type_choice = request.POST.get("patient_type")

        # Validate patient type
        if patient_type_choice not in ['OPD', 'IPD', 'Emergency']:
            messages.error(request, 'Invalid patient type selected.')
            return redirect('appointments:general_appointment')

        if not all([doctor_id, slot_id, appointment_date, consultation_fee, patient_id]):
            messages.error(request, "All fields are required.")
            return redirect('appointments:general_appointment')

        # Validate objects
        slot = get_object_or_404(AppointmentSlot, id=slot_id, is_booked=False)
        doctor = get_object_or_404(Doctor, id=doctor_id)
        patient = get_object_or_404(Patient, id=patient_id)

        # Create appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            timeslot=slot,
            date=appointment_date,
            patient_type=patient_type_choice,
            user=request.user,
            payment_status='UnPaid',
        )

        # Mark slot as booked
        slot.is_booked = True
        slot.save()

        messages.success(request, "Appointment booked successfully.")
        return redirect("appointments:appointment_list")

    return render(request, "appointments/general_appointement_booking.html", {
        "doctors": doctors,
        "patients": patients,
    })




from billing.models import DoctorServiceLog


def booking_confirmation_payment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.status == 'Cancelled':
        messages.warning(request, 'Cannot process payment: Appointment is cancelled.')
        return redirect('appointments:appointment_list')
    if appointment.payment_status == 'Paid':
        messages.info(request, 'This appointment has already been paid.')
        return redirect('appointments:appointment_list')

    patient = appointment.patient
    doctor_fee = appointment.doctor.consultation_fees  
    appointment.patient_type = 'OPD'
    appointment.save()
    doctor_consultation_fee =0
    
    doctor_service =DoctorServiceRate.objects.filter(doctor = appointment.doctor,service_type="Consultation").first()
    if doctor_service:
        doctor_consultation_fee = doctor_service.rate
    else:
        doctor_consultation_fee= 0

    if not appointment.medical_record:  # Check if there is no medical record already linked
        medical_record = MedicalRecord(
            patient=patient,
            doctor=appointment.doctor,
            diagnosis='TBD',
            treatment_plan='TBD'
        )
        medical_record.save()
        
        # Link the medical record to the appointment
        appointment.medical_record = medical_record
        appointment.save()
    else:
        medical_record = appointment.medical_record

    if request.method == 'POST':
        invoice = BillingInvoice(
            patient=patient,
            medical_record=medical_record,
            total_amount=doctor_consultation_fee,
            total_paid=doctor_consultation_fee,
            invoice_type = 'OPD',
            patient_type = 'OPD'
        )
     
        invoice.save()         

        consultation_bill, created = ConsultationBill.objects.get_or_create(
            invoice=invoice,
            appointment=appointment,
            defaults={
                'doctor': appointment.doctor,
                'consultation_fee': doctor_consultation_fee,
                'consultation_type': 'Initial',
                'patient_type': 'OPD',
                'status': 'Paid'
            }
        )



        Payment.objects.create(
            invoice=invoice,
            amount_paid=doctor_fee,
            payment_type='Consultation',
            payment_method='Card',
            remarks='Initial first Consulation fees payment',
            patient_type ='OPD'
        )

 
        log = DoctorServiceLog.objects.filter(
            invoice=invoice,
            medical_record = medical_record,
            doctor=consultation_bill.doctor,
            service_type='Consultation',
            patient=appointment.patient,
            service_date=consultation_bill.consultation_date,
        ).first()

        if not log:
            try:
                DoctorServiceLog.objects.create(
                    invoice=invoice,
                    medical_record = medical_record,
                    doctor=consultation_bill.doctor,
                    service_type='Consultation',
                    patient=appointment.patient,
                    service_date=appointment.date,
                    service_fee = doctor_consultation_fee
                )
            except DoctorServiceRate.DoesNotExist:
                messages.warning(request, f"Doctor service rate not defined for {consultation_bill.doctor}")


        invoice.total_amount = invoice.calculate_total()
        invoice.total_paid = invoice.calculate_total_paid_amount()
        invoice.remaining_amount = invoice.total_amount - invoice.total_paid
        appointment.payment_status = 'Paid'
        appointment.save()
        if invoice.total_paid >= invoice.total_amount:
            invoice.status = 'Paid'
        elif invoice.total_paid == 0:
            invoice.status = 'Unpaid'
        else:
            invoice.status = 'Partially Paid'
        invoice.save()       

        return redirect('billing:invoice_detail', invoice_id=invoice.id)

    context = {
        'appointment': appointment,
        'patient': patient,
        'doctor_fee': doctor_fee,
    }
    return render(request, 'billing/booking_confirmation_payment.html', context)









from billing.models import BillingInvoice,MedicineBill,LabTestBill
from django.db.models import Sum
from medical_records.models import PrescribedMedicine
from lab_tests.models import LabTestRequest,SuggestedLabTestItem,SuggestedLabTestRequest,LabTestRequestItem




from billing.models import BillingInvoice,MedicineBill,LabTestBill
from lab_tests.models import LabTestRequest,SuggestedLabTestItem,SuggestedLabTestRequest,LabTestRequestItem
from django.db.models import Sum
from medical_records.models import PrescribedMedicine

def add_medicine_labtest_to_invoice(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    medical_record = appointment.medical_record
    patient=appointment.patient

    prescriptions = PrescribedMedicine.objects.filter(prescription__medical_record=medical_record)
    #lab_requests = SuggestedLabTestItem.objects.filter(suggested_labtest__medical_record=medical_record)
    suggest_lab_test = SuggestedLabTestRequest.objects.filter(medical_record=medical_record).first()
    lab_requests = suggest_lab_test.suggested_items.all() if suggest_lab_test else SuggestedLabTestItem.objects.none()



    if request.method == 'POST':
        selected_prescriptions = []
        total_medicine_cost = 0

        for pres in prescriptions:
            qty_str = request.POST.get(f'quantity_{pres.id}', '0')
            try:
                qty = int(qty_str)
            except ValueError:
                qty = 0

            if qty > 0:
                unit_price = pres.medication_name.base_unit_price or 0
                subtotal = unit_price * qty
                total_medicine_cost += subtotal
                selected_prescriptions.append((pres, qty, unit_price, subtotal))

        selected_labtest_ids = request.POST.getlist('selected_labtests')
        selected_labtests = SuggestedLabTestItem.objects.filter(id__in=selected_labtest_ids,suggested_labtest__medical_record=medical_record)
        total_lab_test_cost = sum(
            (lr.lab_test.price or 0) for lr in selected_labtests if lr.lab_test and lr.lab_test.test_name
        )

        grand_total = total_medicine_cost + total_lab_test_cost

        with transaction.atomic():
            # Invoice - update or create           
            invoice, created = BillingInvoice.objects.update_or_create(
                    patient=patient,
                    medical_record=medical_record,
                    defaults={                   
                        'total_amount': grand_total,
                        'total_paid': grand_total,                   
                    }
                )

            payment = Payment.objects.create(
                invoice=invoice,
                amount_paid=grand_total,
                payment_type='Full',
                patient_type='OPD',
                payment_method='Cash',
            )

            # Recalculate total_paid
            invoice.total_paid = invoice.payments.aggregate(total=Sum('amount_paid'))['total'] or 0
            invoice.save(update_fields=['total_paid'])
            invoice.update_totals()


            # Clear previous items if re-adding
            MedicineBill.objects.filter(invoice=invoice).delete()
            LabTestBill.objects.filter(invoice=invoice).delete()

            # Create medicine items         
            for pres, qty, unit_price, subtotal in selected_prescriptions:
                MedicineBill.objects.create(
                    invoice=invoice,                    
                    medicine=pres.medication_name,
                    quantity=qty,
                    price_per_unit=unit_price,
                    patient_type = 'OPD',
                    status ='Paid'
                )

            lab_test_request = LabTestRequest.objects.create(
                medical_record=medical_record,               
                    patient_type= 'OPD',
                    status='Pending'               
                
                    )
            
            # Create lab test items            
            for lr in selected_labtests:
                if lr.lab_test and lr.lab_test.test_name:
                    LabTestBill.objects.create(
                        invoice=invoice,
                        lab_test_catelogue=lr.lab_test,                        
                        test_fee=lr.lab_test.price or 0,
                        status = 'Paid',
                        patient_type = 'OPD'
                    )
                   
                    LabTestRequestItem.objects.create(
                       labtest_request=lab_test_request,
                        lab_test=lr.lab_test,
                       
                    )


        return redirect('billing:invoice_detail', invoice.id)

    # For GET request
    prescription_items = [{
        'id': p.id,
        'medicine_name': p.medication_name.name,
        'type': p.medication_type.name if p.medication_type else '',
        'category': p.medication_category.name if p.medication_category else '',
        'dosage': p.dosage,
        'schedule': p.dosage_schedule,
        'duration': p.medication_duration,
        'uom': p.UOM,
        'quantity': p.quantity or 1,
        'price': p.medication_name.base_unit_price or 0,
    } for p in prescriptions if p.medication_name]

    lab_tests = [{
        'id': lr.id,
        'test_name': lr.lab_test.test_name,
        'test_type': lr.lab_test.test_type,
        'description': lr.lab_test.description,      
        'price': lr.lab_test.price or 0,
    } for lr in lab_requests if lr.lab_test and lr.lab_test.test_name]

    context = {
        'appointment': appointment,
        'prescriptions': prescription_items,
        'lab_tests': lab_tests,
    }

    return render(request, 'appointments/add_medicine_labtest.html', context)




def specialization_detail(request, specialization_id):
    appointments = Appointment.objects.select_related("patient", "timeslot").all()
    specialization = get_object_or_404(Specialization, id=specialization_id)   
    specializations = Specialization.objects.all()


    query = request.GET.get("query", "").strip() 
    doctors = specialization.specialized_doctors.all()  

    if query:
        doctors = doctors.filter(name__icontains=query)  

    return render(request, "appointments/specialization_details.html", {
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





def appointment_list(request):     
    appointments = Appointment.objects.none()
    doctors = Doctor.objects.all()  
    patients = Patient.objects.all()  
    doctor_appointment_counts = []

    if request.method == 'GET':       
        doctor_filter = request.GET.get("doctor")
        patient_filter = request.GET.get("patient")
        date_filter = request.GET.get("date", "").strip()
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        today = timezone.now().date()
        
        appointments = Appointment.objects.all()    
    
        if doctor_filter: 
            appointments = appointments.filter(doctor__id=doctor_filter)  

        if patient_filter:  
            appointments = appointments.filter(patient__id=patient_filter) 

        if date_filter:
            appointments = appointments.filter(date=date_filter)

        if start_date and end_date:
            appointments = appointments.filter(date__range=[start_date, end_date])

        if not (doctor_filter or patient_filter or date_filter or (start_date and end_date)):
            appointments = appointments.filter(date=today)

        doctor_appointment_counts = (
            appointments.values("doctor__id", "doctor__name")
            .annotate(total_appointments=Count("id"))
            .order_by("-total_appointments") 
        )

        for appointment in appointments:
            medical_record = MedicalRecord.objects.filter(
                doctor=appointment.doctor, 
                patient=appointment.patient
            ).first()
            appointment.medical_record = medical_record 

            appointment_prescriptions = Prescription.objects.filter(
                medical_record=appointment.medical_record, 
            )
            appointment.prescriptions = appointment_prescriptions

    return render(request, "appointments/appointment_list.html", {
        "appointments": appointments,
        "doctor_appointment_counts": doctor_appointment_counts, 
        'today': date.today(),
        'doctors': doctors,
        'patients': patients,
    })





@csrf_exempt
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
