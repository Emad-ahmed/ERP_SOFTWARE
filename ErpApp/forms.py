# forms.py

from django import forms
from .models import CustomerList, PartyList,  Product, Employee, Voucher

class CustomerListForm(forms.ModelForm):
    class Meta:
        model = CustomerList
        fields = [
            'Debtors_Name',
            'Print_As',
            'Phone',
            'Contact_Person',
            'Address',
            'Email',
            'Branch',
        ]
        widgets = {
            'Debtors_Name': forms.TextInput(attrs={'placeholder': 'Enter Debtors Name'}),
            'Print_As': forms.TextInput(attrs={'placeholder': 'Enter Print As'}),
            'Phone': forms.TextInput(attrs={'placeholder': 'Enter Phone'}),
            'Contact_Person': forms.TextInput(attrs={'placeholder': 'Enter Contact Person'}),
            'Address': forms.Textarea(attrs={'placeholder': 'Enter Address'}),
            'Email': forms.EmailInput(attrs={'placeholder': 'Enter Email'}),
            'Branch': forms.TextInput(attrs={'placeholder': 'Enter Branch'}),
        }


class PartyListForm(forms.ModelForm):
    class Meta:
        model = PartyList
        fields = [
            'Party_Name',
            'Print_As',
            'Phone',
            'Contact_Person',
            'Address',
            'Email',
            'Branch',
        ]
        widgets = {
            'Party_Name': forms.TextInput(attrs={'placeholder': 'Enter Party Name'}),
            'Print_As': forms.TextInput(attrs={'placeholder': 'Enter Print As'}),
            'Phone': forms.TextInput(attrs={'placeholder': 'Enter Phone'}),
            'Contact_Person': forms.TextInput(attrs={'placeholder': 'Enter Contact Person'}),
            'Address': forms.Textarea(attrs={'placeholder': 'Enter Address'}),
            'Email': forms.EmailInput(attrs={'placeholder': 'Enter Email'}),
            'Branch': forms.TextInput(attrs={'placeholder': 'Enter Branch'}),
        }





class ProductUpdateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'sku',
            'uom',
            'vendor',
            'brand',
            'category',
            'sub_category',
            'product_type',
            'variation_name',
            'variation_values',
            'barcode_type',
            'alert_quantity',
            'lead_time',
            'reorder_quantity',
            'reorder_date',
            'expires_in',
            'tax',
            'purchase_price',
            'transport_cost',
            'other_cost',
            'cogs',
            'profit_margin_base_seeling',
            'profit_margin_mrp',
            'base_selling_price',
            'mrp',
            'opening_stock',
            'inventory_location',
            'weight',
            'position',
            'rack',
            'row',
            'image',
            'product_description',
            'instruction',
            'custom_field_1',
            'custom_field_2',
            'custom_field_3',
            'selling',
        ]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
        
            'name',

            'uom',
            'vendor',
            'brand',
            'category',
            'sub_category',
            'product_type',
            'variation_name',
            'variation_values',
            'barcode_type',
            'alert_quantity',
            'lead_time',
            'reorder_quantity',
            'reorder_date',
            'expires_in',
            'tax',
            'purchase_price',
            'transport_cost',
            'other_cost',
           
            'profit_margin_base_seeling',
            'profit_margin_mrp',
           

            'opening_stock',
            'inventory_location',
            'weight',
            'position',
            'rack',
            'row',
            'image',
            'product_description',
            'instruction',
            'custom_field_1',
            'custom_field_2',
            'custom_field_3',
            'selling',
        ]

class EmployeeForm(forms.ModelForm):
    class Meta:

        model = Employee
        fields = '__all__'

        widgets = {
                'birthday': forms.DateInput(attrs={'type': 'date'}),
                'hired_date': forms.DateInput(attrs={'type': 'date'}),
                'termination_date': forms.DateInput(attrs={'type': 'date'}),
        }

class VoucherForm(forms.ModelForm):
    class Meta:
        model = Voucher
        exclude = ['vouchernumber', 'date']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add 'form-control' class to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
