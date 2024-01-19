from django.db import models

from core.constants import time_slots, DAYS_OF_WEEK
from core.models import UUIDMixin, DeptMixin


class Class(DeptMixin):
    name = models.CharField(max_length=100)
    day = models.CharField(max_length=254)

    class Meta:
        verbose_name_plural: str = "classes"

    def __str__(self):
        return self.name


class Assign(models.Model):
    class_id = models.ForeignKey("Class", on_delete=models.CASCADE)
    course = models.ForeignKey("core.Course", on_delete=models.CASCADE)
    teacher = models.ForeignKey("accounts.Teacher", on_delete=models.CASCADE)
    period = models.CharField(max_length=50, choices=time_slots, default="8:00 - 9:30")
    day = models.CharField(max_length=50, default='["Monday", "Wednesday", "Friday"]')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("course", "class_id", "teacher"),)

    def get_monthly_attendance(self, year, month):
        attendance_data = (
            AttendanceClass.objects.filter(
                date__year=year,
                date__month=month,
                assign=self,
            )
        )

        return attendance_data

    def __str__(self):
        cl = self.class_id
        te = self.teacher
        return "%s : %s" % (te.full_name, cl)


class AttendanceClass(models.Model):
    assign = models.ForeignKey("Assign", on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name: str = "Attendance Session"
        verbose_name_plural: str = "Attendance Sessions"


class Student(UUIDMixin):
    CONDITION_CHOICES = (
        ("normal", "normal"),
        ("contract", "Kontrakt"),
        ("free", "Free"),
    )
    full_name = models.CharField(max_length=100)
    groups = models.ManyToManyField("Class", blank=True)
    course = models.ForeignKey("core.Course", on_delete=models.CASCADE)
    address = models.TextField(max_length=254, default="Uzbekistan")
    coins = models.IntegerField(default=0)
    phone_numbers = models.CharField(max_length=254)
    condition = models.CharField(
        choices=CONDITION_CHOICES,
        default="normal",
        max_length=10,
    )

    def __str__(self):
        return self.full_name
    def get_attendance_on_day(self, day):
        try:
            attendance = self.attendance_set.get(date=day) # type: ignore
            return attendance
        except Attendance.DoesNotExist:
            return None

class Attendance(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)
    attendance_class = models.ForeignKey("AttendanceClass", on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.attendance_class}"
