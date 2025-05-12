from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.models import User


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    phone = forms.CharField(max_length=20)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Check if the email is already in use
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already taken.")
        
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        if not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        
        if len(phone) < 10:
            raise ValidationError("Phone number must be at least 10 digits long.")

        phone_regex = re.compile(r'^\+?(\d{1,4})?(\d{10,15})$')
        if not phone_regex.match(phone):
            raise ValidationError("Please enter a valid phone number.")

        return phone

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        if hasattr(user, 'profile'):
            user.profile.phone = self.cleaned_data['phone']
            user.profile.save()

        return user
