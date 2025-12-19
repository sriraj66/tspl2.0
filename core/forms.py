from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import PlayerRegistration


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Email',
            'required': "true",
            "autocomplete": "off"
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Password',
            'required': "true",
            "autocomplete": "off"
        })
    )

class RegisterForm(UserCreationForm):
    username = forms.EmailField(
        label="Email ",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ie , ...@gmail.com'
        })
    )
    
    first_name = forms.CharField(
        label="First Name",
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a password'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']


class PlayerRegistrationForm(forms.ModelForm):
    class Meta:
        model = PlayerRegistration
        fields = [
            'player_name',
            'father_name',
            'category',
            'age',
            'dob',
            'gender',
            'occupation',
            'tshirt_size',
            'mobile',
            'wathsapp_number',
            'email',
            'adhar_card',
            'player_image',
            'social_media_link',
            'district',
            'pin_code',
            'address',
            'first_preference',
            'batting_arm',
            'role',
        ]
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'player_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 60}),
            'occupation': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'tshirt_size': forms.Select(attrs={'class': 'form-select'}),
            'mobile': forms.NumberInput(attrs={'class': 'form-control', 'min': 1000000000, 'max': 9999999999}),
            'wathsapp_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1000000000, 'max': 9999999999}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adhar_card': forms.NumberInput(attrs={'class': 'form-control' ,'min': 100000000000, 'max': 999999999999}),
            'player_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'social_media_link': forms.URLInput(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-select'}),
            'pin_code': forms.NumberInput(attrs={'class': 'form-control','min': 100000, 'max': 999999}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'first_preference': forms.Select(attrs={'class': 'form-select'}),
            'batting_arm': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'player_name': 'Player Name',
            'father_name': 'Father\'s Name',
            'category': 'Category',
            'age': 'Player Age',
            'occupation': 'Player Occupation',
            'dob': 'Date of Birth',
            'gender': 'Gender',
            'tshirt_size': 'T-Shirt Size',
            'mobile': 'Mobile Number',
            'wathsapp_number': 'WhatsApp Number',
            'email': 'Email Address',
            'adhar_card': 'Aadhar Card Number',
            'social_media_link': 'Social Media Profile Link',
            'player_image': 'Player Image',
            'district': 'District',
            'pin_code': 'PIN Code',
            'address': 'Address',
            'first_preference': 'First Preference',
            'batting_arm': 'Batting Arm',
            'role': 'Player Role',
        }
        