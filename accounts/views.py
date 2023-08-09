from django.core.exceptions import ValidationError
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django import forms


from main.models import Teacher, CustomUser
from accounts.forms import LoginForm


# Create your views here.


def login_view(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    User: CustomUser = get_user_model()
    if request.method == "POST":
        if request.user.is_authenticated:
            return redirect("main:dashboard")
        form: forms.Form = LoginForm(request.POST)
        if form.is_valid():
            username: str = form.cleaned_data["username"]
            password: str = form.cleaned_data["password"]
            try:
                user: CustomUser = User.objects.get(username=username)
            except User.DoesNotExist:
                messages.error(request, mark_safe("user not found with this username"))
                return redirect("accounts:login")

            if user.check_password(password):
                login(request, user)
                if user.user_type is "teacher" or "chef":
                    return redirect("main:dashboard")
                elif user.is_staff:
                    return redirect("/admin/")
            else:
                messages.error(request, "Given password for this user is incorrect")
                return redirect("accounts:login")
        else:
            messages.error(request, "Form is not valid")
            return render(request, "accounts/login.html", {"form": form})

    form: forms.Form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request: HttpRequest) -> HttpResponseRedirect:
    if request.user.is_authenticated:
        logout(request)
        return redirect("accounts:login")
    return redirect("accounts:login")
