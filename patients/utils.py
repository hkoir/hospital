

from datetime import time
from django.utils.timezone import now
from django.utils.timezone import localtime
from facilities.models import Bed,Ward,Room


def update_room_occupancy(room): 
    capacity = room.capacity or 0
    occupied_beds = room.occupied_beds  
    room.is_occupied = (capacity > 0 and occupied_beds >= capacity)
    room.save(update_fields=['is_occupied'])

def update_ward_occupancy(ward):
    total_capacity = ward.capacity or 0
    occupied_beds = Bed.objects.filter(room__ward=ward, is_occupied=True).count()

    ward.is_occupied = (total_capacity > 0 and occupied_beds >= total_capacity)
    ward.save(update_fields=['is_occupied'])

def update_bed_occupancy(bed, occupied=None):
    if occupied is not None:
        bed.is_occupied = occupied
        bed.save(update_fields=['is_occupied'])

    if bed.room:
        update_room_occupancy(bed.room)
        update_ward_occupancy(bed.room.ward)
    elif bed.ward:
        update_ward_occupancy(bed.ward)






def calculate_billed_days(assigned_at, released_at):
    if not assigned_at:
        return 0
    if not released_at:
        released_at = now()
    assigned_at = localtime(assigned_at)
    released_at = localtime(released_at)

    days = (released_at.date() - assigned_at.date()).days
    return max(days + 1, 1)






def calculate_billed_days2(assigned_at, released_at):
    if not assigned_at or not released_at:
        return 0

    same_day = assigned_at.date() == released_at.date()    
    if same_day:
        return 1   
    days = (released_at.date() - assigned_at.date()).days
    if released_at.time() > time(12, 0):
        days += 1  
    return days
