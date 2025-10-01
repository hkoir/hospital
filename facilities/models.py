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
    ]

    name = models.CharField(max_length=100)
    ward_type = models.CharField(max_length=50, choices=WARD_TYPE_CHOICES)
    daily_charge = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    location = models.CharField(max_length=100,null=True,blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_ward_type_display()})"





class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('Private', 'Private Room'),
        ('Semi-Private', 'Semi-Private Room'),
        ('Suite', 'Suite'),
    ]

    number = models.CharField("Room No.", max_length=10, unique=True,null=True,blank=True)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='ward_rooms')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    floor = models.IntegerField(null=True,blank=True)
    capacity= models.PositiveIntegerField(help_text="How many beds fit in this room",null=True,blank=True)
    daily_charge= models.DecimalField(max_digits=10, decimal_places=2, help_text="Daily charge for using this room",null=True,blank=True)
    is_active = models.BooleanField(default=True)
    is_occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.number} ({self.room_type})"

    @property
    def occupied_beds(self):
        return self.beds.filter(is_occupied=True).count()

    @property
    def available_beds(self):
        return self.capacity - self.occupied_beds

class Bed(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='ward_beds')
    room = models.ForeignKey('facilities.Room', on_delete=models.CASCADE, related_name='room_beds',null=True,blank=True)
    bed_number = models.CharField(max_length=10,null=True,blank=True)
    daily_charge = models.DecimalField(max_digits=10,decimal_places=2, help_text="Optional override for this specific bed", null=True, blank=True)
    is_occupied = models.BooleanField(default=False)
    bed_type = models.CharField(
        max_length=50,
        choices=[('Regular', 'Regular'), ('Oxygen', 'Oxygen'), ('Ventilator', 'Ventilator')],null=True,blank=True
    )
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bed {self.bed_number} in {self.ward.name}"


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

    def __str__(self):
        return f"{self.name} ({self.ot_type})"
    

class OTBooking(models.Model):
    operation_theatre = models.ForeignKey(OperationTheatre, on_delete=models.CASCADE)
    invoice = models.ForeignKey(BillingInvoice, on_delete=models.CASCADE,null=True,blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,null=True,blank=True)
    surgeon = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    booked_start = models.DateTimeField(null=True,blank=True)
    booked_end = models.DateTimeField(null=True,blank=True)
    procedure = models.ForeignKey(DoctorServiceRate, on_delete=models.SET_NULL, null=True, blank=True)
    surgery_type = models.CharField(max_length=100, choices=DoctorServiceRate.SURGERY_TYPE_CHOICES, blank=True, null=True)
    patient_type =  models.CharField(max_length=50,choices=[('IPD','Inpatient'),('OPD','OutPatient'),('Emergency','Emergency')],null=True,blank=True)
    notes = models.TextField(blank=True)
    total_charge = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def duration_hours(self):
        delta = self.booked_end - self.booked_start
        return round(delta.total_seconds() / 3600, 2)

    def save(self, *args, **kwargs):
        if not self.total_charge:
            self.total_charge = float(self.operation_theatre.hourly_rate) * float(self.duration_hours())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient} OT Booking for {self.procedure}"



class BedAssignmentHistory(models.Model):
    patient_admission = models.ForeignKey('patients.PatientAdmission', on_delete=models.CASCADE, related_name='bed_assignments',null=True,blank=True)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE,null=True,blank=True)
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE,null=True,blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE,null=True,blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,related_name='patient_bed_histories')
    reason_for_move = models.CharField(max_length=255, blank=True, null=True) 
    assigned_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient} assigned to {self.bed} from {self.assigned_at}"


