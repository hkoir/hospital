from django import forms

from.models import Product,Category



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
    class Meta:
        model = Product
        exclude=['user','product_code','users_wishlist','likes']

        widgets={
            'description':forms.TextInput(attrs={
                'class': 'form-control custom-textarea',
                'rows': 3, 
                'style': 'height: 50px;', 
            }),

            'manufacture_date':forms.DateInput(attrs={'type':'date'}),
            'expire_date':forms.DateInput(attrs={'type':'date'})
        }


