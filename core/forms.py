from django import forms
from.models import Employee,Company,Location,Department,Position
from.models import Notice
from.models import CompanyPolicy,SalaryStructure


class ManageDepartmentForm(forms.ModelForm):   
    description = forms.CharField(required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 4, 
                'style': 'height: 20px;', 
            }
        )
    )
    custom_department_name = forms.CharField(
        max_length=100,
        required=False,
        label=" Enter Custom Department",
        help_text="Add a new department if it does not exist in the choices."
    )

    class Meta:
        model = Department
        fields = ['name', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = False  



class ManagePositionForm(forms.ModelForm):  
    custom_position_name = forms.CharField(
        max_length=100,
        required=False,
        label="Enter Custom Position",
        help_text="Add a new position if it does not exist in the current department."
    )

    class Meta:
        model = Position
        exclude = ['user']

        widgets={
            'requirement':forms.CheckboxSelectMultiple(),
            'description':forms.CheckboxSelectMultiple()
        }

   
       

from.models import JobRequirement,JobDescription

class JobRequirementForm(forms.ModelForm):     
    class Meta:
        model = JobRequirement
        exclude = ['user']

        widgets={
            'requirement':forms.TextInput(attrs={
                'class':'form-control',
                'row':3
            })
        }

   
class JobDescriptionForm(forms.ModelForm):     
    class Meta:
        model = JobDescription
        exclude = ['user']

        widgets={
            'description':forms.TextInput(attrs={
                'class':'form-control',
                'row':3
            })
        }


class ManageLocationForm(forms.ModelForm):
    description = forms.CharField(required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 4, 
                'style': 'height: 20px;', 
            }
        )
    )
    custom_location_name = forms.CharField(
        max_length=100,
        required=False,
        label="Enter Custom Location",
        help_text="Add a new location if it does not exist in the location list."
    )

    class Meta:
        model = Location
        exclude = ['user']
        widgets={
            'address':forms.Textarea(attrs={
                'class': 'form-control custom-textarea',
                'rows': 4, 
                'style': 'height: 20px;', 
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.all()
        self.fields['name'].required = False  
       



class UpdateLocationForm(forms.ModelForm):
    address = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control custom-textarea',
                'rows': 3, 
                'style': 'height: 30px;', 
            }
        )
    )
    class Meta:
        model=Location
        exclude = ['location_id','history','created_at','updated_at','user']

 

class AddCompanyForm(forms.ModelForm):      
    class Meta:
        model = Company
        exclude = ['created_at','updated_at','history','user']




#############################Policy and salary structure#################################################
from.models import Festival,PerformanceBonus

class CompanyPolicyForm(forms.ModelForm):      
    class Meta:
        model = CompanyPolicy
        exclude = ['user','policy_code']

class SalaryStructureForm(forms.ModelForm):      
    class Meta:
        model = SalaryStructure
        exclude = ['user','salary_structure_code']


class FestivalForm(forms.ModelForm):      
    class Meta:
        model = Festival
        exclude = ['user','policy_code']

class PeformanceBonusForm(forms.ModelForm):      
    class Meta:
        model = PerformanceBonus
        exclude = ['user','salary_structure_code']

 
################################################################################################

from django import forms
from .models import Employee

class AddEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ['employee_code', 'resignation_date', 'lateness_salary_deductions']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'resignation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'office_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'office_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'employee_photo_ID': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_education_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_NID': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter full address...',
                'style': 'height:80px'
            }),
            'is_roster_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_senior_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(AddEmployeeForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.FileInput, forms.CheckboxInput)):  
                field.widget.attrs['class'] = 'form-control'



from.models import Doctor,Nurse

class AddDoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        exclude = ['employee_code', 'resignation_date', 'lateness_salary_deductions']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'resignation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'office_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'office_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'employee_photo_ID': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_education_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_NID': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter full address...',
                'style': 'height:80px'
            }),
            'is_roster_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_senior_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'description': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter doctor BIO in Brief...',
            'style': 'height:80px'
        }),
          'hospital_affiliations': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter hospital affiliations...',
            'style': 'height:80px'
        }),
         'memberships': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter doctor membership...',
            'style': 'height:80px'
        }),

         'awards': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter doctor awards...',
            'style': 'height:80px'
        }),

            'education': forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Enter doctor awards...',
            'style': 'height:80px'
        }),
        'consultation_fees':forms.NumberInput(attrs={
            'class':'form-control'
        })


        }

        

    def __init__(self, *args, **kwargs):
        super(AddDoctorForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.FileInput, forms.CheckboxInput)):  
                field.widget.attrs['class'] = 'form-control'



class AddNurseForm(forms.ModelForm):
    class Meta:
        model = Nurse
        exclude = ['employee_code', 'resignation_date', 'lateness_salary_deductions']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'resignation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'office_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'office_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'employee_photo_ID': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_education_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'employee_NID': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Enter full address...',
                'style': 'height:80px'
            }),
            'is_roster_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_senior_employee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(AddNurseForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.FileInput, forms.CheckboxInput)):  
                field.widget.attrs['class'] = 'form-control'



class NoticeForm(forms.ModelForm):

    content=forms.CharField(widget=(
        forms.Textarea(attrs={
            'class':'form-control custom-textarea',
            'rows':3,
            'style':'height:200px'
        })
    ))
    class Meta:
        model = Notice
        exclude =['created_at','user']





class MonthYearForm(forms.Form):
    month = forms.IntegerField(min_value=1, max_value=12)
    year = forms.IntegerField(min_value=2000, max_value=2700)







from core.utils import DEPARTMENT_CHOICES,POSITION_CHOICES


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

  

#####################################################################

    year = forms.IntegerField(required=False, label="Year")
    month = forms.IntegerField(required=False, label="Month")
    start_year = forms.IntegerField(label='Start Year',required=False)
    end_year = forms.IntegerField(label='End Year',required=False)
    
       
   
    employee = forms.CharField(max_length=20,label='Employee',required=False)
    employee_name = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False,
        widget=forms.Select(attrs={'id': 'id_employee_name'}),
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),  # Fetch all departments
        label='Department',
        required=False,
        widget=forms.Select(
            attrs={
                'style': 'width: 200px;',  # Inline style for width
                'class': 'custom-select',  # Optional styling
            }
        ),
    )

    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),  # Fetch all departments
        label=Position,
        required=False,
        widget=forms.Select(
            attrs={
                'style': 'width: 200px;',  # Inline style for width
                'class': 'custom-select',  # Optional styling
            }
        ),
    )


    aggregation_type = forms.ChoiceField(
        choices=[
            ('month_wise', 'Month-wise'),
            ('quarter_wise', 'Quarter-wise'),
            ('year_wise', 'Year-wise'),
        ],
        required=False,
        label="Aggregation Type"
    )
