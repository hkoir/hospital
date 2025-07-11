

from datetime import time
from django.utils.timezone import now
from django.utils.timezone import localtime

def update_room_occupancy(room):
    if room.room_beds.filter(is_occupied=False).exists():
        room.is_occupied = False
    else:
        room.is_occupied = True
    room.save(update_fields=['is_occupied'])



def update_ward_occupancy(ward):
    if ward.ward_rooms.filter(is_occupied=False).exists():
        ward.is_occupied = False
    else:
        ward.is_occupied = True
    ward.save(update_fields=['is_occupied'])




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
