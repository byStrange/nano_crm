from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from main.models import (
    Attendance,
    Course,
    Class,
    Student,
    Teacher,
    Assign,
    AttendanceClass,
    Course,
    Dept,
    CustomUser,
)

models = [
    Class,
    Student,
    Teacher,
    Assign,
    AttendanceClass,
    Course,
    Dept,
]


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
    list_display = ("student", "is_present", "attendance_class")
    list_select_related = ("student", "attendance_class__assign")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("student", "attendance_class")

# Register the CustomUser model with the customized UserAdmin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Attendance, AttendanceAdmin)

[admin.site.register(model) for model in models]
