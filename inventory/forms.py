from.models import Warehouse,Location
from django import forms
from .models import Inventory, InventoryTransaction

from product.models import Product,Category
from purchase.models import Batch


class InventoryTransactionForm(forms.ModelForm):
    create_inventory = forms.BooleanField(required=False, label="Create New Inventory Entry")
    target_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), required=False)
    target_location = forms.ModelChoiceField(queryset=Location.objects.all(), required=False)


    class Meta:
        model = InventoryTransaction
        fields = [
            'transaction_type',
            'product',
            'batch',
            'warehouse',
            'location',
            'quantity',
            'remarks',
        ]
        widgets = {
            'batch': forms.Select(attrs={'class': 'form-control'}),  # Apply 'form-control' class here
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
          
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # You can pass the user in the view
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        warehouse = cleaned_data.get('warehouse')
        location = cleaned_data.get('location')
        quantity = cleaned_data.get('quantity')
        transaction_type = cleaned_data.get('transaction_type')

        if transaction_type in ['OUTBOUND', 'TRANSFER_OUT', 'SCRAPPED_OUT','RETURN']:
            inventory = Inventory.objects.filter(
                product=product, warehouse=warehouse, location=location
            ).first()
            if not inventory or inventory.quantity < quantity:
                raise forms.ValidationError("Not enough inventory to perform this transaction.")
        
        return cleaned_data
        
    def save(self, commit=True):
        transaction = super().save(commit=False)
        transaction.user = self.user

        product = transaction.product
        warehouse = transaction.warehouse
        location = transaction.location
        batch = transaction.batch
        quantity = transaction.quantity
        transaction_type = transaction.transaction_type

        # Inventory lookup
        inventory = Inventory.objects.filter(
            product=product,
            warehouse=warehouse,
            location=location,
            batch=batch
        ).first()

        # 🔹 INBOUND-like transactions
        if transaction_type in ['INBOUND', 'EXISTING_ITEM_IN', 'SCRAPPED_IN']:
            if inventory:
                inventory.quantity += quantity
                inventory.save()
            else:
                inventory = Inventory.objects.create(
                    product=product,
                    warehouse=warehouse,
                    location=location,
                    batch=batch,
                    quantity=quantity,
                    user=self.user
                )

        # 🔹 OUTBOUND-like transactions
        elif transaction_type in ['OUTBOUND', 'SCRAPPED_OUT', 'RETURN']:
            if not inventory or inventory.quantity < quantity:
                raise forms.ValidationError("Not enough inventory to perform this transaction.")
            inventory.quantity -= quantity
            inventory.save()

            if batch:
                if (batch.remaining_quantity or 0) < quantity:
                    raise forms.ValidationError("Not enough batch quantity.")
                batch.remaining_quantity -= quantity
                batch.save()

        # 🔹 TRANSFER transaction (source OUT + target IN)
        elif transaction_type == 'TRANSFER_OUT':
            if not inventory or inventory.quantity < quantity:
                raise forms.ValidationError("Not enough inventory to perform transfer.")
            # Decrease from source inventory
            inventory.quantity -= quantity
            inventory.save()

            if batch:
                if (batch.remaining_quantity or 0) < quantity:
                    raise forms.ValidationError("Not enough batch quantity.")
                # ❗ Do NOT increment batch again later — transfer keeps total stock unchanged
                batch.remaining_quantity -= quantity
                batch.save()

            # Target info
            target_warehouse = self.cleaned_data.get('target_warehouse')
            target_location = self.cleaned_data.get('target_location')
            if not target_warehouse or not target_location:
                raise forms.ValidationError("Target warehouse and location required for transfer.")

            # Target inventory
            target_inventory = Inventory.objects.filter(
                product=product,
                warehouse=target_warehouse,
                location=target_location,
                batch=batch
            ).first()
            if not target_inventory:
                target_inventory = Inventory.objects.create(
                    product=product,
                    warehouse=target_warehouse,
                    location=target_location,
                    batch=batch,
                    quantity=0,
                    user=self.user
                )

            target_inventory.quantity += quantity
            target_inventory.save()

            # Create transfer in record
            InventoryTransaction.objects.create(
                inventory_transaction=target_inventory,
                user=self.user,
                transaction_type='TRANSFER_IN',
                product=product,
                batch=batch,
                warehouse=target_warehouse,
                location=target_location,
                quantity=quantity,
                remarks=f"Auto-created TRANSFER_IN from {warehouse.name}/{location.name}"
            )

        transaction.inventory_transaction = inventory
        if commit:
            transaction.save()

        return transaction



class ProductSearchForm(forms.Form):   
    product = forms.CharField(required=False)
    warehouse = forms.CharField(required=False)
    location = forms.CharField(required=False)
    batch = forms.CharField(required=False)
  


class CommonFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        label='End Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    days = forms.IntegerField(
        label='Number of Days',
        min_value=1,
        required=False
    )

 
    ID_number = forms.CharField(
        label='Order ID',
        required=False,
       
    )   

    warehouse_name = forms.ModelChoiceField(queryset=Warehouse.objects.all(),required=False)
    product_name = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_product_name'}),
    )

    

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_category'}),
    )




class AddCategoryForm(forms.ModelForm):     

    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 3, 
                'style': 'height: 20px;', 
            }
        )
    )
 
    class Meta:
        model = Category
        fields = ['name','description']



class AddProductForm(forms.ModelForm):  
    description = forms.CharField(required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 3, 
                'style': 'height: 20px;', 
            }
        )
    )    
    manufacture_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    expiry_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = Product
        exclude=['user','product_id','barcode','is_popular','is_hot_sale','is_regular','is_offer','likes','users_wishlist','product_image']



class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        exclude=['user','remaining_quantity']

        widgets={
            'manufacture_date':forms.DateInput(attrs={'type':'date'}),
            'expiry_date':forms.DateInput(attrs={'type':'date'})
        }






from .models import MedicineSaleOnly,MedicineSaleItem

class MedicineSaleOnlyForm(forms.ModelForm):
    class Meta:
        model = MedicineSaleOnly
        fields = ['patient', 'doctor_ref', 'doctor', 'prescription_file']

class MedicineSaleItemForm(forms.ModelForm):
    class Meta:
        model = MedicineSaleItem 
        fields = ['medicine', 'batch', 'quantity']



##############################################


from.models import InventoryTransaction,Warehouse,Location
from product.models import Product
from purchase.models import Batch
from .models import Inventory


class AddWarehouseForm(forms.ModelForm):      
    class Meta:
        model = Warehouse
        exclude = ['created_at','updated_at','history','user','warehouse_id','reorder_level','lead_time']
        widgets = {
            
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter a description', 
                'rows': 3
            }),
        }

class AddLocationForm(forms.ModelForm):      
    class Meta:
        model = Location
        fields= ['warehouse','name','address','description']
        widgets = {
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter the address', 
                'rows': 3
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter a description', 
                'rows': 3
            }),
        }

          


class QualityControlCompletionForm(forms.Form):
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.all(),
        label="Select Warehouse",
        required=True
    )
    location = forms.ModelChoiceField(
        queryset=Location.objects.none(),  # Initially empty, will be dynamically loaded
        label="Select Location",
        required=True
    )  
    # batch= forms.ModelChoiceField(
    #     queryset=Batch.objects.all(),  # Initially empty, will be dynamically loaded
    #     label="Select Batch",
    #     required=False
    # )  

    def __init__(self, *args, **kwargs): 
        warehouse = kwargs.pop('warehouse', None)
        super().__init__(*args, **kwargs)
        
        if warehouse:
            self.fields['location'].queryset = Location.objects.filter(warehouse=warehouse)




class WarehouseReorderLevelForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['product', 'warehouse', 'reorder_level']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control'}),
        }
