from.models import Warehouse,Location
from django import forms
from .models import Inventory, InventoryTransaction,Batch,Product,ProductCategory




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

        # 🔁 INBOUND + similar transactions
        if transaction_type in ['INBOUND', 'TRANSFER_IN', 'EXISTING_ITEM_IN', 'SCRAPPED_IN']:         
            # Update or create inventory
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

        # 🔁 OUTBOUND-like transactions
        elif transaction_type in ['OUTBOUND', 'TRANSFER_OUT', 'SCRAPPED_OUT', 'RETURN']:
            if not inventory or inventory.quantity < quantity:
                raise forms.ValidationError("Not enough inventory to perform this transaction.")
            inventory.quantity -= quantity
            inventory.save()

            if batch:
                if (batch.remaining_quantity or 0) < quantity:
                    raise forms.ValidationError("Not enough batch quantity.")
                batch.remaining_quantity -= quantity
                batch.save()

        transaction.inventory_transaction = inventory
        if commit:
            transaction.save()

        # 🔁 TRANSFER_OUT: create matching TRANSFER_IN
        if transaction_type == 'TRANSFER_OUT':
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

            # Batch adjustment for transfer in
            if batch:
                batch.remaining_quantity += quantity
                batch.save()

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
        queryset=ProductCategory.objects.all(),
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
        model = ProductCategory
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
        exclude=['user','product_id']




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



