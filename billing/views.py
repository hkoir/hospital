from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.http import JsonResponse,HttpResponse
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import base64
from io import BytesIO

from num2words import num2words
import qrcode
from django.contrib import messages

from django.contrib.auth.decorators import login_required,permission_required,user_passes_test
from reportlab.platypus import PageBreak
from django.core.paginator import Paginator


from facilities.models import Bed
from billing.models import DoctorServiceLog
from core.models import Location
from .models import BillingInvoice, MedicineBill,LabTest,DoctorServiceRate,DoctorPayment,WardBill
from patients.models import Patient
# from inventory.models import Batch,Product
from product.models import Product
from purchase.models import Batch
from .forms import ConsultationBillForm,LabTestBillForm,BillingInvoiceForm,PaymentForm,DoctorServiceRateForm
from.forms import WardBillForm,MedicineBillForm,OTBookingForm,MiscBillForm,EmergencyVisitForm,CommonFilterForm

from django.forms import modelformset_factory
MedicineBillFormSet = modelformset_factory(MedicineBill, form=MedicineBillForm, extra=1, can_delete=True)
from billing.models import BillingInvoice,LabTestBill
import json
from lab_tests.models import LabTestRequest
from django.db import transaction
from appointments.models import Appointment,AppointmentSlot
from billing.models import ConsultationBill
from django.urls import reverse


from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.dateparse import parse_date
from django.db.models import Sum, Q
from.models import ReferralSource,ReferralPayment,DoctorPayment,ReferralCommissionRule,ReferralCommissionTransaction
from .models import BillingInvoice,LabTestBill,Payment,ConsultationBill
from .models import BillingInvoice, MedicineBill,LabTest,DoctorServiceRate
from appointments.models import Appointment,AppointmentSlot
from core.models import Doctor
from.forms import DoctorPaymentForm,ReferralCommissionRuleForm,ReferralSourceForm
from .forms import ConsultationBillForm,LabTestBillForm,BillingInvoiceForm,PaymentForm,DoctorServiceRateForm
from.forms import WardBillForm,MedicineBillForm,OTBookingForm,MiscBillForm,EmergencyVisitForm,CommonFilterForm


from billing.utils import get_doctor_financials
from patients.models import PatientAdmission
from django.utils.timezone import now
from django.utils.timezone import localtime
from medical_records.models import MedicalRecord
from lab_tests.models import LabTestCatalog,LabTestRequest,LabTestRequestItem
from messaging.models import Notification
from messaging.views import create_notification
from django.urls import reverse






@login_required
def create_invoice(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    invoice = BillingInvoice.objects.create(
        patient=patient,
       
    )
    return redirect('billing:invoice_detail', invoice_id=invoice.id)






@login_required
def ipd_invoice_list(request):
    form = CommonFilterForm(request.GET)
    #create_notification(request.user,notification_type='Alert Message',message='This is alert message to all of you to take care as necessary during this pendamic')
    if request.method == 'GET':    
        if form.is_valid():
            entity_id = form.cleaned_data['entity_id']
            patient_name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            patient_id = form.cleaned_data['patient_id']
            admission = form.cleaned_data['admission']

            invoice_type = form.cleaned_data.get('service_type')
            invoices = BillingInvoice.objects.select_related('patient').order_by('-created_at')

            if admission:
                invoices= invoices.filter(admission__isnull = False)
            if invoice_type:
                invoices = invoices.filter(invoice_type=invoice_type)
            else:
                invoices = invoices
            if entity_id:
                invoices = invoices.filter(invoice_id__icontains=entity_id)
            if patient_name:
                invoices = invoices.filter(patient__name__icontains=patient_name)
            if phone_number:
                invoices = invoices.filter(patient__phone=phone_number)
            if email:
                invoices = invoices.filter(patient__email=email)
            if patient_id:
                invoices = invoices.filter(patient__patient_id__icontains=patient_id)
            
    datas = invoices
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'billing/ipd_invoice_list.html', {'form': form, 'page_obj': page_obj})



@login_required
def opd_invoice_list(request):
    form = CommonFilterForm(request.GET)    
    if request.method == 'GET':    
        if form.is_valid():
            entity_id = form.cleaned_data['entity_id']
            patient_name = form.cleaned_data['name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            patient_id = form.cleaned_data['patient_id']

            invoice_type = form.cleaned_data.get('service_type') or 'OPD'
            invoices = BillingInvoice.objects.select_related('patient').order_by('-created_at')
           
            if invoice_type:
                invoices = invoices.filter(invoice_type=invoice_type)
            else:
                invoices = invoices.filter(invoice_type='OPD')        

            if entity_id:
                invoices = invoices.filter(invoice_id__icontains=entity_id)
            if patient_name:
                invoices = invoices.filter(patient__name__icontains=patient_name)
            if phone_number:
                invoices = invoices.filter(patient__phone=phone_number)
            if email:
                invoices = invoices.filter(patient__email=email)
            if patient_id:
                invoices = invoices.filter(patient__patient_id__icontains=patient_id)

    datas = invoices
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'billing/opd_invoice_list.html', {'form': form, 'page_obj': page_obj})




@login_required
def invoice_detail(request, invoice_id):   
    invoice = get_object_or_404(BillingInvoice, id=invoice_id) 
    patient_id = invoice.patient.id  # Ensure this is valid
    admission_id = invoice.admission.id if invoice.admission else None

    buttons_list = [
        {'url': reverse('billing:ipd_followup_booking', args=[patient_id, invoice_id]), 'label': 'IPD Followup Booking', 'btn_class': 'btn-warning'},
        {'url': reverse('billing:add_lab_test_bill', args=[invoice_id]), 'label': 'Add Lab test bill', 'btn_class': 'btn-info'},
        {'url': reverse('billing:add_medicine_bill', args=[invoice_id]), 'label': 'Add Medicine bill', 'btn_class': 'btn-primary'},
        {'url': reverse('billing:add_misc_bill', args=[invoice_id]), 'label': 'Add Misc bill', 'btn_class': 'btn-secondary'},
        {'url': reverse('billing:ot_booking', args=[invoice_id]), 'label': 'OT Booking', 'btn_class': 'btn-danger'},
        {'url': reverse('billing:add_payment', args=[invoice_id]), 'label': 'Add Payment', 'btn_class': 'btn-success'},
	{'url': reverse('billing:finalize_invoice', args=[invoice_id]), 'label': 'Bill Details', 'btn_class': 'btn-success'},

  ]


    return render(request, "billing/invoice_details.html", {
        "invoice": invoice,
        'buttons_list': buttons_list,
    })



@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    if request.method == 'POST':
        form = BillingInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.save()  # triggers your custom save() to recalculate totals/status
            return redirect('billing:invoice_details', invoice_id=invoice.id)
    else:
        form = BillingInvoiceForm(instance=invoice)
    
    return render(request, 'billing/edit_invoice.html', {
        'form': form,
        'invoice': invoice,
    })


@login_required
def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    if request.method == 'POST':
        invoice.delete()
        return redirect('billing:invoice_list')
    
    return render(request, 'billing/delete_invoice_confirm.html', {
        'invoice': invoice,
    })



from core.models import Doctor

@login_required
def get_consultation_fee(request):
    doctor_id = request.GET.get('doctor_id')
    fee = 0
    if doctor_id:
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            fee = doctor.consultation_fees  # Assuming this field exists on the Doctor model
        except Doctor.DoesNotExist:
            pass
    return JsonResponse({'fee': fee})


@login_required
def add_ipd_consultation_bill(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    doctor_fee = None
    latest_appointment = None
    doctor = None
    patient = invoice.patient
    doctor_service_rate = 0

    # Get latest appointment to extract doctor and fee
    patient_appointments = patient.patient_appointments.all()
    if patient_appointments.exists():
        latest_appointment = patient_appointments.order_by('-date').first()
        doctor = latest_appointment.doctor
        if doctor:
            doctor_service_rate = DoctorServiceRate.objects.filter(doctor=doctor,service_type='Consulation').first()
            doctor_fee = doctor_service_rate.rate


    if request.method == 'POST':
        form = ConsultationBillForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.invoice = invoice
            consultation.save()

            # Log doctor service
            DoctorServiceLog.objects.create(
                doctor=consultation.doctor,
                service_type='Consultation',
                patient=consultation.invoice.patient,
                service_date=consultation.consultation_date,
               
            )
            invoice.update_totals()
            invoice.save()
            return redirect('billing:invoice_detail', invoice_id=invoice.id)
    else:
        form = ConsultationBillForm(initial={
            'consultation_fee': doctor_fee,
            'doctor': doctor,
            'invoice': invoice,
            'appointment': latest_appointment
        })

    return render(request, 'billing/add_ipd_consultation_bill.html', {
        'form': form,
        'invoice': invoice,
    })




@login_required
def ipd_followup_booking(request, patient_id, invoice_id):
    patient = get_object_or_404(Patient, id=patient_id)
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    doctors = Doctor.objects.all()

    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        slot_id = request.POST.get("slot_id")
        appointment_date = request.POST.get("appointment_date")
        patient_type_choice = request.POST.get("patient_type")

        if patient_type_choice not in ['OPD', 'IPD', 'Emergency']:
            messages.error(request, "Invalid patient type.")
            return redirect(request.path)

        if not all([doctor_id, slot_id, appointment_date]):
            return render(request, "billing/ipd_follow_up_booking.html", {
                "error": "All fields are required.",
                "doctors": doctors,
                "patient": patient,
                "invoice": invoice
            })

        with transaction.atomic(): 
            slot = AppointmentSlot.objects.select_for_update().filter(
                id=slot_id, is_booked=False
            ).first()
            if not slot:
                messages.error(request, "This slot is already booked.")
                return redirect(request.path)

            doctor = get_object_or_404(Doctor, id=doctor_id) 
            new_appointment = Appointment.objects.create(
                medical_record=invoice.medical_record,
                patient=patient,
                doctor=doctor,
                timeslot=slot,
                invoice=invoice,
                date=appointment_date,
                patient_type="IPD",
                appointment_type =patient.next_appointment_type(doctor),
                user=request.user,
                payment_status='Unpaid',
                status='Scheduled' 
            )

            slot.is_booked = True
            slot.save()

            messages.success(request, "Follow-up appointment booked successfully.")
            return redirect("workspace:staff_dashboard")

    return render(request, "billing/ipd_follow_up_booking.html", {
        "doctors": doctors,
        "patient": patient,
        "invoice": invoice
    })


@login_required
def ipd_followup_confirm_visit(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if appointment.status != 'Scheduled':
        messages.warning(request, "Appointment already processed.")
        return redirect('workspace:staff_dashboard')

    doctor_service = DoctorServiceRate.objects.filter(
        doctor=appointment.doctor,
        service_type='Followup-Consultation'
    ).first()

    if not doctor_service:
        messages.warning(request, f"No consultation rate set for {appointment.doctor}.")
        return redirect('workspace:staff_dashboard')

    consultation_fee = doctor_service.rate

    consultation_bill, created = ConsultationBill.objects.get_or_create(
        invoice=appointment.medical_record.billing_invoice_records,
        appointment=appointment,
        defaults={
            'doctor': appointment.doctor,
            'consultation_fee': consultation_fee,
            'user': request.user,
            'patient_type': appointment.patient_type,
            'consultation_date': appointment.date,
            'consultation_type': 'Follow-Up',
            'status': 'Unpaid',
        }
    )

    if not created:
        messages.warning(request, "Consultation bill already exists for this appointment.")

    # Doctor service log
    DoctorServiceLog.objects.get_or_create(
        doctor=appointment.doctor,
        invoice=appointment.medical_record.billing_invoice_records,
        medical_record=appointment.medical_record,
        service_type='Consultation',
        patient=appointment.patient,
        service_date=appointment.date,
        defaults={'service_fee': consultation_fee}
    )

    appointment.status = 'Prescription-Given'
    appointment.save(update_fields=['status'])
    invoice = appointment.invoice
    invoice.update_totals()
    invoice.save()
    messages.success(request, "Consultation visit confirmed and bill created.")
    return redirect('workspace:staff_dashboard')




def get_test_fee(request):
    lab_test_catelogue_id = request.GET.get('lab_test_catelogue_id')  # was lab_test_id
    fee = 0
    if lab_test_catelogue_id:
        try:
            test = LabTestCatalog.objects.get(id=lab_test_catelogue_id)
            fee = test.price if test.price else 0
        except LabTestCatalog.DoesNotExist:
            pass
    return JsonResponse({'fee': fee})




@login_required
def add_lab_test_bill(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    LabTestBillFormSet = modelformset_factory(LabTestBill, form=LabTestBillForm, extra=1, can_delete=True)

    total_amount = 0        

    if request.method == 'POST':
        formset = LabTestBillFormSet(request.POST)

        if formset.is_valid():
            with transaction.atomic():
                instances = formset.save(commit=False)
                created_bills = []
                created_requests = []

                lab_test_request, created = LabTestRequest.objects.get_or_create(
                    medical_record=invoice.medical_record,
                    patient_type='External-Lab-Test',
                    defaults={'requested_by': invoice.medical_record.doctor, 'status': 'Unpaid'}
                )
                if not created:
                    lab_test_request.requested_by = invoice.medical_record.doctor
                    lab_test_request.status = 'Unpaid'
                    lab_test_request.save()

                for form, instance in zip(formset.forms, instances):
                    if form.cleaned_data.get('DELETE'):
                        continue

                    instance.invoice = invoice
                    instance.test_fee = instance.lab_test_catelogue.price or 0
                    #instance.patient_type = invoice.patient_type
                    instance.lab_test_request_order = lab_test_request
                    instance.status ='Paid'
                    instance.save()
                    created_bills.append(instance)
                    total_amount += instance.test_fee

                    # Create related LabTestRequest
                    lab_test_request_items = LabTestRequestItem.objects.create(
			labtest_request= lab_test_request,
                        lab_test=instance.lab_test_catelogue,
                        status = 'Paid',
			notes =  f'Labtest for IPD patient{invoice.medical_record.patient.name} doctor -{invoice.medical_record.doctor}'
                    )
                    created_requests.append(lab_test_request)

                # Handle deletions
                for form in formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()

                # Update invoice totals and status
                invoice.update_totals()
              
                # Set invoice status
                if invoice.total_paid >= invoice.total_amount:
                    invoice.status = 'Paid'
                    status = 'Paid'
                elif invoice.total_paid == 0:
                    invoice.status = 'Unpaid'
                    status = 'Unpaid'
                else:
                    invoice.status = 'Partially-Paid'
                    status = 'Partially-Paid'
                invoice.save(update_fields=['status'])

                # Update statuses
                for bill in created_bills:
                    bill.status = status
                    bill.save()
                for request_obj in created_requests:
                    request_obj.status = status
                    request_obj.save()
                invoice.update_totals()
                invoice.save()
                return redirect('billing:ipd_invoice_list')
    else:
        formset = LabTestBillFormSet(queryset=LabTestBill.objects.none())

    # For JS to access test price dynamically
    test_prices = {
    str(test.id): float(test.price) or 0 for test in LabTestCatalog.objects.all()
        }


    test_prices_json = json.dumps(test_prices)

    return render(request, 'billing/add_lab_test_bill.html', {
        'formset': formset,
        'invoice': invoice,
        'test_prices': test_prices_json,
        'total_amount': total_amount
    })






@login_required
def add_ward_bill(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)

    if request.method == 'POST':
        form = WardBillForm(request.POST)
        if form.is_valid():
            ward_bill = form.save(commit=False)
            bed_number = form.cleaned_data['bed']
            bed = get_object_or_404(Bed,bed_number = bed_number)
            ward_bill.invoice = invoice    
            ward_bill.patient_type = 'IPD'     
            if ward_bill.bed:
                ward_bill.charge_per_day = bed.daily_charge
            ward_bill.save()
            invoice.update_totals()
            invoice.save()                
            return redirect('billing:invoice_detail', invoice_id=invoice.id)
        else:
            print(form.errors)
    else:
        form = WardBillForm()

    return render(request, 'billing/add_ward_bill.html', {'form': form, 'invoice': invoice})





def get_batch_price(request):  
    product_id = request.GET.get('medicine_id')
    data = {'unit_price': ''}
    
    if product_id:
        batch_qs = Batch.objects.filter(product_id=product_id, expiry_date__gte=timezone.now().date())
        batch = batch_qs.order_by('-manufacture_date').first() 

        if batch:
            data['unit_price'] = str(batch.sale_price or batch.unit_price)
        else:          
            product = get_object_or_404(Product, id=product_id)
            data['unit_price'] = str(product.base_unit_price)  

    return JsonResponse(data)



@login_required
def add_medicine_bill(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)

    if request.method == 'POST':    
        formset = MedicineBillFormSet(request.POST, queryset=MedicineBill.objects.none())      

        if formset.is_valid():          
            for form in formset:
                if not form.cleaned_data.get('DELETE', False):
                    medicine = form.save(commit=False)
                    medicine.invoice = invoice                   
                    medicine.save() 
            invoice.update_totals()
            invoice.save()  
            messages.success(request, 'Medicine bill has been successfully added.')
            return redirect('billing:ipd_invoice_list')
        else:
            print(formset.errors)  # Debugging help

    else:
        formset = MedicineBillFormSet(queryset=MedicineBill.objects.none())

    return render(request, 'billing/add_medicine_bill.html', {
        'formset': formset,
        'invoice': invoice
    })



@login_required
def add_misc_bill(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    if request.method == 'POST':
        form = MiscBillForm(request.POST)
        if form.is_valid():
            misc_bill = form.save(commit=False)
            misc_bill.invoice = invoice
            misc_bill.save()

        invoice.update_totals()
        invoice.save() 
        return redirect('billing:invoice_detail', invoice_id=invoice.id)
    else:
        form = MiscBillForm()

    return render(request, 'billing/add_misc_bill.html', {'form': form, 'invoice': invoice})





from .forms import OTBookingForm, OTBookingProcedureFormSet
from facilities.models import OTBooking 
from facilities.utils import generate_ot_bills
from billing.models import BillingInvoice

@login_required
def ot_booking(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)

    if request.method == 'POST':

        form = OTBookingForm(request.POST)
        formset = OTBookingProcedureFormSet(request.POST)

        if form.is_valid() and formset.is_valid():        
            booking = form.save(commit=False)
            booking.invoice = invoice
            booking.save()

            formset.instance = booking
            formset.save()

            for f in formset:
                print("  -", f.cleaned_data)
            generate_ot_bills(booking)
            invoice.update_totals()
            invoice.save()

            return redirect('billing:invoice_detail', invoice_id=invoice.id)

        else:           
            print("FORM errors:", form.errors)
            print("FORMSET errors:", formset.errors)
            print("Management form:", formset.management_form.errors)

    else:       
        form = OTBookingForm()
        formset = OTBookingProcedureFormSet()    

    return render(request, 'billing/add_ot_bill_new.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice
    })





@login_required
def emergency_visit_create(request):
    if request.method == 'POST':
        form = EmergencyVisitForm(request.POST)
        if form.is_valid():
            emergency_visit = form.save(commit=False)
            emergency_visit.status = 'Emergency-Service'
            patient = emergency_visit.patient

	    #Create MedicalRecord for the emergency visit
            medical_record = MedicalRecord.objects.create(
                patient=patient,
                doctor=emergency_visit.treated_by,
                diagnosis = 'Emergency Patient',
                treatment_plan ="Under observation"              

            )


	   # Create BillingInvoice
            invoice = BillingInvoice.objects.create(
                patient=patient,
                medical_record=medical_record,
                invoice_type='Emergency',
                patient_type='Emergency',
                status='Unpaid',
            )


            # Link invoice + medical record to emergency visit
            emergency_visit.invoice = invoice
            emergency_visit.medical_record = medical_record  # if model has this FK
            emergency_visit.save()

            return redirect('billing:ipd_invoice_list')
    else:
        form = EmergencyVisitForm()
    
    return render(request, 'billing/emergency_visit.html', {'form': form})




from .models import EmergencyVisit

@login_required
def emergency_visit_edit(request, visit_id):
    visit = get_object_or_404(EmergencyVisit, id=visit_id)

    if request.method == 'POST':
        form = EmergencyVisitForm(request.POST, instance=visit)
        if form.is_valid():
            with transaction.atomic():
                visit = form.save(commit=False)
                visit.save()
                # Optionally update related invoice or medical record if needed
                messages.success(request, f"Emergency visit for {visit.patient.name} updated.")
                return redirect('billing:emergency_visit_list')
    else:
        form = EmergencyVisitForm(instance=visit)
    return render(request, 'billing/emergency_visit.html', {'form': form, 'visit': visit})




@login_required
def emergency_visit_list(request):
    visits = EmergencyVisit.objects.select_related(
        'patient', 'treated_by', 'invoice', 'assigned_bed'
    ).order_by('-visit_time')

    query = request.GET.get('q')
    if query:
        visits = visits.filter(
            Q(patient__name__icontains=query) |
            Q(patient__phone__icontains=query) |
            Q(invoice__id__icontains=query)
        )

    paginator = Paginator(visits, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'billing/emergency_visit_list.html', {
        'page_obj': page_obj,
        'query': query
    })




@login_required
def doctor_service_rate_list(request):
    user = request.user
    rates = DoctorServiceRate.objects.select_related('doctor').order_by('-updated_at')
    doctor = getattr(user, 'doctor', None)
    if doctor and not user.is_staff:
        rates = rates.filter(doctor=doctor)
    q = request.GET.get('q', '').strip()
    if q:
        rates = rates.filter(
            Q(service_type__icontains=q) |
            Q(surgery_type__icontains=q) |
            Q(doctor__name__icontains=q)
        )

    paginator = Paginator(rates, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'rates': rates,
        'page_obj':page_obj,
        'q': q
    }
    return render(request, 'billing/doctor_service_rate_list.html', context)



def doctor_service_rate_create(request):
    if request.method == 'POST':
        form = DoctorServiceRateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('billing:doctor_service_rate_list')
    else:
        form = DoctorServiceRateForm()
    return render(request, 'billing/doctor_service_rate_form.html', {'form': form})


def doctor_service_rate_update(request,service_id):
    service_instance = get_object_or_404(DoctorServiceRate,id=service_id)
    if request.method == 'POST':
        form = DoctorServiceRateForm(request.POST,instance = service_instance)
        if form.is_valid():
            form.save()
            return redirect('billing:doctor_service_rate_list')
    else:
        form = DoctorServiceRateForm(instance = service_instance)
    return render(request, 'billing/doctor_service_rate_form.html', {'form': form,'service_instance':service_instance})


########################## referal/commision ##################################

class ReferralCommissionRuleListView(ListView):
    model = ReferralCommissionRule
    template_name = 'referrals/referral_rule_list.html'
    context_object_name = 'rules'
    ordering = ['referral_source', 'service_type']

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset().select_related('referral_source')
        doctor = getattr(user, 'doctor', None)
        if doctor and not user.is_staff:
            qs = qs.filter(referrer_doctor=doctor)   
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(referrer_doctor__name__icontains=q) |
                Q(service_type__icontains=q)            )

        return qs



class ReferralCommissionRuleCreateView(CreateView):
    model = ReferralCommissionRule
    form_class = ReferralCommissionRuleForm
    template_name = 'referrals/referral_rule_form.html'
    success_url = reverse_lazy('billing:referral_rule_list')


class ReferralCommissionRuleUpdateView(UpdateView):
    model = ReferralCommissionRule
    form_class = ReferralCommissionRuleForm
    template_name = 'referrals/referral_rule_form.html'
    success_url = reverse_lazy('billing:referral_rule_list')



class ReferralSourceListView(LoginRequiredMixin, ListView):
    model = ReferralSource
    template_name = "referrals/referral_source_list.html"
    context_object_name = "referrals"
    paginate_by = 20
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset().select_related('internal_doctor')
        q = self.request.GET.get('q', '').strip()
        
        if q:
            qs = qs.filter(
                Q(internal_doctor__name__icontains=q) |
                Q(agent_name__icontains=q) |
                Q(hospital_name__icontains=q) |
                Q(external_name__icontains=q)
            )        

        source_type = self.request.GET.get("source_type")
        if source_type:
            qs = qs.filter(source_type=source_type)

        return qs



def referral_source_detail(request, pk):
    referral = get_object_or_404(ReferralSource, pk=pk)
    data = {}
    if referral.referral_type == 'internal_doctor':
        data['Doctor'] = referral.internal_doctor.name if referral.internal_doctor else None
    elif referral.referral_type == 'external_doctor':
        data['External Name'] = referral.external_name
        data['External Contact'] = referral.external_contact
    elif referral.referral_type == 'agent':
        data['Agent Name'] = referral.agent_name
        data['Agent Contact'] = referral.agent_phone
    elif referral.referral_type == 'hospital':
        data['Hospital Name'] = referral.hospital_name
        data['Hospital Contact'] = referral.hospital_contact
    elif referral.referral_type in ['self', 'other']:
        data['Type'] = referral.get_referral_type_display()

    context = {
        'referral': referral,
        'data': data
    }
    return render(request, 'referrals/referral_source_detail.html', context)



class ReferralSourceCreateView(LoginRequiredMixin, CreateView):
    model = ReferralSource
    form_class = ReferralSourceForm
    template_name = "referrals/referral_source_form.html"
    success_url = reverse_lazy('billing:referral_source_list')

    def form_valid(self, form):  
        form.instance.user = self.request.user
        return super().form_valid(form)


class ReferralSourceUpdateView(LoginRequiredMixin, UpdateView):
    model = ReferralSource
    form_class = ReferralSourceForm
    template_name = "referrals/referral_source_update_form.html"
    success_url = reverse_lazy('billing:referral_source_list')

    def get_queryset(self):     
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            return qs.filter(user=self.request.user)
        return qs




@login_required
def referral_report(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    stakeholder_type = request.GET.get('stakeholder_type')  # internal_doctor, external_doctor, agent, hospital
    stakeholder_name = request.GET.get('stakeholder_name')  # actual name/id filter

    referrals = ReferralCommissionTransaction.objects.select_related(
        'referral_source', 'invoice'
    ).order_by('-created_at')

    if start_date:
        referrals = referrals.filter(created_at__date__gte=parse_date(start_date))
    if end_date:
        referrals = referrals.filter(created_at__date__lte=parse_date(end_date))


    if stakeholder_type and stakeholder_name:
        if stakeholder_type == 'internal_doctor':
            referrals = referrals.filter(referral_source__internal_doctor_id=stakeholder_name)
        elif stakeholder_type == 'external_doctor':
            referrals = referrals.filter(referral_source__external_name__icontains=stakeholder_name)
        elif stakeholder_type == 'agent':
            referrals = referrals.filter(referral_source__agent_name__icontains=stakeholder_name)
        elif stakeholder_type == 'hospital':
            referrals = referrals.filter(referral_source__hospital_name__icontains=stakeholder_name)

    summary = referrals.aggregate(
        total_service_amount=Sum('service_amount') or 0,
        total_commission=Sum('commission_amount') or 0,
        total_paid=Sum('commission_amount', filter=Q(status='Paid')) or 0,
    )
    summary['remaining'] = (summary['total_commission'] or 0) - (summary['total_paid'] or 0)

    context = {
        'referrals': referrals,
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
        'stakeholder_type': stakeholder_type,
        'stakeholder_name': stakeholder_name,
    }
    return render(request, 'referrals/referral_report.html', context)




from datetime import datetime,timedelta

@login_required
def stakeholder_referral_report(request): 
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
    stakeholder_type = request.GET.get('stakeholder_type')  # internal_doctor, external_doctor, agent, hospital
    stakeholder_id = request.GET.get('stakeholder_id')  # doctor id, agent name, etc.

    referrals = ReferralCommissionTransaction.objects.select_related(
        'referral_source', 'invoice'
    ).order_by('-created_at')
 
    referrals = referrals.filter(created_at__range=(start_date,end_date))   
    if stakeholder_type and not stakeholder_id:
        referrals = ReferralCommissionTransaction.objects.none()
    else:
        if stakeholder_id:
            if stakeholder_type == 'internal_doctor':
                try:
                    stakeholder_id = int(stakeholder_id)
                except ValueError:
                    stakeholder_id = None

                if stakeholder_id:
                    referrals = referrals.filter(
                        referral_source__internal_doctor_id=stakeholder_id
                    )

            elif stakeholder_type == 'external_doctor':
                referrals = referrals.filter(
                    referral_source__external_name=stakeholder_id
                )

            elif stakeholder_type == 'agent':
                referrals = referrals.filter(
                    referral_source__agent_name=stakeholder_id
                )

            elif stakeholder_type == 'hospital':
                referrals = referrals.filter(
                    referral_source__hospital_name=stakeholder_id
                )


    summary = referrals.aggregate(
        total_service_amount=Sum('service_amount'),
        total_commission=Sum('commission_amount'),
        total_paid=Sum('commission_amount', filter=Q(status='Paid')),
    )

    total_service_amount = summary['total_service_amount'] or 0
    total_commission = summary['total_commission'] or 0
    total_paid = summary['total_paid'] or 0
    summary['total_service_amount'] = total_service_amount
    summary['total_commission'] = total_commission
    summary['total_paid'] = total_paid
    summary['remaining'] = total_commission - total_paid

    internal_doctors = ReferralSource.objects.filter(referral_type='internal_doctor').values_list('internal_doctor__id', 'internal_doctor__name').distinct()
    external_doctors = ReferralSource.objects.filter(referral_type='external_doctor').values_list('external_name', flat=True).distinct()
    agents = ReferralSource.objects.filter(referral_type='agent').values_list('agent_name', flat=True).distinct()
    hospitals = ReferralSource.objects.filter(referral_type='hospital').values_list('hospital_name', flat=True).distinct()


    context = {
        'referrals': referrals,
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
        'stakeholder_type': stakeholder_type,
        'stakeholder_id': stakeholder_id,
        'internal_doctors': internal_doctors,
        'agents': agents,
        'hospitals': hospitals,
        'external_doctors': external_doctors,
    }
    return render(request, 'referrals/stakeholder_referral_report.html', context)




from decimal import Decimal
from django.db import transaction
from finance.models import AllExpenses  
from accounting.models import FiscalYear,JournalEntry,JournalEntryLine,Account


@login_required
def create_referral_payment(request):   
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    referral_sources = ReferralSource.objects.all()
    selected_referral_source = None

    pending_referrals = ReferralCommissionTransaction.objects.filter(
        status="Pending"
    ).order_by('referral_source', 'created_at')

    referral_source_id = request.GET.get("referral_source") or request.POST.get("referral_source")
    if referral_source_id:
        selected_referral_source = get_object_or_404(ReferralSource, id=referral_source_id)
        pending_referrals = ReferralCommissionTransaction.objects.filter(
            referral_source=selected_referral_source,
            status="Pending"
        ).order_by('created_at')

    if request.method == "POST":
        payment_mode = request.POST.get("payment_mode")
        selected_referrals = request.POST.getlist("referrals")
        amount_paid = request.POST.get("amount_paid") or "0"
        notes = request.POST.get("notes")
     
        try:
            amount_paid = Decimal(amount_paid.replace(',', ''))
        except:
            amount_paid = Decimal("0.00")
     
        if referral_source_id:
            selected_referral_source = get_object_or_404(
                ReferralSource, id=referral_source_id
            )
            pending_referrals = pending_referrals.filter(
                referral_source=selected_referral_source
            )
  
        if selected_referrals:
            with transaction.atomic():       
                payment = ReferralPayment.objects.create(
                    referral_source=selected_referral_source,
                    amount_paid=amount_paid,
                    payment_mode=payment_mode,
                    notes=notes
                )
                referrals_to_pay = pending_referrals.filter(
                    id__in=selected_referrals
                )        
                payment.applied_referrals.set(referrals_to_pay)          
                referrals_to_pay.update(status="Paid")             
                referrals_to_pay = ReferralCommissionTransaction.objects.filter(
                    id__in=selected_referrals
                )              
              
                for ref_tx in referrals_to_pay:
                    commission_amount = Decimal(ref_tx.commission_amount)
                    from accounting.utils import create_referral_commission_payment_journal
                    create_referral_commission_payment_journal(
                        referral_transaction = ref_tx,
                        payment_amount=Decimal(commission_amount),        
                        created_by=request.user
                    )                   

                payment.save()

            return redirect("billing:referral_payment_list")
    total_due = sum(r.commission_amount for r in pending_referrals)

    return render(request, 'referrals/create_referral_payment.html', {
        'referral_sources': referral_sources,
        'selected_referral_source': selected_referral_source,
        'pending_referrals': pending_referrals,
        'total_due': total_due
    })



@login_required
def doctor_service_log_list(request): 
    query = request.GET.get('q', '').strip()
    doctor_id = request.GET.get('doctor', '')
    paid_status = request.GET.get('paid', '') 

    logs = DoctorServiceLog.objects.select_related(
        'doctor', 'patient', 'invoice'
    ).order_by('-service_date')

    if doctor_id:
        logs = logs.filter(doctor_id=doctor_id)
    if paid_status == 'paid':
        logs = logs.filter(is_paid=True)
    elif paid_status == 'unpaid':
        logs = logs.filter(is_paid=False)

    if query:
        logs = logs.filter(
            Q(patient__name__icontains=query) |
            Q(service_type__icontains=query) |
            Q(invoice__id__icontains=query)
        )

    doctors = Doctor.objects.all()  

    context = {
        'logs': logs,
        'query': query,
        'doctors': doctors,
        'selected_doctor': doctor_id,
        'paid_status': paid_status,
    }
    return render(request, 'doctor/doctor_service_log_list.html', context)


@login_required
def create_doctor_service_log_payment(request):
    fiscal_year = FiscalYear.get_active()
    if not fiscal_year:
        raise ValueError("No active fiscal year found.")

    pending_logs = DoctorServiceLog.objects.filter(is_paid=False).order_by("created_at")
    selected_service_logs = None

    if request.method == "POST":
        payment_mode = request.POST.get("payment_mode")
        selected_service_logs = request.POST.getlist("service_logs")
        notes = request.POST.get("notes")

        if not selected_service_logs:
            messages.error(request, "No service logs selected.")
            return redirect(request.path)

        logs = pending_logs.filter(id__in=selected_service_logs)

        logs_by_doctor = {}
        for log in logs:
            logs_by_doctor.setdefault(log.doctor_id, []).append(log)

        from accounting.utils import create_doctor_service_payment_journal
        with transaction.atomic():
            
            for doctor_id, doctor_logs in logs_by_doctor.items():
                total_amount = sum(Decimal(l.doctor_share) for l in doctor_logs)
                doctor = doctor_logs[0].doctor
                payment = DoctorPayment.objects.create(
                    doctor=doctor,
                    total_paid_amount=total_amount,
                    payment_method=payment_mode,
                    remarks=notes,
                )
                payment.applied_service_logs.set(doctor_logs)

                for log in doctor_logs:
                    log.is_paid = True
                    log.save()
 
                create_doctor_service_payment_journal(
                    doctor_payment=payment,
                    payment_amount=total_amount,
                    created_by=request.user
                )

        return redirect("workspace:staff_dashboard")

    total_due = sum(log.doctor_share for log in pending_logs)

    return render(request, 'doctor/create_doctor_service_log_payment.html', {
        'pending_service_logs': pending_logs,
        'selected_service_logs': selected_service_logs,
        'total_due': total_due
    })



@login_required
def referral_payment_list(request):
    payments = ReferralPayment.objects.select_related('referral_source').prefetch_related('applied_referrals').order_by('-payment_date')
    context = {'payments': payments }
    return render(request, 'referrals/referral_payment_list.html', context)





# payment by patient ########################################################
@login_required
def add_payment(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.patient_type = invoice.patient_type
            payment.save()       
        return redirect('billing:invoice_detail', invoice_id=invoice.id)
    else:
        form = PaymentForm(initial={'invoice':invoice})

    return render(request, 'billing/add_payment.html', {
        'form': form,
        'invoice': invoice
    })


from django.db.models import Q

@login_required
def payment_landing(request):
    query = request.GET.get("q")
    invoices = BillingInvoice.objects.none()  # default empty queryset

    if query:
        invoices = BillingInvoice.objects.filter(
            Q(patient__name__icontains=query) |
            Q(patient__phone__icontains=query) |
            Q(patient__patient_id__icontains=query) |
            Q(id__icontains=query)  # invoice ID
        ).order_by("-id")

    context = {
        "invoices": invoices,
        "query": query
    }
    return render(request, "billing/payments/payment_landing.html", context)



# payment to doctor ########################################################



@login_required
def add_doctor_payment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    financials = get_doctor_financials(doctor.id)
    total_due_amount = financials.get('total_due', 0)

    if total_due_amount <= 0:
        messages.warning(request, "This doctor has no due payment.")
        return redirect('appointments:doctor_list')

    if request.method == 'POST':
        form = DoctorPaymentForm(request.POST)        
        if form.is_valid():
            payment_amount = form.cleaned_data['total_amount_paid']

            if payment_amount > Decimal(total_due_amount):
                messages.error(request, f"Payment cannot exceed due amount ({total_due_amount}).")
                return redirect(request.path)
            
            with transaction.atomic():
                payment = form.save(commit=False)
                payment.user = request.user
                payment.doctor = doctor
                payment.save()

                from accounting.utils import create_doctor_service_payment_journal
                create_doctor_service_payment_journal(
                    doctor_payment=payment,
                    payment_amount=payment_amount,
                    created_by=request.user)

            messages.success(request, "Doctor payment recorded successfully.")
            return redirect('finance:shareholder_dashboard')
        messages.error(request, "Invalid form submission.")
    else:
        form = DoctorPaymentForm()
    return render(request, 'billing/add_doctor_payment.html', {
        'form': form,
        'doctor': doctor,
        'total_due': total_due_amount
    })




@login_required
def doctor_payment_summary(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)  
    financials = get_doctor_financials(doctor.id)
   
    recent_service_payments = DoctorPayment.objects.filter(doctor=doctor).order_by('-payment_date')[:10]
    recent_service_logs = DoctorServiceLog.objects.filter(doctor=doctor).order_by('-service_date')

    pending_referrals = ReferralCommissionTransaction.objects.filter(
        invoice__medical_record__doctor_id=doctor.id, status='Pending'
    ).order_by('-created_at')

    recent_referral_payments = ReferralPayment.objects.filter(
        applied_referrals__invoice__medical_record__doctor_id=doctor.id
    ).distinct().order_by('-payment_date')[:10]

    context = {
        'doctor': doctor,
        'recent_service_payments': recent_service_payments,
        'recent_service_logs': recent_service_logs,
        'pending_referrals': pending_referrals,
        'recent_referral_payments': recent_referral_payments,
        **financials,
    }
    
    return render(request, 'billing/doctor_payment_summary.html', context)



def generate_invoice_qr(invoice):  
    invoice_url = f"http://localhost/billing/finalize_invoice/{invoice.id}/"

    qr = qrcode.make(invoice_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return qr_base64





def calculate_billed_days(assigned_at, released_at):
    if not assigned_at:
        return 0
    if not released_at:
        released_at = now()
    assigned_at = localtime(assigned_at)
    released_at = localtime(released_at)

    days = (released_at.date() - assigned_at.date()).days
    return max(days + 1, 1)




from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils.timezone import now as tz_now, localtime, make_aware,is_naive
from billing.models import BillingInvoice, Payment, MedicineBill, LabTestBill, WardBill
from patients.models import PatientAdmission
from facilities.models import BedAssignmentHistory






def calculate_instant_wardbill(invoice=None, admission=None, emergency_visit=None):
    total_running_bill = Decimal('0.00')
    current_time = tz_now()
    latest_bed_history = None

    if emergency_visit:
        latest_bed_history = BedAssignmentHistory.objects.filter(
            emergency_visit=emergency_visit,
            released_at__isnull=True
        ).order_by('-assigned_at').first()       

    if not latest_bed_history and admission:
        latest_bed_history = admission.bed_assignments.filter(
            released_at__isnull=True
        ).order_by('-assigned_at').first()       

    if not latest_bed_history and invoice and getattr(invoice, 'patient', None):
        latest_bed_history = invoice.patient.bed_histories.filter(
            released_at__isnull=True
        ).order_by('-assigned_at').first()      

    if not latest_bed_history or not latest_bed_history.bed:       
        return total_running_bill

    bed = latest_bed_history.bed
    assigned_at = latest_bed_history.assigned_at 

    if is_naive(assigned_at):
        assigned_at = make_aware(assigned_at)

    duration_seconds = (current_time - assigned_at).total_seconds()
    duration_hours = Decimal(duration_seconds / 3600)
 
    if getattr(bed, 'hourly_charge', None) and duration_hours <= 24:
        total_running_bill = (duration_hours * bed.get_effective_hourly_charge()).quantize(Decimal('0.01'))

    elif getattr(bed, 'hourly_charge', None) and duration_hours > 24:
        hourly_bill = Decimal(24) * bed.get_effective_hourly_charge()
        remaining_days = max(1, int((duration_hours - 24) // 24))
        daily_bill = Decimal(remaining_days) * bed.get_effective_daily_charge()
        total_running_bill = (hourly_bill + daily_bill).quantize(Decimal('0.01')) 
    else:
        num_days = max(1, (current_time.date() - assigned_at.date()).days)
        total_running_bill = (Decimal(num_days) * bed.get_effective_daily_charge()).quantize(Decimal('0.01'))
    return total_running_bill



@login_required
def finalize_invoice(request, invoice_id):
    invoice = get_object_or_404(BillingInvoice, id=invoice_id)
    qr_code = generate_invoice_qr(invoice)
    hospital = Location.objects.first()
    grand_total_bill = Decimal(0.0)
    grand_total_paid=Decimal(0.0)
    last_assignment = None

    consultation_subtotal = invoice.consultation_bills.aggregate(total=Sum('consultation_fee'))['total'] or Decimal('0.00')
    lab_subtotal = invoice.lab_test_bills.aggregate(total=Sum('test_fee'))['total'] or Decimal('0.00')
    medicine_subtotal = invoice.medicine_bills.aggregate(
        total=Sum(ExpressionWrapper(F('quantity') * F('price_per_unit'), output_field=DecimalField()))
    )['total'] or Decimal('0.00')
    ward_subtotal = invoice.ward_bills.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    ot_subtotal = invoice.ot_bills.aggregate(total=Sum('total_charge'))['total'] or Decimal('0.00')
    misc_subtotal = invoice.misc_bills.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    ward_running_bill = Decimal('0.00')
    grand_total_ward_bill = ward_subtotal
    admission = getattr(invoice, 'admission', None) if hasattr(invoice, 'admission') else None
    emergency = getattr(invoice, 'emergency_visit_invoice', None) if hasattr(invoice, 'emergency_visit_invoice') else None
      
    emergency_due = Decimal(0.0)
    if admission and hasattr(admission, 'emergency') and admission.emergency:
        emergency_to_admission = admission.emergency
        emergency_invoice = emergency_to_admission.invoice
        emergency_due = emergency_invoice.remaining_amount or Decimal("0.00")
    else:
        emergency_invoice = None
        emergency_due = Decimal("0.00")    
    grand_total_with_emergency = Decimal(0.0)
    grand_total_remaining_include_emergency=Decimal(0.0)



    if invoice.is_locked:
        ward_running_bill = Decimal('0.00')
    else:
        try:
            ward_running_bill = calculate_instant_wardbill(
                invoice=invoice,
                admission=admission if admission else None,
                emergency_visit=emergency if emergency else None
            )
        except Exception:
            ward_running_bill = Decimal('0.00')
   
    if invoice.is_locked:
        grand_total_bill = invoice.total_amount or Decimal("0.00")
    else:
        grand_total_bill = (invoice.total_amount or 0) + ward_running_bill

    grand_total_paid = invoice.total_paid or Decimal('0.00')
    grand_total_remaining = (grand_total_bill - grand_total_paid).quantize(Decimal('0.01'))

    grand_total_with_emergency = grand_total_bill + emergency_due
    grand_total_remaining_include_emergency = (
        grand_total_with_emergency - grand_total_paid
    ).quantize(Decimal("0.01"))
 
    if request.method == 'POST' and 'lock_invoice' in request.POST:
        if invoice.is_locked:
            messages.info(request, "Invoice is already locked.")
            return redirect('billing:finalize_invoice', invoice_id=invoice.id)

        with transaction.atomic():
            if not invoice.is_locked:
                if invoice.invoice_type in ['IPD', 'Emergency']:               
                    last_assignment = BedAssignmentHistory.objects.filter(
                        emergency_visit=emergency if emergency else None,
                        patient_admission =admission if admission else None,
                        released_at__isnull=True
                    ).order_by('-assigned_at').first()
  
                if not last_assignment:
                    last_assignment = BedAssignmentHistory.objects.filter(
                        patient=invoice.patient,
                        released_at__isnull=True
                    ).order_by('-assigned_at').first()

                if last_assignment:
                    release_time = tz_now()
                    last_assignment.released_at = release_time
                    last_assignment.save()

                    bed = last_assignment.bed
                    assigned_dt = last_assignment.assigned_at
                    released_dt = last_assignment.released_at

                    if is_naive(assigned_dt):
                        assigned_dt = make_aware(assigned_dt)
                    if is_naive(released_dt):
                        released_dt = make_aware(released_dt)                     
                  
                    duration_seconds = (released_dt - assigned_dt).total_seconds()
                    duration_hours = Decimal(duration_seconds / 3600)

                    if getattr(bed, 'hourly_charge', None) and duration_hours <= 24:
                        total_bill = (duration_hours * bed.get_effective_hourly_charge()).quantize(Decimal('0.01'))
                        days_stayed = None
                    elif getattr(bed, 'hourly_charge', None) and duration_hours > 24:
                        hourly_bill = Decimal(24) * bed.get_effective_hourly_charge()
                        remaining_days = max(1, int((duration_hours - 24) // 24))
                        daily_bill = Decimal(remaining_days) * bed.get_effective_daily_charge()
                        total_bill = (hourly_bill + daily_bill).quantize(Decimal('0.01'))
                        days_stayed = remaining_days
                    else:
                        days_stayed = max(1, (released_dt.date() - assigned_dt.date()).days)
                        total_bill = (Decimal(days_stayed) * bed.get_effective_daily_charge()).quantize(Decimal('0.01'))
                    
                    ward_bill = None
                    if admission:
                        ward_bill = WardBill.objects.filter(
                            invoice=invoice,
                            bed=bed,
                            patient_admission=admission
                        ).order_by('-id').first()
                    elif emergency:
                        ward_bill = WardBill.objects.filter(
                            invoice=invoice,
                            bed=bed,
                            patient_emergency=emergency
                        ).order_by('-id').first()
                    else:
                        ward_bill = None

                    if not ward_bill or ward_bill.released_at:
                        ward_bill = WardBill.objects.create(
                            invoice=invoice,
                            patient_admission=admission if admission else None,
                            bed=bed,
                            assigned_at=assigned_dt,
                            released_at=released_dt,
                            days_stayed=days_stayed,
                            total_bill=total_bill
                        )
                    else:    
                        ward_bill.assigned_at = assigned_dt
                        ward_bill.released_at = released_dt
                        ward_bill.days_stayed = days_stayed
                        ward_bill.total_bill = total_bill
                        ward_bill.save()

                    bed.is_occupied = False
                    bed.save(update_fields=['is_occupied'])
                    room = getattr(bed, 'room', None)
                    ward = getattr(bed, 'ward', None)                  
                    if room and not room.room_beds.filter(is_occupied=True).exists():
                        room.is_occupied = False
                        room.save(update_fields=['is_occupied'])
                    if ward and not ward.ward_rooms.filter(room_beds__is_occupied=True).exists():
                        ward.is_occupied = False
                        ward.save(update_fields=['is_occupied'])

            invoice.is_locked = True
            invoice.locked_at = tz_now()

            invoice.update_total_wardbill()
            invoice.update_totals()
            invoice.save()
           
            if invoice.is_locked:
                grand_total_bill = invoice.total_amount or Decimal("0.00")
            else:
                grand_total_bill = (invoice.total_amount or 0) + ward_running_bill           
                               
            grand_total_paid = invoice.total_paid or Decimal('0.00')
            grand_total_remaining = (grand_total_bill - grand_total_paid).quantize(Decimal('0.01'))
            grand_total_with_emergency = grand_total_bill + emergency_due
            grand_total_remaining_include_emergency = (
                grand_total_with_emergency - grand_total_paid
            ).quantize(Decimal("0.01"))
 
            from accounting.utils import create_journal_entry
            from billing.utils import create_referral_transactions_for_invoice

            bill_items = invoice.get_all_bill_items()
            breakdown_agg = {}
            for item in bill_items:
                rtype = item.get("revenue_type", "Other")
                
                if rtype not in breakdown_agg:
                    breakdown_agg[rtype] = {
                        "amount_received": Decimal("0.00"),
                        "net_amount": Decimal("0.00"),
                        "vat_amount": Decimal("0.00"),
                        "ait_amount": Decimal("0.00"),
                    }
                
                breakdown_agg[rtype]["amount_received"] += Decimal (item.get("total_amount", 0))
                breakdown_agg[rtype]["net_amount"] += Decimal(item.get("net_amount", 0))
                breakdown_agg[rtype]["vat_amount"] += Decimal(item.get("vat_amount", 0))
                breakdown_agg[rtype]["ait_amount"] += Decimal(item.get("ait_amount", 0))

            breakdown_list = []
            for rtype, values in breakdown_agg.items():
                breakdown_list.append({
                    "revenue_type": rtype,
                    "amount_received": values["amount_received"],
                    "net_amount": values["net_amount"],
                    "vat_amount": values["vat_amount"],
                    "ait_amount": values["ait_amount"],
                })
       
            latest_payment = invoice.payments.order_by("-id").first() 

            if latest_payment and breakdown_list:
                create_journal_entry(
                    payment=latest_payment,
                    breakdown=breakdown_list,
                    description=f"Final {invoice.invoice_type} revenue for {invoice.patient.name}",
                    created_by=request.user,
                    entry_type="REVENUE_RECOGNITION"
                )
            create_referral_transactions_for_invoice(invoice)
            messages.success(request, "Invoice locked successfully. Collect any remaining due payment.")
            return redirect('billing:finalize_invoice', invoice_id=invoice.id)

    context = {
        'invoice': invoice,
        'consultation_subtotal': consultation_subtotal,
        'lab_subtotal': lab_subtotal,
        'medicine_subtotal': medicine_subtotal,
        'ot_subtotal': ot_subtotal,
        'misc_subtotal': misc_subtotal,
        'qr_code': qr_code,
        'hospital': hospital,
        'ward_subtotal': ward_subtotal,
        'ward_running_bill': ward_running_bill,
        'grand_total_ward_bill': grand_total_ward_bill,
        'grand_total_bill': grand_total_bill,
        'grand_total_paid': grand_total_paid,
        'grand_total_remaining': grand_total_remaining,
        'grand_total_with_emergency':grand_total_with_emergency,
        'grand_total_remaining_include_emergency': grand_total_remaining_include_emergency,
        'emergency_due':emergency_due
    }
    return render(request, 'billing/finalize_invoice.html', context)






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

    ward_subtotal= invoice.ward_bills.aggregate(
            total=Sum('total_bill')
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
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(f"{hospital.city}-{hospital.postal_code}", styles['Center']))
    elements.append(Paragraph(f" {hospital.company.website}", styles['Center']))
    elements.append(Spacer(1, 10))


    # Provisional Bill Title
    elements.append(Paragraph("🧾 Final Bill", styles['Heading']))

    triger_total_calculation = invoice.update_total_wardbill()

     # Patient Information
    admission_no =None
    ward =None
    bed_room=None
    if invoice.invoice_type == 'OPD':
        patient_id = invoice.patient.patient_id
        patient_name = invoice.patient.name
        doctor = invoice.patient.patient_appointments.first().doctor
        invoice_no = invoice.invoice_id
    elif invoice.invoice_type == 'IPD':
        patient_id = invoice.admission.patient.patient_id
        patient_name = invoice.admission.patient.name
        doctor = invoice.admission.admitting_doctor
        admission_no = invoice.admission.admission_code
        ward = invoice.admission.assigned_ward.name
        bed_room = f"{invoice.admission.assigned_bed.bed_number} / {invoice.admission.assigned_room.number}"
    else:
        patient_id = invoice.patient
        patient_name = invoice.patient.name
        doctor = invoice.emergergency_visit_invoices.treated_by if invoice.emergergency_visit_invoices\
        else invoice.external_lab_visit_invoices.doctor.name

    admission = None
    ward_running_bill = 0
    grand_total_ward_bill = 0
    grand_total_bill=0
    grand_total_paid=0
    grand_total_remaining=0

    if invoice.invoice_type == 'IPD' and invoice.admission:
        admission = invoice.admission  # directly from the invoice FK
        ward_running_bill = calculate_instant_wardbill(admission)
        grand_total_ward_bill = ward_running_bill + ward_subtotal

        grand_total_bill = invoice.total_amount + ward_running_bill
        grand_total_paid = invoice.total_paid
        grand_total_remaining = grand_total_bill - grand_total_paid
    else:
        grand_total_bill = invoice.total_amount
        grand_total_paid = invoice.total_paid
        grand_total_remaining = grand_total_bill - grand_total_paid 

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
  
    col_widths = [80, 170, 100, 80]

    if invoice.consultation_bills.exists():
        data = []     
        data.append([
            Paragraph("<b>Consultation Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])
   
        data.append(["Appointment", "Doctor", "Consultation Date", "Consultation Fee"])

        for bill in invoice.consultation_bills.all():
            data.append([
                bill.appointment.appointment_code if bill.appointment else None,
                str(bill.doctor),
                bill.consultation_date.strftime("%Y-%m-%d"),
                f"{bill.consultation_fee:.2f}"
            ])

        data.append(["", "","Subtotal", f"{consultation_subtotal:.2f}"])

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
    ward_subtotal =  invoice.ward_bills.aggregate(
            total=Sum('total_bill')
        )['total'] or 0
    
    print(f'ward subtotal={ward_subtotal}')
    if invoice.ward_bills.exists():
       
        data = []     
        data.append([
            Paragraph("<b>Ward Bills</b>", styles['SubHeading']),
            '', '', '' 
        ])
   
        data.append( ["Ward", "Bed/Room", "Charge/day", "Days stayed", "Total"])      

        for bill in invoice.ward_bills.all():
            data.append([
                bill.ward.name,
                f'{bill.bed.bed_number}|{bill.room.number}',
                bill.charge_per_day,              
                bill.days_stayed,
                bill.total_bill,
            ])        

        data.append(["", "", "", "Subtotal", f"{ward_subtotal:.2f}"])
        data.append(["", "", "", "Unbilled (Running)", f"{ward_running_bill:.2f}"])
        data.append(["", "", "", "Total Ward Bill", f"{grand_total_ward_bill:.2f}"])

        ward_table = Table(data, colWidths=col_widths)        

        ward_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (-1, 0)),  # Title row span
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightblue),  # Header row
            
            # Highlight subtotal, unbilled, total rows
            ('BACKGROUND', (0, -3), (-1, -1), colors.whitesmoke),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),

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
            Paragraph("<b>Lab Test Bills</b>", styles['SubHeading']),
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
    <b>Grand Total:</b> {grand_total_bill:.2f} &nbsp;&nbsp; || &nbsp;&nbsp; 
    <b>Total Paid:</b> {grand_total_paid:.2f} &nbsp;&nbsp; || &nbsp;&nbsp;
    <b>Total Due:</b> {grand_total_remaining:.2f}<br/>       
    """
    
    elements.append(Paragraph(grand_total_text, styles['Normal']))
    elements.append(Spacer(1, 20))

    grand_total_due_text = f"""          
    <b>Total Due Bill in Words:</b> {num2words(grand_total_remaining, to='currency', lang='en_IN')}
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
