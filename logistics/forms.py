
from django import forms
from .models import PurchaseShipment,PurchaseDispatchItem
from purchase.models import PurchaseOrderItem





class PurchaseShipmentForm(forms.ModelForm):
    estimated_delivery = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    class Meta:
        model = PurchaseShipment
        fields = ['carrier', 'tracking_number', 'estimated_delivery']



class PurchaseDispatchItemForm(forms.ModelForm):
    dispatch_date=forms.DateField(
        widget=forms.DateInput(attrs={'type':'date'}),
        required=False
    )
    delivery_date=forms.DateField(
        widget=forms.DateInput(attrs={'type':'date'}),
        required=False
    )

    class Meta:
        model = PurchaseDispatchItem
        exclude=['dispatch_id','user','status']


    def __init__(self, *args, purchase_shipment=None, **kwargs):
        super(PurchaseDispatchItemForm, self).__init__(*args, **kwargs)

        if purchase_shipment:
            self.fields['purchase_shipment'].queryset = PurchaseShipment.objects.filter(id=purchase_shipment.id)            
            self.fields['dispatch_item'].queryset = PurchaseOrderItem.objects.filter(purchase_order__purchase_shipment=purchase_shipment)
        else:
            self.fields['purchase_shipment'].queryset = PurchaseShipment.objects.all()
            self.fields['dispatch_item'].queryset = PurchaseOrderItem.objects.all()
         
        self.fields['purchase_shipment'].widget.attrs.update({
            'style': 'max-width: 200px; word-wrap: break-word; overflow: hidden; text-overflow: ellipsis;'
        })
          
        self.fields['dispatch_item'].widget.attrs.update({
            'style': 'max-width: 200px; word-wrap: break-word; overflow: hidden; text-overflow: ellipsis;'
        })


