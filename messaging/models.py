from django.db import models


import requests
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import logging
from django.contrib import messages

from accounts.models import CustomUser
from patients.models import Patient,Guardian
from core.models import Doctor
from payment_gateway.utils import send_sms
from core.utils import POSITION_CHOICES




class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='student_notifications', null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='teacher_notifications', null=True, blank=True)
    notification_type=models.CharField(max_length=20,choices=[('attendance','Attendance'),('payment-due','Payment_due'),('notice','Notice'),('general','General')], null=True, blank=True)
    message = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  

    def __str__(self):
        if self.patient:
            return f"Notification for {self.patient.name}: {self.message}"
        elif self.doctor:
            return f"Notification for {self.doctor.name}: {self.message}"
        else:
            return f"Notification for {self.user}: {self.message}"

    def mark_as_read(self):
        self.is_read = True
        self.save()




class Message(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE,null=True,blank=True,related_name='student_message')
    doctor = models.ForeignKey(Doctor, null=True, blank=True, on_delete=models.CASCADE, related_name='teacher_messages')
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE,null=True,blank=True)
    
    message_content = models.TextField()
    message_type = models.CharField(max_length=50, choices=[
        ('Attendance', 'Attendance'),
        ('Result', 'Result'),
        ('Fee', 'Fee'),
        ('General', 'General'),
    ],null=True,blank=True)
    
    date_sent = models.DateTimeField(auto_now_add=True)
    is_sent = models.BooleanField(default=False)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SMS to {self.guardian.name} about {self.patient.name}"
        

    def send_sms(self):
        if self.guardian and self.guardian.phone_number:    
            patient = self.patient            
            tenant = patient.user.tenant              
            phone_number = self.guardian.phone_number
            message = self.message_content

            try:
                response = send_sms(tenant, phone_number, message)               

                if response:
                    self.is_sent = True
                    self.save()
                return response
            except Exception as e:
                print(f"SMS send failed: {str(e)}")
                return None
        else:
            print("Guardian or phone number missing")
            return None
        


@receiver(post_save, sender=Message)
def send_sms_on_message_creation(sender, instance, created, **kwargs):
    if created and not instance.is_sent:
        instance.send_sms()





class ManagementMessage(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,null=True,blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=100,choices=POSITION_CHOICES, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='tenant_photo/', null=True, blank=True)
    signature = models.ImageField(upload_to='tenant_signature/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message of {self.name} -- {self.position}"

    class Meta:
        # Meta options for your model (e.g., ordering or constraints)
        pass
