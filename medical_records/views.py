
from.models import MedicalRecord
from.forms import MedicalRecordFilter
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required,permission_required,user_passes_test

from django.shortcuts import render,redirect,get_object_or_404
from medical_records.models import MedicalRecord
from lab_tests.models import LabTestRequest
from django.contrib import messages
from.forms import MedicalRecordProgressForm
from.models import MedicalRecordProgress
from django.utils import timezone




@login_required
def medical_record_list(request):
    form = MedicalRecordFilter(request.GET)
    records = MedicalRecord.objects.none()

    if form.is_valid():
        doctor = form.cleaned_data['doctor']
        patient = form.cleaned_data['patient']    
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        records = MedicalRecord.objects.all()

        if doctor:
            records = records.filter(doctor=doctor)
        if patient:
            records = records.filter(patient=patient)
        if start_date and end_date:
            records = records.filter(date__range =[start_date,end_date])
    

    datas =records.order_by('-date')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'medical_records/medical_record_list.html', {'page_obj': page_obj,'form':form})



from .forms import MedicalRecordInitialAssessmentForm
from patients.models import PatientAdmission
from core.models import Doctor

@login_required
def medical_record_update_initial_assessment(request, admission_id):
    admission = get_object_or_404(PatientAdmission, id=admission_id)
    billing= admission.billing_admission
    medical_record = billing.medical_record  
    # doctor = request.user.doctor                 #

    # if admission.doctor != doctor:
    #     messages.error(request, "You are not assigned to this patient.")
    #     return redirect("patients:patient_admission_detail", admission_id=admission.id)

    doctor = Doctor.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = MedicalRecordInitialAssessmentForm(request.POST, instance=medical_record)

        if form.is_valid():
            mr = form.save(commit=False)
            mr.doctor = doctor
            mr.save()

            messages.success(request, "Initial Assessment updated successfully.")
            return redirect("patients:patient_admission_detail", admission_id=admission.id)
    else:
        form = MedicalRecordInitialAssessmentForm(instance=medical_record)

    context = {
        "form": form,
        "admission": admission,
        "medical_record": medical_record
    }
    return render(request, "medical_records/medical_record_initial_assessment.html", context)





def grouped_lab_test_requests_view(request, record_id):
    medical_record = get_object_or_404(MedicalRecord, id=record_id)
    
    lab_test_requests = LabTestRequest.objects.filter(
        medical_record=medical_record
    ).prefetch_related('test_items__lab_test', 'requested_by').order_by('-created_at')


    for lab_request in lab_test_requests:
        lab_request.has_pending_items = lab_request.test_items.filter(status='Pending').exists()


    context = {
        'medical_record': medical_record,
        'lab_test_requests': lab_test_requests,
    }
    return render(request, 'medical_records/grouped_lab_test_requests.html', context)







@login_required
def medical_record_progress_detail(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)

    class PseudoNote:
        def __init__(self, record):
            self.diagnosis = record.diagnosis
            self.treatment_plan = record.treatment_plan
            self.remarks = None
            self.date = record.date
            self.created_by = record.doctor.name if record.doctor else record.external_doctor
            self.is_main_record = True
            self.id = None  # No ID for main record

    # Main record as pseudo-object
    main_note = PseudoNote(record)

    # Actual progress note instances with flag
    progress_notes = list(record.progress_notes.all().order_by('date'))
    for p in progress_notes:
        p.is_main_record = False

    # Combine
    all_notes = [main_note] + progress_notes

    return render(request, 'medical_records/medical_record_progress_detail.html', {
        'record': record,
        'all_notes': all_notes
    })








@login_required
def add_medical_record_progress(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)
    current_time = timezone.now
    
    if request.method == 'POST':
        form = MedicalRecordProgressForm(request.POST)
        if form.is_valid():
            progress = form.save(commit=False)
            progress.medical_record = record
            progress.updated_by = request.user
            progress.save()
            messages.success(request, 'Progress update added successfully.')
            return redirect('medical_records:medical_record_progress_detail',record_id=record.id)
    else:
        form = MedicalRecordProgressForm()
    
    return render(request, 'medical_records/add_medical_record_progress.html', {
        'form': form,
        'record': record,
        'current_time':current_time
    })



@login_required
def edit_medical_record_progress(request, progress_id):
    progress_note = get_object_or_404(MedicalRecordProgress, id=progress_id)
    if request.method == 'POST':
        form = MedicalRecordProgressForm(request.POST, instance=progress_note)
        if form.is_valid():
            updated_note = form.save(commit=False)
            updated_note.is_edited = True
            updated_note.edited_by = request.user
            updated_note.save()
            messages.success(request, 'Progress note updated successfully.')
            return redirect('medical_records:medical_record_progress_detail', record_id=progress_note.medical_record.id)
    else:
        form = MedicalRecordProgressForm(instance=progress_note)

    return render(request, 'medical_records/edit_progress_note.html', {'form': form, 'progress_note': progress_note})













