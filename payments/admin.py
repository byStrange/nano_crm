from django.contrib import admin

from payments.models import Price, StudentPayment, TeacherPayment

# Register your models here.

admin.site.register(Price)
admin.site.register(StudentPayment)
admin.site.register(TeacherPayment)
