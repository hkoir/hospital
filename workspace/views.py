
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import date
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.db.models import Count, Sum, OuterRef, Subquery, DecimalField,Value,F,Q
from django.db.models.functions import Coalesce

from billing.models import ConsultationBill,MedicineBill,LabTestBill,OTBill,MiscellaneousBill,WardBill
from billing.models import EmergencyVisit,BillingInvoice,Payment
from facilities.models import Bed
from finance.models import AllExpenses
from appointments.models import Appointment
from medical_records.models import MedicalRecord,Prescription
from patients.models import PatientAdmission,Patient
from core.models import Doctor
from messaging.models import Notification
from django.core.paginator import Paginator


@login_required
def doctor_dashboard(request):
    doctor = Doctor.objects.filter(user=request.user).first()
 
    appointments = Appointment.objects.filter(
        doctor=doctor,
        #date=date.today()
    ).select_related("patient").order_by("id")

    today_appointments = appointments.count()
    pending_queue = appointments.filter(status="Pending").count()
    consulted_today = appointments.filter(status="Prescription-Given").count()

    admitted_patients = PatientAdmission.objects.filter(
        admitting_doctor=doctor,
        discharge_date__isnull=True
    ).count()

    notifications = Notification.objects.filter(
        doctor=doctor
    ).order_by("-created_at")

    paginator = Paginator(notifications, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    paginator2 = Paginator(appointments, 10) 
    page_number2 = request.GET.get('page2')
    page_obj2 = paginator2.get_page(page_number2)


    context = {
        "appointments": appointments,
        "today_appointments": today_appointments,
        "pending_queue": pending_queue,
        "consulted_today": consulted_today,
        "admitted_patients": admitted_patients,
        "notifications": notifications,
        "page_obj":page_obj,
        "page_obj2":page_obj2,
	"doctor":doctor
    }
    return render(request, "workspace/doctor_dashboard.html", context)






@login_required
def staff_dashboard(request):
    today = date.today()

    # Daily Stats
    registrations_today = Patient.objects.filter(created_at__date=today).count()
    appointments_today = Appointment.objects.filter(date=today).count()
    admissions_today = PatientAdmission.objects.filter(admission_date=today).count()
    emergency_today = EmergencyVisit.objects.filter(created_at__date=today).count()

    # Bed Status
    beds_available = Bed.objects.filter(is_occupied=False).count()
    beds_occupied = Bed.objects.filter(is_occupied=True).count()
    icu_free = Bed.objects.filter(is_occupied=False, ward__ward_type="ICU").count()

    # Pending Tasks
    pending_unassigned_beds = PatientAdmission.objects.filter(
        assigned_bed__isnull=True, discharge_date__isnull=True
    ).select_related("patient")

    pending_discharges = PatientAdmission.objects.filter(
        discharge_approved=True,
       discharge_date__isnull=True,
    ).select_related("patient")

    pending_unbilled = BillingInvoice.objects.filter(
        is_locked=False,
        admission__discharge_approved = True
    ).select_related("patient")

    pending_emergency = EmergencyVisit.objects.filter(
        discharge_approved=True,
	discharge_date__isnull=True,
    )

    context = {
        # KPIs
        "registrations_today": registrations_today,
        "appointments_today": appointments_today,
        "admissions_today": admissions_today,
        "emergency_today": emergency_today,

        # Beds
        "beds_available": beds_available,
        "beds_occupied": beds_occupied,
        "icu_free": icu_free,

        # Tasks
        "pending_unassigned_beds": pending_unassigned_beds,
        "pending_discharges": pending_discharges,
        "pending_unbilled": pending_unbilled,
        "pending_emergency": pending_emergency,
    }

    return render(request, "workspace/staff_dashboard.html", context)





def appointment_list(request):     
    appointments = Appointment.objects.none()
    doctors = Doctor.objects.all()  
    patients = Patient.objects.all()  
    doctor_appointment_counts = []

    if request.method == 'GET':       
        doctor_filter = request.GET.get("doctor")
        patient_filter = request.GET.get("patient") or request.GET.get("patient_id")
        date_filter = request.GET.get("date", "").strip()
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        today = timezone.now().date()    
        appointments = Appointment.objects.all()    
      
        # if request.user.role == 'doctor':
        #     doctor = Doctor.objects.filter(user = request.user).first()
        #     appointments = Appointment.objects.filter(doctor = doctor) 
    
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
    paginator = Paginator(appointments, 10) 
    page_number = request.GET.get('page')
    page_obj= paginator.get_page(page_number)

    return render(request, "workspace/appointment_list.html", {
        "appointments": appointments,
        "doctor_appointment_counts": doctor_appointment_counts, 
        'today': date.today(),
        'doctors': doctors,
        'patients': patients,
        'page_obj':page_obj
    })


from django.db.models import Sum, OuterRef, Subquery, DecimalField
from django.db.models.functions import Coalesce
from billing.models import BillingInvoice
from django.db.models import Value

@login_required
def management_dashboard(request):
    print(f'management dashboard started')
    today = timezone.now()
    
    revenue_today = Payment.objects.filter(created_at__date=date.today()).aggregate(
    total=Sum("amount_paid")
    )["total"] or 0
    revenue_month = Payment.objects.filter(
        created_at__year=today.year,
        created_at__month=today.month
    ).aggregate(total=Sum("amount_paid"))["total"] or 0


    expenses_month = AllExpenses.objects.filter(
        created_at__year=today.year,
        created_at__month=today.month
    ).aggregate(total=Sum("amount"))["total"] or 0
    
    profit_month = revenue_month - expenses_month
   
    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.filter(is_occupied=True).count()
    occupancy = round((occupied_beds / total_beds) * 100, 2) if total_beds else 0

    icu_beds = Bed.objects.filter(ward__ward_type="ICU").count()
    icu_occupied = Bed.objects.filter(ward__ward_type="ICU", is_occupied=True).count()
    icu_occupancy = round((icu_occupied / icu_beds) * 100, 2) if icu_beds else 0


    doctors = Doctor.objects.all()  
    query = request.GET.get('q', '').strip()
    if query:
           doctors = doctors.filter(
            Q(name__icontains=query) |
            Q(phone__icontains =query) |
            Q(user__phone_number__icontains =query))   

    doctor_performance = doctors.annotate(
        consultations=Count('doctor_appointments', distinct=True),
        consultation_revenue=Coalesce(
            Sum('doctor_appointments__consultation_fees__consultation_fee', output_field=DecimalField()),
            Value(0, output_field=DecimalField())
        )
    )



    revenue_breakdown = [] 
    consultation_revenue = ConsultationBill.objects.aggregate(
        total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField())
    )['total']
    revenue_breakdown.append(consultation_revenue) 
    lab_revenue = LabTestBill.objects.aggregate(
        total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField())
    )['total']
    revenue_breakdown.append(lab_revenue)   
    medicine_revenue = MedicineBill.objects.aggregate(
        total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField())
    )['total']
    revenue_breakdown.append(medicine_revenue)
    ward_revenue = WardBill.objects.aggregate(
        total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField())
    )['total']
    revenue_breakdown.append(ward_revenue)   
    ot_revenue = OTBill.objects.aggregate(
        total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField())
    )['total']
    revenue_breakdown.append(ot_revenue) 
    misc_revenue = MiscellaneousBill.objects.aggregate(
        total=Coalesce(Sum('total_amount'), Value(0), output_field=DecimalField())
    )['total']
    revenue_breakdown.append(misc_revenue)

    paginator = Paginator(doctor_performance, 10) 
    page_number = request.GET.get('page')
    page_obj= paginator.get_page(page_number)


    context = {
        "revenue_today": revenue_today,
        "revenue_month": revenue_month,
        "expenses_month": expenses_month,
        "profit_month": profit_month,
        "occupancy": occupancy,
        "icu_occupancy": icu_occupancy,
        "doctor_performance": doctor_performance,
        'page_obj':page_obj,
        "revenue_breakdown": revenue_breakdown,
        "revenue_breakdown_json": json.dumps(revenue_breakdown, cls=DjangoJSONEncoder),
        'now':timezone.now()
    }
    return render(request, "workspace/management_dashboard.html", context)

