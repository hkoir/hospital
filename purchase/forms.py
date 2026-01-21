
from django import forms
from django.contrib.auth.models import User

from product.models import Product,Category
from.models import PurchaseRequestOrder,PurchaseRequestItem, QualityControl
from inventory.models import Warehouse,Location
from supplier.models import Supplier
from purchase.models import PurchaseRequestOrder,PurchaseOrder
from django.contrib.auth.models import User

from accounts.models import CustomUser
from.models import Batch


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        exclude=['user','remaining_quantity','sale_price','unit_price','selling_price','shelf']

        widgets={
            'manufacture_date':forms.DateInput(attrs={'type':'date'}),
            'expiry_date':forms.DateInput(attrs={'type':'date'})
        }


class BatchFormShort(forms.ModelForm):
    class Meta:
        model = Batch
        fields=['product','quantity','manufacture_date','expiry_date','purchase_price','regular_price','discounted_price']

        widgets={
            'manufacture_date':forms.DateInput(attrs={'type':'date'}),
            'expiry_date':forms.DateInput(attrs={'type':'date'}),
             'purchase_price': forms.NumberInput(attrs={'readonly': 'readonly'}),
        }


class AssignRolesForm(forms.Form):
    requester = forms.ModelChoiceField(queryset=CustomUser.objects.all(), label="Requester")
    reviewer = forms.ModelChoiceField(queryset=CustomUser.objects.all(), label="Reviewer")
    approver = forms.ModelChoiceField(queryset=CustomUser.objects.all(), label="Approver")


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestOrder  
        fields = ['category', 'product', 'product_type','quantity']  

    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        label="Supplier",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Category",
        widget=forms.Select(attrs={'class': 'form-control'})
         )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="Product",
        widget=forms.Select(attrs={'class': 'form-control'})
         )
    product_type = forms.ChoiceField(
        choices=[
            ('raw_materials', 'Raw Materials'),
            ('finished_product', 'Finished Product'),
            ('component', 'Component'),
            ('BOM', 'BOM')
        ],
        label="Product Type",
        widget=forms.Select(attrs={'class': 'form-control'})
        )
   
    quantity = forms.IntegerField(
        label="Quantity",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
         )





from django import forms
from django.forms import inlineformset_factory
from .models import RFQ, RFQItem
from django.forms import inlineformset_factory
from .models import SupplierQuotation, SupplierQuotationItem


class RFQForm(forms.ModelForm):
    class Meta:
        model = RFQ
        fields = ["purchase_request_order","date", "valid_until", "notes", "status"]
        widgets={          
            'valid_until': forms.DateInput(attrs={'type':'date'}),  
             'date': forms.DateInput(attrs={'type':'date'}),
            'notes':forms.TextInput(attrs={
                'style':'height:50px'
            }),         
        }

class RFQItemForm(forms.ModelForm):
    class Meta:
        model = RFQItem
        fields = ["product", "quantity", "notes"]
        widgets={
            'notes':forms.TextInput(attrs={
                'style':'height:50px'
            }),
           
        }
RFQItemFormSet = inlineformset_factory(RFQ, RFQItem, form=RFQItemForm, extra=1, can_delete=True)


class SupplierQuotationForm(forms.ModelForm):
    class Meta:
        model = SupplierQuotation
        fields = ["supplier", "date", "valid_until", "status", "notes"]
        widgets={
            'notes':forms.TextInput(attrs={
                'style':'height:50px'
            }),
            'valid_until': forms.DateInput(attrs={'type':'date'}),
             'date': forms.DateInput(attrs={'type':'date'})
        }


class SupplierQuotationItemForm(forms.ModelForm):
    class Meta:
        model = SupplierQuotationItem
        fields = ["product", "quantity", "unit_price", "vat_percentage","vat_status","ait_status"]

SupplierQuotationItemFormSet = inlineformset_factory(
    SupplierQuotation,
    SupplierQuotationItem,
    form=SupplierQuotationItemForm,
    extra=2,
    can_delete=True
)








class PurchaseOrderForm(forms.ModelForm):
    order_item_id = forms.ModelChoiceField(
        queryset=PurchaseRequestItem.objects.none(),
        label="Request Item",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        label="Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        label="Product",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    batch = forms.ModelChoiceField(
        queryset=Batch.objects.all(),
        label="Batch",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        label="Supplier",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        label="Quantity",
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = PurchaseOrder
        fields = ['order_item_id', 'category', 'product', 'batch', 'supplier', 'quantity']

    def __init__(self, *args, request_instance=None, **kwargs):
        super().__init__(*args, **kwargs)

        if request_instance:
            pr_items = PurchaseRequestItem.objects.filter(purchase_request_order=request_instance)
            product_ids = pr_items.values_list('product_id', flat=True)
            category_ids = pr_items.values_list('product__category_id', flat=True)

            self.fields['order_item_id'].queryset = pr_items
            self.fields['product'].queryset = Product.objects.filter(id__in=product_ids)
            self.fields['category'].queryset = Category.objects.filter(id__in=category_ids)

            

           


class QualityControlForm(forms.ModelForm):
    comments = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 5, 
                'style': 'height: 100px;',  
            }
        )
    )
    inspection_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    class Meta:
        model = QualityControl
        fields = ['total_quantity','good_quantity', 'bad_quantity','inspection_date', 'comments']

    def clean(self):
        cleaned_data = super().clean()
        total_quantity = cleaned_data.get("total_quantity")
        good_quantity = cleaned_data.get("good_quantity")
        bad_quantity = cleaned_data.get("bad_quantity")
        
        if good_quantity and bad_quantity and total_quantity:
            if good_quantity + bad_quantity > total_quantity:
                raise forms.ValidationError("Good and bad quantities cannot exceed the total quantity.")
        return cleaned_data

class PurchaseOrderSearchForm(forms.Form):
    order_number = forms.CharField(
        label="Purchase Order Number",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter order number'})
    )


class PurchaseStatusForm(forms.Form):
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('CANCELLED', 'Cancelled'),
    ]
    approval_status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select)

    remarks = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 5, 
                'style': 'height: 100px;',  
            }
        ),
        required=False
    )

############################### Direct Purchase Procurement ###################################


from. models import DirectPurchaseInvoice,DirectPurchaseInvoiceItem,PurchasePayment,GoodsReceivedItem
from django.forms import inlineformset_factory


class DirectPurchaseInvoiceForm(forms.ModelForm):
    class Meta:
        model = DirectPurchaseInvoice
        fields = ["created_at", "due_date", "supplier_name",'AIT_rate','AIT_type', "advance_amount", "discount_amount", "notes","terms_and_conditions"]
        widgets = {
            "created_at": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2, "style": "height:80px;"}),
            "terms_and_conditions": forms.Textarea(attrs={"rows": 2, "style": "height:80px;"}),
        }


class DirectPurchaseInvoiceItemForm(forms.ModelForm):
    class Meta:
        model = DirectPurchaseInvoiceItem
        fields = ["item", "product_type","description", "batch", "warehouse", "location", "quantity", "unit_price",'VAT_rate','VAT_type', "total_amount"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"step": "any", "class": "form-control quantity-input"}),
            "unit_price": forms.NumberInput(attrs={"step": "any", "class": "form-control unit-price-input"}),
            "total_amount": forms.NumberInput(attrs={
                "step": "any",
                "readonly": "readonly",
                "class": "form-control total-price-input",
            }),
            "description": forms.Textarea(attrs={"rows": 2, "style": "height:80px;"}),
        }

        


DirectPurchaseInvoiceItemFormSet = inlineformset_factory(
    DirectPurchaseInvoice,
    DirectPurchaseInvoiceItem,
    form=DirectPurchaseInvoiceItemForm,
    extra=1,
    can_delete=True
)



class GoodsReceivedItemForm(forms.ModelForm):
    invoice_item = forms.ModelChoiceField(
        queryset=DirectPurchaseInvoiceItem.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = GoodsReceivedItem
        fields = ['invoice_item', 'warehouse', 'location', 'batch', 'quantity_received']
        widgets = {    

              
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'batch': forms.Select(attrs={'class': 'form-select'}),
            'quantity_received': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
   


class PurchasePaymentForm(forms.ModelForm):
    class Meta:
        model = PurchasePayment
        fields = [
            'purchase_invoice','supplier_name',
           'purchase_price', 'vat_amount', 'ait_amount','net_amount',
            'payment_method', 'bank_account', 'asset_tag'
        ]
        widgets = {
            'purchase_invoice': forms.Select(attrs={'class': 'form-control'}),          
            'supplier_name': forms.Select(attrs={'class': 'form-control'}),           
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'vat_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'ait_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'bank_account': forms.Select(attrs={'class': 'form-control'}),
            'asset_tag': forms.TextInput(attrs={'class': 'form-control'}),
            'net_amount': forms.TextInput(attrs={'class': 'form-control'}),
        }












