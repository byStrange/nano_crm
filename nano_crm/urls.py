from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("courses.urls", namespace="courses")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path('admin/', admin.site.urls),
    path("__debug__", include("debug_toolbar.urls"))
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
