from django import forms
from .models import Order
import re

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']

PAYMENT_CHOICES = [
    ('mpesa', 'Vodacom M-Pesa'),
    ('mixx', 'Mixx by YAS'),
    ('airtel', 'Airtel Money'),
    ('stripe', 'Credit/Debit Card (Stripe)'),
    ('bank', 'Bank Transfer'),
]

BANK_CHOICES = [
    ('CRDB', 'CRDB'),
    ('NMB', 'NMB'),
    ('NBC', 'NBC'),
    ('TCB', 'TCB'),
]

class CheckoutForm(forms.Form):
    first_name = forms.CharField(
        max_length=100, required=True, label="First Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=100, required=True, label="Last Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True, label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=15, required=True, label="Phone Number",
        initial='000000000001',  # <-- default sandbox number
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'tel',
            'pattern': r'^\+?[0-9]{7,15}$',
            'placeholder': '255712345678',
            'title': 'Enter a valid phone number'
        })
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Delivery Address',
            'rows': 3
        }),
        required=True, label="Delivery Address"
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES, required=True, label="Payment Method",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleBankDropdown(this.value)'
        })
    )
    bank_name = forms.ChoiceField(
        choices=BANK_CHOICES,
        required=False,
        label="Select Bank",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_bank_name'
        })
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\+?[0-9]{7,15}$', phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        bank_name = cleaned_data.get("bank_name")

        if payment_method == "bank" and not bank_name:
            self.add_error('bank_name', "Please select a bank for bank transfer.")
