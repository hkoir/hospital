from django.contrib import admin

from.models import PurchaseRequestOrder,PurchaseRequestItem,PurchaseOrder,PurchaseOrderItem,ReceiveGoods,QualityControl
from .models import PurchaseRequestOrder,Batch,SupplierQuotation,SupplierQuotationItem,RFQ,RFQItem


admin.site.register(PurchaseOrderItem)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseRequestOrder)
admin.site.register(PurchaseRequestItem)
admin.site.register(QualityControl)
admin.site.register(ReceiveGoods)
admin.site.register(Batch)
admin.site.register(RFQ)
admin.site.register(RFQItem)
admin.site.register(SupplierQuotation)
admin.site.register(SupplierQuotationItem) 



# @admin.register(PurchaseRequestOrder)
# class PurchaseRequestOrderAdmin(admin.ModelAdmin):
#     list_display = ['order_id', 'requester', 'reviewer', 'approver']
#     actions = ['assign_roles_action']

#     def assign_roles_action(self, request, queryset):
#         if 'apply' in request.POST:
#             form = AssignRolesForm(request.POST)
#             if form.is_valid():
#                 requester = form.cleaned_data['requester']
#                 reviewer = form.cleaned_data['reviewer']
#                 approver = form.cleaned_data['approver']

#                 for order in queryset:
#                     if requester:
#                         order.requester = requester
#                     if reviewer:
#                         order.reviewer = reviewer
#                     if approver:
#                         order.approver = approver
#                     order.save()

#                 self.message_user(request, "Roles assigned successfully.")
#                 return HttpResponseRedirect(request.get_full_path())
#         else:
#             form = AssignRolesForm()

#         # Render the form and pass the selected orders
#         return render(request, 'admin/assign_roles.html', {'form': form, 'orders': queryset})

#     assign_roles_action.short_description = "Assign roles to selected purchase requests"
