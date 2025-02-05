import random
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import QuerySet as Q
from django.test import TestCase

from core.models import Course, Dept
from accounts.models import Teacher
from courses.models import (Assign, Attendance, AttendanceClass, Class, Student)
from courses.views import _update_or_create_attendance

User = get_user_model()


class UpdateOrCreateAttendanceTest(TestCase):
    def setUp(self):
        dept: Dept = Dept.objects.create(name="TEST")
        course: Course = Course.objects.create(dept=dept, name="TEST COURSE")
        group: Class = Class.objects.create(
            dept=dept, name="G1", day="Monday, Tuesday, Wednesday"
        )
        user = User.objects.create(
            username="rakhmatullo", password="Abcd1234!", user_type="teacher"
        )
        teacher: Teacher = Teacher.objects.create(
            dept=dept,
            full_name="Fan Zhendong",
            working_days="workingdays",
            working_time="12:00",
            user=user,
        )
        assign: Assign = Assign.objects.create(
            class_id=group, course=course, teacher=teacher
        )
        AttendanceClass.objects.create(date=datetime.now().date(), assign=assign)
        Student.objects.create(
            full_name="John Doe",
            course=course,
            phone_numbers="+xx xxx xx xx",
            group=group,
        )
        Student.objects.create(
            full_name="Sugar Momma",
            course=course,
            phone_numbers="+xx xxx xx xx",
            group=group,
        )
        Student.objects.create(
            full_name="White Scout",
            course=course,
            phone_numbers="+xx xxx xx xx",
            group=group,
        )
        Student.objects.create(
            full_name="Count Dooku",
            course=course,
            phone_numbers="+xx xxx xx xx",
            group=group,
        )
        Student.objects.create(
            full_name="Dick Ramdass",
            course=course,
            phone_numbers="+xx xxx xx xx",
            group=group,
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
            attendance_class=attendance_class,  # type: ignore
        )

        self.assertFalse(result)

    def test_update_or_create_attendance_second_case(self):
        students = Student.objects.all()
        attendance_list = {
            str(student.id): random.choice([True, False]) for student in students
        }

        result = _update_or_create_attendance(
            attendance_list=attendance_list, students=students, attendance_class=None  # type: ignore
        )

        self.assertTrue(result)
