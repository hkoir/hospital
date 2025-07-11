from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from.models import  Notification
from django.contrib import messages
from patients.models import Patient
from.models import Message
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.http import require_POST


from messaging.models import ManagementMessage
from.forms import ManagementMessageForm

from django.core.paginator import Paginator



# def create_notification(user,notification_type, message):   
#     Notification.objects.create(user,message=message,notification_type=notification_type)




    
def create_notification(user, notification_type, message, patient=None, doctor=None):
    if patient:
        Notification.objects.create(student=patient, message=message, notification_type=notification_type)
    elif doctor:
        Notification.objects.create(doctor=doctor, message=message, notification_type=notification_type)
    else:
        Notification.objects.create(user=user, message=message, notification_type=notification_type)




def mark_notification_as_read(notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()




@login_required
@require_POST  # Only allow POST requests
def mark_notification_read_view(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({"success": True}) 
    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notification not found"}, status=404)






@login_required
def manage_management_message(request, id=None):  
    instance = get_object_or_404(ManagementMessage, id=id) if id else None
    message_text = "updated successfully!" if id else "added successfully!"  
    form = ManagementMessageForm(request.POST or None, request.FILES or None, instance=instance)

    max_messages = 6 
    message_count = ManagementMessage.objects.all().count()
    if message_count >= max_messages:
        messages.error(request, "You have reached the maximum limit of messages.")
        return redirect('messaging:create_management_message')  

    if request.method == 'POST' and form.is_valid():
        form_intance=form.save(commit=False)     
        form_intance.user=request.user  
        form_intance.save()              
        messages.success(request, message_text)
        return redirect('messaging:create_management_message')  
    else:
        print(form.errors)

    datas = ManagementMessage.objects.all().order_by('-created_at')
    paginator = Paginator(datas, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    form = ManagementMessageForm(instance=instance)
    return render(request, 'messaging/manage_management_message.html', {
        'form': form,
        'instance': instance,
        'datas': datas,
        'page_obj': page_obj
    })


@login_required
def delete_management_message(request, id):
    instance = get_object_or_404(ManagementMessage, id=id)
    if request.method == 'POST':
        instance.delete()
        messages.success(request, "Deleted successfully!")
        return redirect('messaging:create_management_message')    

    messages.warning(request, "Invalid delete request!")
    return redirect('messaging:create_management_message')  


