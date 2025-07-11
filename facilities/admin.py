from django.contrib import admin

from.models import Ward,Bed,Room,OperationTheatre,OTBooking,BedAssignmentHistory

admin.site.register(Ward)
admin.site.register(Bed)
admin.site.register(Room)
admin.site.register(OperationTheatre)
admin.site.register(OTBooking)

admin.site.register(BedAssignmentHistory)
