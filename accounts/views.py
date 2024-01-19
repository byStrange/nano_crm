from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.utils.safestring import mark_safe

from courses.views import is_chef
from accounts.helpers import generate_token
from accounts.models import RegisterToken
from accounts.forms import LoginForm, TokenRegisterForm


def revoke_token(request: HttpRequest, tk: str):
    if is_chef(request):
        if request.method == "POST":
            try:
                token = RegisterToken.objects.select_related("teacher", "dept").get(
                    token=tk
                )
            except RegisterToken.DoesNotExist:
                return render(request, "404.html")
            token.delete()
            new_token = generate_token()

            new_register_token = RegisterToken(
                token=new_token, teacher=token.teacher, dept=token.dept
            )
            new_register_token.save()
            messages.success(request, "token for this teacher revoked successfully")
            return redirect("courses:teacher", teacher_id=new_register_token.teacher.id)
        else:
            return HttpResponseNotAllowed(["POST"])
    else:
        return render(request, "403.html")


def token_register(request: HttpRequest, tk: str):
    User = get_user_model()
    try:
        token = RegisterToken.objects.select_related("teacher").get(token=tk)
    except RegisterToken.DoesNotExist:
        return render(request, "404.html")
    if token.is_valid():
        print("token is valid")
        if request.method == "POST":
            form = TokenRegisterForm(request.POST)
            if form.is_valid():
                print("form is valid")
                # Check if the username already exists
                username = form.cleaned_data.get("username")
                if User.objects.filter(username=username).exists():
                    messages.error(request, "Username already exists")
                    return render(
                        request,
                        "accounts/token_register.html",
                        {"form": form, "teacher": token.teacher},
                    )
                user = form.save(commit=False)
                user.user_type = "teacher"
                user.dept = token.dept
                user.save()
                token.teacher.user = user
                token.teacher.save()
                login(request, user)
                token.delete()
                return redirect("courses:dashboard")
            else:
                print(form.errors)
                messages.error(request, "Form is not a valid" + form.errors.as_text())
                return render(
                    request,
                    "accounts/token_register.html",
                    {"form": form, "teacher": token.teacher},
                )
        form = TokenRegisterForm
        return render(
            request,
            "accounts/token_register.html",
            {"form": form, "teacher": token.teacher},
        )
    else:
        messages.error(
            request,
            "Your token has expired or there is already account attached to this teacher",
        )
        return JsonResponse(
            {"error": "Your token has expired or there is no need to this link"}
        )


def login_view(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    User = get_user_model()
    if request.method == "POST":
        if request.user.is_authenticated:
            return redirect("courses:dashboard")
        form: forms.Form = LoginForm(request.POST)
        if form.is_valid():
            username: str = form.cleaned_data["username"]
            password: str = form.cleaned_data["password"]
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                messages.error(request, mark_safe("user not found with this username"))
                return redirect("accounts:login")

            if user.check_password(password):
                login(request, user)
                if user.user_type == "teacher" or user.user_type == "chef":  # type: ignore
                    return redirect("courses:dashboard")
                elif user.is_staff:  # type: ignore
                    return redirect("/admin/")
            else:
                messages.error(request, "Given password for this user is incorrect")
                return redirect("accounts:login")
        else:
            messages.error(request, "Form is not valid")
            return render(request, "accounts/login.html", {"form": form})

    form: forms.Form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(
    request: HttpRequest,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    if request.user.is_authenticated:
        logout(request)
        return redirect("accounts:login")
    return redirect("accounts:login")
