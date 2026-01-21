from django.contrib import admin

from.models import LabTest,LabTestRequest,LabTestCatalog,LabTestResult,LabTestCategory,LabTestResultOrder
from.models import ExternalLabVisit,SuggestedLabTestRequest,LabTestRequestItem,LabSampleCollection


admin.site.register(LabTest)
admin.site.register(LabTestRequest)
admin.site.register(LabTestCatalog)
admin.site.register(LabTestCategory)
admin.site.register(LabTestResult)
admin.site.register(LabTestResultOrder)
admin.site.register(ExternalLabVisit)
admin.site.register(SuggestedLabTestRequest)
admin.site.register(LabTestRequestItem)
admin.site.register(LabSampleCollection)
