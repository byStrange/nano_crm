import uuid

from django.db import models

from core.models import DeptMixin, UUIDMixin

# Create your models here.
class Price(DeptMixin, UUIDMixin):
    percentage = models.IntegerField()
    assign = models.OneToOneField("courses.Assign", on_delete=models.CASCADE)


class StudentPayment(DeptMixin, UUIDMixin):
    assign = models.ForeignKey("courses.Assign", on_delete=models.CASCADE)
    student = models.ForeignKey("courses.Student", on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    amount = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.student.full_name


class TeacherPayment(DeptMixin, UUIDMixin):
    assign = models.ForeignKey("courses.Assign", on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    amount = models.IntegerField()

    approved_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self) -> str:
        return self.assign.teacher.full_name