import uuid
from typing import Literal

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

from typing import Type, Tuple

Choices = Tuple[Tuple[str, str]]

time_slots: Choices = (
    ("8:00 - 9:30", "8:00 - 9:30"),
    ("10:00 - 9:30", "8:30 - 9:30"),
    ("9:30 - 10:30", "9:30 - 10:30"),
    ("11:00 - 11:50", "11:00 - 11:50"),
    ("11:50 - 12:40", "11:50 - 12:40"),
    ("12:40 - 1:30", "12:40 - 1:30"),
    ("2:30 - 3:30", "2:30 - 3:30"),
    ("3:30 - 4:30", "3:30 - 4:30"),
    ("4:30 - 5:30", "4:30 - 5:30"),
)

DAYS_OF_WEEK: Choices = (
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
)


class CustomUser(AbstractUser):
    USER_TYPES: Choices = (
        ("chef", "Chef of Department"),
        ("teacher", "Teacher"),
    )
    user_type: models.CharField = models.CharField(
        max_length=10, choices=USER_TYPES, blank=True, null=True
    )

    @property
    def is_chef(self):
        return self.user_type == "chef"

    @property
    def is_teacher(self):
        return self.user_type == "teacher"


class TimeStampedModel(models.Model):
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        abstract: bool = True


class Dept(models.Model):
    name: models.CharField = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    dept: models.ForeignKey[Dept, models.CASCADE] = models.ForeignKey(
        Dept, on_delete=models.CASCADE
    )
    name: models.CharField = models.CharField(max_length=50)
    shortname: models.CharField = models.CharField(max_length=50, default="X")

    def __str__(self):
        return self.name


class Class(models.Model):
    dept: models.ForeignKey[Dept, models.CASCADE] = models.ForeignKey(
        Dept, on_delete=models.CASCADE
    )
    name: models.CharField = models.CharField(max_length=100)
    day: models.CharField = models.CharField(max_length=254)

    class Meta:
        verbose_name_plural: str = "classes"

    def __str__(self):
        return self.name


class Assign(models.Model):
    class_id: models.ForeignKey[Class, models.CASCADE] = models.ForeignKey(
        Class, on_delete=models.CASCADE
    )
    course: models.ForeignKey[Course, models.CASCADE] = models.ForeignKey(
        "Course", on_delete=models.CASCADE
    )
    teacher: models.ForeignKey = models.ForeignKey("Teacher", on_delete=models.CASCADE)
    period: models.CharField = models.CharField(
        max_length=50, choices=time_slots, default="11: - 11:50"
    )
    day: models.CharField = models.CharField(
        max_length=50, default='["Monday", "Wednesday", "Friday"]'
    )

    class Meta:
        unique_together = (("course", "class_id", "teacher"),)

    def __str__(self):
        cl = self.class_id
        te = self.teacher
        return "%s : %s" % (te.full_name, cl)


class AttendanceClass(models.Model):
    assign: models.ForeignKey[Assign, models.CASCADE] = models.ForeignKey(
        Assign, on_delete=models.CASCADE
    )
    date: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    status: models.IntegerField = models.IntegerField(default=0)

    class Meta:
        verbose_name: str = "Attendance"
        verbose_name_plural: str = "Attendance"


class Student(models.Model):
    CONDITION_CHOICES: Choices = (
        ("normal", "normal"),
        ("contract", "Kontrakt"),
        ("free", "Free"),
    )
    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    full_name: models.CharField = models.CharField(max_length=100)
    group: models.ForeignKey[Class, models.CASCADE] = models.ForeignKey(
        Class, on_delete=models.CASCADE, blank=True, null=True
    )
    course: models.ForeignKey[Course, models.CASCADE] = models.ForeignKey(
        "Course", on_delete=models.CASCADE
    )
    address: models.TextField = models.TextField(max_length=254, default="Uzbekistan")
    coins: models.IntegerField = models.IntegerField(default=0)
    phone_numbers: models.TextField = models.CharField(max_length=254)
    condition: models.CharField = models.CharField(
        choices=CONDITION_CHOICES,
        default="normal",
        max_length=10,
    )

    # Add a OneToOneField to link a student to their corresponding user account
    user: models.OneToOneField[Type[CustomUser], models.CASCADE] = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.full_name


class Chef(models.Model):
    id: uuid.UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    dept: models.ForeignKey[Dept, models.CASCADE] = models.ForeignKey(
        Dept, on_delete=models.CASCADE
    )
    full_name: models.CharField = models.CharField(max_length=254)
    user: models.OneToOneField[Type[CustomUser], models.CASCADE] = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return self.full_name + " - " + self.dept.name


class Teacher(models.Model):
    id: uuid.UUID = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    WORKING_DAYS_CHOICES: Choices = (
        ("workingdays", "ish kunlari"),
        ("everyotherday", "kun oralab"),
    )
    dept: models.ForeignKey[Dept, models.CASCADE] = models.ForeignKey(
        "Dept", on_delete=models.CASCADE, null=True, blank=True
    )
    full_name: models.CharField = models.CharField(max_length=100)
    working_days: models.CharField = models.CharField(
        max_length=254, choices=WORKING_DAYS_CHOICES
    )
    working_time: models.CharField = models.CharField(max_length=254)
    courses: models.ManyToManyField = models.ManyToManyField(
        "Course", blank=True
    )
    address: models.CharField = models.CharField(max_length=254, default="Andijon")
    phone_numbers: models.CharField = models.CharField(max_length=254, default="None")

    user: models.OneToOneField[Type[CustomUser], models.CASCADE] = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.full_name


class Attendance(models.Model):
    student: models.ForeignKey[Student, models.CASCADE] = models.ForeignKey(
        "Student", on_delete=models.CASCADE
    )
    is_present: models.BooleanField = models.BooleanField(default=False)
    attendance_class: models.ForeignKey[
        AttendanceClass, models.CASCADE
    ] = models.ForeignKey(AttendanceClass, on_delete=models.CASCADE)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.attendance_class}"
