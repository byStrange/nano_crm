from typing import List, Tuple

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpRequest

from main.models import (Assign, Attendance, AttendanceClass, Chef, Class,
                         Course, CustomUser, Dept, Student, Teacher)

ListDisplay = List[str] | Tuple[str]

models = [Class, Student, Teacher, Assign, AttendanceClass, Course, Dept, Chef]



class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {"fields": ("user_type",)},
        ),
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {"fields": ("user_type",)},
        ),
    )


class AttendanceAdmin(admin.ModelAdmin):
    list_display: ListDisplay = ("student", "is_present", "attendance_class")
    list_select_related: ListDisplay = ("student", "attendance_class__assign")

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return (
            super().get_queryset(request).select_related("student", "attendance_class")
        )


# Register the CustomUser model with the customized UserAdmin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Attendance, AttendanceAdmin)

[admin.site.register(model) for model in models]
