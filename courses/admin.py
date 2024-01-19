from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpRequest

from courses.models import Assign, Attendance, AttendanceClass, Class, Student

models = [Class, Student, Assign, AttendanceClass]


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "is_present", "attendance_class")
    list_select_related = ("student", "attendance_class__assign")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return (
            super().get_queryset(request).select_related("student", "attendance_class")
        )


# Register the CustomUser model with the customized UserAdmin
admin.site.register(Attendance, AttendanceAdmin)

[admin.site.register(model) for model in models]
