from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import EmergencyContact

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    mobile_number = forms.CharField(
        required=True,
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be in the format: '+911234567890'. Up to 15 digits allowed."
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91XXXXXXXXXX'
        }),
        help_text="Enter number with country code (e.g., +911234567890)"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'mobile_number', 'password1', 'password2']

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data.get('mobile_number')
        # Ensure mobile number has only digits and starts with a '+'
        if mobile_number:
            mobile_number = ''.join(filter(lambda x: x.isdigit() or x == '+', mobile_number))
            if not mobile_number.startswith('+'):
                mobile_number = '+' + mobile_number
        return mobile_number



class EmergencyContactForm(forms.ModelForm):
    name = forms.CharField(
        min_length=2,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contact Name'
        }),
        help_text='Full name of emergency contact'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    
    phone = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be in format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91XXXXXXXXXX'
        }),
        help_text='Enter number with country code (e.g., +911234567890)'
    )
    
    relationship = forms.CharField(
        widget=forms.Select(choices=[
            ('', 'Select Relationship'),
            ('PARENT', 'Parent'),
            ('SPOUSE', 'Spouse'),
            ('SIBLING', 'Sibling'),
            ('CHILD', 'Child'),
            ('RELATIVE', 'Relative'),
            ('FRIEND', 'Friend'),
            ('OTHER', 'Other')
        ], attrs={'class': 'form-control'})
    )

    class Meta:
        model = EmergencyContact
        fields = ['name', 'email', 'phone', 'relationship']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove any spaces or special characters except '+'
            phone = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))
            if not phone.startswith('+'):
                phone = '+' + phone
        return phone