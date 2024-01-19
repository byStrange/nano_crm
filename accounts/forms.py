from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms

from core.constants import DEFAULT_INPUT_ATTRS
from core.models import Course
from accounts.models import Teacher



class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class TokenRegisterForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "password1")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    # Define widgets for password fields within UserCreationForm
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget = forms.PasswordInput(
            attrs={"class": "form-control"}
        )
        self.fields["password2"].widget = forms.PasswordInput(
            attrs={"class": "form-control"}
        )


class CreateTeacherForm(forms.ModelForm):
    def __init__(self, *args, dept, **kwargs):
        super().__init__(*args, **kwargs)
        if dept:
            self.fields["courses"].queryset = Course.objects.filter(dept=dept)

    class Meta:
        model = Teacher
        fields = [
            "full_name",
            "working_days",
            "working_time",
            "courses",
            "address",
            "phone_numbers",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "working_days": forms.Select(attrs=DEFAULT_INPUT_ATTRS),
            "working_time": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "faculties": forms.SelectMultiple(attrs=DEFAULT_INPUT_ATTRS),
            "address": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "phone_numbers": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
        }