

from django.shortcuts import render
from .models import Ward
from .models import OperationTheatre  
from django.core.paginator import Paginator

def ward_room_bed_status(request):
    wards = Ward.objects.all()
    operation_theatres = OperationTheatre.objects.all()

    ward_status_list = []
    for ward in wards:
        total_beds = ward.ward_beds.count()
        occupied_beds = ward.ward_beds.filter(is_occupied=True).count()
        available_beds = total_beds - occupied_beds

        ward_status_list.append({
            'ward': ward,
            'total_beds': total_beds,
            'occupied_beds': occupied_beds,
            'available_beds': available_beds,
            'rooms': [
                {
                    'room': room,
                    'daily_charge': room.daily_charge,
                    'total_beds': room.room_beds.count(),
                    'occupied_beds': room.room_beds.filter(is_occupied=True).count(),
                    'available_beds': room.room_beds.count() - room.room_beds.filter(is_occupied=True).count()
                }
                for room in ward.ward_rooms.all()
            ]
        })

    # Collect OT status
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
        'ward_status_list': ward_status_list,
        'ot_status_list': ot_status_list,
         'page_obj': page_obj,
    }

    return render(request, 'facilities/ward_room_bed_status.html', context)
