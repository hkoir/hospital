from django.contrib import admin

from.models import Patient,PatientAdmission,DischargeReport

admin.site.register(Patient)
admin.site.register(PatientAdmission)
admin.site.register(DischargeReport)