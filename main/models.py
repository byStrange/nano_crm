from typing import Literal
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

time_slots = (
    ("8:00 - 9:30", "8:00 - 9:30"),
    ("8:30 - 9:30", "8:30 - 9:30"),
    ("9:30 - 10:30", "9:30 - 10:30"),
    ("11:00 - 11:50", "11:00 - 11:50"),
    ("11:50 - 12:40", "11:50 - 12:40"),
    ("12:40 - 1:30", "12:40 - 1:30"),
    ("2:30 - 3:30", "2:30 - 3:30"),
    ("3:30 - 4:30", "3:30 - 4:30"),
    ("4:30 - 5:30", "4:30 - 5:30"),
)

DAYS_OF_WEEK = (
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
)


class CustomUser(AbstractUser):
    USER_TYPES = (
        ("chef", "Chef of Department"),
        ("teacher", "Teacher"),
    )
    user_type = models.CharField(
        max_length=10, choices=USER_TYPES, blank=True, null=True
    )

    @property
    def is_chef(self):
        return self.user_type == "chef"

    @property
    def is_teacher(self):
        return self.user_type == "teacher"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Dept(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    dept = models.ForeignKey(Dept, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    shortname = models.CharField(max_length=50, default="X")

    def __str__(self):
        return self.name


class Class(models.Model):
    dept = models.ForeignKey(Dept, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    day = models.CharField(max_length=254)

    class Meta:
        verbose_name_plural = "classes"

    def __str__(self):
        return self.name


class Assign(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    teacher = models.ForeignKey("Teacher", on_delete=models.CASCADE)
    period = models.CharField(max_length=50, choices=time_slots, default="11: - 11:50")
    day = models.CharField(max_length=50, default='["Monday", "Wednesday", "Friday"]')

    class Meta:
        unique_together = (("course", "class_id", "teacher"),)

    def __str__(self):
        cl = self.class_id
        te = self.teacher
        return "%s : %s" % (te.full_name, cl)


class AttendanceClass(models.Model):
    assign = models.ForeignKey(Assign, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance"


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    group = models.ForeignKey(Class, on_delete=models.CASCADE, blank=True, null=True)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    address = models.TextField(max_length=254, default="Uzbekistan")
    coins = models.IntegerField(default=0)
    phone_numbers = models.TextField(max_length=254)
    condition = models.CharField(
        choices=(("normal", "normal"), ("contract", "Kontrakt"), ("free", "Free")),
        default="normal",
        max_length=10,
    )

    # Add a OneToOneField to link a student to their corresponding user account
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.full_name


class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    WORKING_DAYS_CHOICES = (
        ("workingdays", "ish kunlari"),
        ("everyotherday", "kun oralab"),
    )
    dept = models.ForeignKey("Dept", on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    working_days = models.CharField(max_length=254, choices=WORKING_DAYS_CHOICES)
    working_time = models.CharField(max_length=254)
    courses = models.ManyToManyField("Course", blank=True)
    address = models.CharField(max_length=254, default="Andijon")
    phone_numbers = models.CharField(max_length=254, default="None")
       
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.full_name


class Attendance(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)
    attendance_class = models.ForeignKey(AttendanceClass, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.attendance_class}"
