from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from accounts.models import Chef, CustomUser, Teacher, RegisterToken


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            None,
            {"fields": ("first_name", "user_type", "dept")},
        ),
    )
    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {"fields": ("user_type", "dept")},
        ),
    )  # type: ignore


admin.site.unregister(Group)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Teacher)
admin.site.register(Chef)
admin.site.register(RegisterToken)
