from django.contrib import admin
from.models import EmployeeLeaveBalance,LeaveApplication,Shift,RosterSchedule,AttendanceModel
from.models import LatePolicy

admin.site.register(AttendanceModel)

# Register your models here.
admin.site.register(EmployeeLeaveBalance)
admin.site.register(LeaveApplication)

admin.site.register(Shift)
admin.site.register(RosterSchedule)
admin.site.register(LatePolicy)