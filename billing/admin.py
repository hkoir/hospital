from django.contrib import admin
from.models import Payment,BillingInvoice,ConsultationBill,MedicineBill,OTBill,WardBill,DoctorServiceLog,DoctorPayment
from.models import EmergencyVisit,DoctorServiceRate,LabTestBill


admin.site.register(EmergencyVisit)
admin.site.register(Payment)
admin.site.register(BillingInvoice)
admin.site.register(ConsultationBill)
admin.site.register(WardBill)
admin.site.register(MedicineBill)
admin.site.register(OTBill)
admin.site.register(DoctorServiceLog)
admin.site.register(DoctorPayment)
admin.site.register(DoctorServiceRate)

admin.site.register(LabTestBill)
