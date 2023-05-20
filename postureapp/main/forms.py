from django import forms
from .models import User, FeedBack


# creating login, register and feedback forms.
class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), label='First Name')
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), label='Last Name')
    email = forms.EmailField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Confirm password')
    profile_picture = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), label='Profile Picture', required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'password2', 'profile_picture')

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2


class FeedBackForm(forms.ModelForm):
    opinion = forms.CharField(max_length=300, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}), label='')

    class Meta:
        model = FeedBack
        exclude = ['author']