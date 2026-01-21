from django.db import models
from billing.models import BillingInvoice
from core.models import Doctor
from billing.models import DoctorServiceRate





class Ward(models.Model):
    WARD_TYPE_CHOICES = [
        ('General', 'General Ward'),
        ('Private', 'Private Room'),
        ('SemiPrivate', 'Semi Private'),
        ('ICU', 'ICU'),
        ('SDU', 'Step-Down Unit'),
        ('NICU', 'Neonatal ICU'),
        ('PICU', 'Pediatric ICU'),
        ('Emergency', 'Emergency ward'),
    ]

    name = models.CharField(max_length=100)
    ward_type = models.CharField(max_length=50, choices=WARD_TYPE_CHOICES)
    location = models.CharField(max_length=100, null=True, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)

    def __str__(self):
        return f"{self.name} ({self.get_ward_type_display()})"


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('General', 'General Room'),
        ('Cabin', 'Cabin / Private Room'),
        ('SemiPrivate', 'Semi-Private Room'),
        ('Suite', 'Suite'),
    ]

    number = models.CharField("Room No.", max_length=10, unique=True, null=True, blank=True)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='ward_rooms')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    floor = models.IntegerField(null=True, blank=True)
    capacity = models.PositiveIntegerField(help_text="How many beds fit in this room", null=True, blank=True)   
    is_active = models.BooleanField(default=True)
    is_occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def occupied_beds(self):
        return self.room_beds.filter(is_occupied=True).count()

    @property
    def available_beds(self):
        return (self.capacity or 0) - self.occupied_beds

    def __str__(self):
        return f"Room {self.number} ({self.get_room_type_display()})"

from django.core.exceptions import ValidationError

class Bed(models.Model):
    BED_TYPE_CHOICES = [
        ('Regular', 'Regular'),
        ('Oxygen', 'Oxygen'),
        ('Ventilator', 'Ventilator'),
        ('Emergency', 'Emergency')
    ]

    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='ward_beds')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_beds', null=True, blank=True)
    bed_number = models.CharField(max_length=10, null=True, blank=True)
    daily_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hourly_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bed_type = models.CharField(max_length=50, choices=BED_TYPE_CHOICES, null=True, blank=True)
    is_occupied = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)

    def clean(self):
        if not self.room and not self.ward:
            raise ValidationError("A bed must belong to either a Room or a Ward.")

    def save(self, *args, **kwargs):
        self.clean()  
        super().save(*args, **kwargs)

    def get_effective_daily_charge(self):
        return self.daily_charge

    def get_effective_hourly_charge(self):
        return self.hourly_charge

    def __str__(self):
        return f"Bed {self.bed_number} ({self.bed_type or 'Regular'})"



class BedAssignmentHistory(models.Model):
    patient_admission = models.ForeignKey('patients.PatientAdmission', on_delete=models.CASCADE, related_name='bed_assignments', null=True, blank=True)
    emergency_visit = models.ForeignKey('billing.EmergencyVisit',on_delete=models.CASCADE,related_name='emergency_bed_histories',null=True,blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='bed_histories')
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE, null=True, blank=True)
    reason_for_move = models.CharField(max_length=255, blank=True, null=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient.name} - Bed {self.bed.bed_number if self.bed else 'N/A'}"

    @property
    def charge_amount(self):      
        if not self.assigned_at or not self.released_at:
            return Decimal('0.00')

        duration_hours = (self.released_at - self.assigned_at).total_seconds() / 3600
        if self.bed and self.bed.hourly_charge:
            return (Decimal(duration_hours) * self.bed.get_effective_hourly_charge()).quantize(Decimal('0.01'))
        else:
            num_days = max(1, (self.released_at.date() - self.assigned_at.date()).days)
            return (Decimal(num_days) * (self.bed.get_effective_daily_charge() if self.bed else Decimal('0.00'))).quantize(Decimal('0.01'))



class OperationTheatre(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True,blank=True)
    ot_type = models.CharField(
        max_length=50,null=True,blank=True,
        choices=[('General', 'General Surgery'), ('Cardiac', 'Cardiac OT'), ('Neuro', 'Neurosurgery OT'), ('Other', 'Other')],
        default='General')
    hourly_rate = models.DecimalField(max_digits=10,null=True,blank=True, decimal_places=2, help_text="Cost per hour for using this OT")
    is_available = models.BooleanField(default=True)
    is_occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)

    def __str__(self):
        return f"{self.name} ({self.ot_type})"



from billing.models import SERVICE_TYPE_CHOICES

class OTBooking(models.Model):
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES,null=True,blank=True)
    operation_theatre = models.ForeignKey(OperationTheatre, on_delete=models.CASCADE)
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE,null=True,blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,null=True,blank=True)
    surgeon = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    booked_start = models.DateTimeField(null=True,blank=True)
    booked_end = models.DateTimeField(null=True,blank=True)
    procedure = models.ForeignKey(DoctorServiceRate, on_delete=models.SET_NULL, null=True, blank=True)
    patient_type =  models.CharField(max_length=50,choices=[('IPD','Inpatient'),('OPD','OutPatient'),('Emergency','Emergency')],null=True,blank=True)
    notes = models.TextField(blank=True)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)
    def duration_hours(self):
        delta = self.booked_end - self.booked_start
        return round(delta.total_seconds() / 3600, 2)

    def save(self, *args, **kwargs):
        if not self.total_charge:
            self.total_charge = float(self.operation_theatre.hourly_rate) * float(self.duration_hours())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OT Booking for {self.patient}"




class OTBookingProcedure(models.Model):
    ot_booking = models.ForeignKey(OTBooking, on_delete=models.CASCADE, related_name='procedures')
    procedure = models.ForeignKey(
        DoctorServiceRate,
        on_delete=models.CASCADE,
        related_name='booking_procedures'
    )
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)

    def __str__(self):
        return f"OT Booking for {self.procedure}"

