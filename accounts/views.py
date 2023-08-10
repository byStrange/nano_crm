from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe

from accounts.forms import LoginForm
from main.models import Teacher

# Create your views here.


def login_view(request):
    User = get_user_model()
    if request.method == "POST":
        if request.user.is_authenticated:
            return redirect("main:dashboard")
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                messages.error(
                    request, mark_safe("user not found with this username"))
                return redirect("accounts:login")
            
            if user.check_password(password):
                login(request, user)
                if user.user_type == "teacher" or user.user_type == "chef":
                    return redirect("main:dashboard")
                elif user.is_staff:
                    return redirect("/admin/")
            else:
                messages.error(
                    request, "Given password for this user is incorrect")
                return redirect("accounts:login")
        else:
            messages.error(request, "Form is not valid")
            return render(request, "accounts/login.html", {"form": form})

    form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect("accounts:login")
    return redirect("accounts:login")
