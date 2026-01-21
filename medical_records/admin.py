from django.contrib import admin

from.models import MedicalRecord, Prescription,MedicalRecordProgress

admin.site.register(MedicalRecord)
admin.site.register(Prescription)
admin.site.register(MedicalRecordProgress)
