


from django.contrib import admin
from.models import Payment,BillingInvoice,ConsultationBill,MedicineBill,OTBill,WardBill,LabTestBill
from.models import EmergencyVisit,DoctorServiceRate,DoctorServiceLog,ReferralSource,ReferralCommissionRule,ReferralCommissionTransaction
from.models import ReferralPayment,DoctorPayment

admin.site.register(Payment)
admin.site.register(BillingInvoice)
admin.site.register(ConsultationBill)
admin.site.register(WardBill)
admin.site.register(MedicineBill)
admin.site.register(OTBill)
admin.site.register(LabTestBill)

admin.site.register(DoctorServiceRate)
admin.site.register(EmergencyVisit)
admin.site.register(DoctorServiceLog)
admin.site.register(DoctorPayment)

admin.site.register(ReferralCommissionTransaction)
admin.site.register(ReferralCommissionRule)
admin.site.register(ReferralSource)
admin.site.register(ReferralPayment)




