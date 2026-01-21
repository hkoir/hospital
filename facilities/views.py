

from django.shortcuts import render
from .models import Ward
from .models import OperationTheatre  
from django.core.paginator import Paginator


from facilities.models import Ward, Room, Bed, OperationTheatre

from django.http import JsonResponse


def get_rooms(request):
    ward_id = request.GET.get("ward_id")
    rooms = Room.objects.filter(ward_id=ward_id)
    data = [{"id": r.id, "number": r.number} for r in rooms]
    return JsonResponse({"rooms": data})

def get_beds(request):
    room_id = request.GET.get("room_id")
    beds = Bed.objects.filter(room_id=room_id, is_occupied=False)
    data = [
        {
            "id": b.id,
            "bed_number": b.bed_number,
            "charge": b.hourly_charge if b.hourly_charge else b.daily_charge,
            "charge_type": "Hourly" if b.hourly_charge else "Daily",
        }
        for b in beds
    ]
    return JsonResponse({"beds": data})


def ward_room_bed_status(request):
    wards = Ward.objects.prefetch_related('ward_rooms__room_beds').all()
    operation_theatres = OperationTheatre.objects.all()

    ward_status_list = []

    for ward in wards:
        rooms_list = []
        for room in ward.ward_rooms.all():
            beds_list = room.room_beds.all()
            rooms_list.append({
                'room': room,
                'beds': beds_list,
                'total_beds': beds_list.count(),
                'occupied_beds': beds_list.filter(is_occupied=True).count(),
                'available_beds': beds_list.count() - beds_list.filter(is_occupied=True).count(),
            })

        total_beds = sum(r['total_beds'] for r in rooms_list)
        occupied_beds = sum(r['occupied_beds'] for r in rooms_list)

        ward_status_list.append({
            'ward': ward,
            'rooms': rooms_list,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'available_beds': total_beds - occupied_beds
        })

    # OT status
    ot_status_list = [
        {
            'ot': ot,
            'name': ot.name,
            'type': ot.ot_type,
            'location': ot.location,
            'hourly_rate': ot.hourly_rate,
            'is_available': ot.is_available,
            'is_occupied': ot.is_occupied
        }
        for ot in operation_theatres
    ]

    paginator = Paginator(ward_status_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'ward_status_list': page_obj,
        'ot_status_list': ot_status_list,
        'page_obj': page_obj,
    }

    return render(request, 'facilities/ward_room_bed_status.html', context)
