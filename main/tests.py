from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import QuerySet as Q

from datetime import datetime
import random

from main.views import _update_or_create_attendance
from main.models import (
    AttendanceClass,
    Attendance,
    Student,
    Course,
    Class,
    Dept,
    Assign,
    Class,
    Teacher,
)

User = get_user_model()


class UpdateOrCreateAttendanceTest(TestCase):
    def setUp(self):
        dept = Dept.objects.create(name="TEST")
        course = Course.objects.create(dept=dept, name="TEST COURSE")
        group = Class.objects.create(
            dept=dept, name="G1", day="Monday, Tuesday, Wednesday"
        )
        user = User.objects.create(
            username="rakhmatullo", password="Abcd1234!", user_type="teacher"
        )
        teacher = Teacher.objects.create(
            dept=dept,
            full_name="Fan Zhendong",
            working_days="workingdays",
            working_time="12:00",
            user=user,
        )
        assign = Assign.objects.create(
            class_id=group, course=course, teacher=teacher
        )
        AttendanceClass.objects.create(
            date=datetime.now().date(), assign=assign
        )
        Student.objects.create(
            full_name="John Doe", course=course, phone_numbers="+xx xxx xx xx", group=group
        )
        Student.objects.create(
            full_name="Sugar Momma", course=course, phone_numbers="+xx xxx xx xx", group=group
        )
        Student.objects.create(
            full_name="White Scout", course=course, phone_numbers="+xx xxx xx xx", group=group
        )
        Student.objects.create(
            full_name="Count Dooku", course=course, phone_numbers="+xx xxx xx xx", group=group
        )
        Student.objects.create(
            full_name="Dick Ramdass", course=course, phone_numbers="+xx xxx xx xx", group=group
        )

    def test_update_or_create_attendance(self):
        students = Student.objects.all()
        attendance_class = AttendanceClass.objects.first()

        attendance_list = {
            str(student.id): random.choice([True, False]) for student in students
        }
        
        result = _update_or_create_attendance(
            attendance_list=attendance_list,
            students=students,
            attendance_class=attendance_class,
        )

        self.assertTrue(result)

    def test_update_or_create_attendance_second_case(self):
        students = Student.objects.all()
        attendance_list = {
            str(student.id): random.choice([True, False]) for student in students
        }

        result = _update_or_create_attendance(
            attendance_list=attendance_list, students=students, attendance_class=None
        )

        self.assertTrue(result)
