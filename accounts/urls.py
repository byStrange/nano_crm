from django.urls import path

from accounts import views

app_name = "accounts"

urlpatterns = [
    path("token-register/<str:tk>/", views.token_register, name="token_register"),
    path("token-register/<str:tk>/revoke/", views.revoke_token, name="revoke_token"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout")
]
