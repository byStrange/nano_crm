from django.shortcuts import render, redirect
from django.db.models.query import QuerySet
from django.template.defaulttags import register
from django.http import (
    JsonResponse,
    HttpResponseForbidden,
    HttpRequest,
    HttpResponse,
    HttpResponseRedirect,
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.views import View
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.forms import Form

import json
from datetime import datetime, time
from typing import Dict, List
import uuid

from main.models import (
    Assign,
    Attendance,
    Class,
    Course,
    Dept,
    Student,
    Teacher,
    AttendanceClass,
)
from main.forms import CreateClassForm, CreateTeacherForm
from main.forms import RegisterStudentForm


@register.filter(name="split")
def split(value, key):
    return value.split(key)


@register.filter(name="strip")
def strip(value):
    return value.strip()


@register.filter(name="parse")
def parse(value, key):
    valid_json_string = value.replace("'", '"')[1:-1]
    list_result = json.loads("[" + valid_json_string + "]")
    return list_result[int(key)]


@login_required
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "main/dashboard.html")


class GroupsView(View):
    template_name = "main/groups.html"
    form_class = CreateClassForm

    def get(self, request: HttpRequest) -> HttpResponse:
        form: Form = self.form_class()
        assign_objects = (
            Assign.objects.filter(teacher=request.user.teacher)
            .prefetch_related("class_id", "course", "teacher")
            .all()
        )
        return render(
            request,
            self.template_name,
            {
                "assign_objects": assign_objects,
                "form": form,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form: Form = self.form_class(request.POST)
        if form.is_valid():
            return self.handle_valid_form(form, request)
        else:
            print("Form is invalid")
            groups: QuerySet[Class] = Class.objects.all()
            return render(request, self.template_name, {"groups": groups, "form": form})

    def handle_valid_form(self, form: Form, request: HttpRequest) -> HttpResponse:
        group: Class = Class(
            name=form.cleaned_data["name"], day=form.cleaned_data["day"]
        )
        if not request.user.is_staff:
            return self.create_teacher_group(form, group, request)
        else:
            return self.handle_staff_error()

    def create_teacher_group(
        self, form: Form, group: Class, request: HttpRequest
    ) -> HttpResponseRedirect:
        course_id: int = form.cleaned_data["course"]
        teacher: Teacher = Teacher.objects.get(user__username=request.user.username)
        course: Course = Course.objects.get(id=course_id)

        group.dept: Dept = teacher.dept
        group.save()

        assign: Assign = Assign(
            class_id=group,
            course=course,
            teacher=teacher,
            period=form.cleaned_data["time"],
            day=form.cleaned_data["day"],
        )
        assign.save()

        messages.success(request, "You've successfully created a group")
        return redirect("main:groups")

    def handle_staff_error(self):
        return ValidationError(
            "You are not allowed to create a class as you are not a teacher"
        )


@login_required
def group(request: HttpRequest, assign_id: int) -> HttpResponse:
    if request.method == "POST":
        pass
    attendance_class_exists: bool = False
    attendances: QuerySet[Attendance] | None = None
    period_end: bool = False
    now: datetime = datetime.now()
    assign: Assign = Assign.objects.select_related("class_id").get(id=assign_id)
    attendance_class_queryset: QuerySet[
        AttendanceClass
    ] = AttendanceClass.objects.filter(date__date=now.date(), assign=assign)
    course_period: str = assign.period
    course_start_time_str, course_end_time_str = course_period.split(" - ")
    course_start_time, course_end_time = [
        datetime.strptime(course_start_time_str, "%H:%M").time(),
        datetime.strptime(course_end_time_str, "%H:%M").time(),
    ]
    if now.time() < course_start_time or now.time() > course_end_time:
        print("what the fuck")
        period_end = True
    if attendance_class_queryset.exists():
        attendance_class_exists = True
        attendance_class: AttendanceClass = attendance_class_queryset.first()
        attendances: QuerySet[
            Attendance
        ] = attendance_class.attendance_set.select_related("student").all()

    students: QuerySet[Student] = assign.class_id.student_set.all()
    print(period_end)
    return render(
        request,
        "main/group.html",
        {
            "attendance_class_exists": attendance_class_exists,
            "assign": assign,
            "students": students,
            "current_date": timezone.now(),
            "attendances": attendances,
            "out_of_period": period_end,
        },
    )


@login_required
def take_attendance(request: HttpRequest, assign_id: int) -> JsonResponse:
    if request.method == "POST":
        try:
            now: datetime = datetime.now()
            attendance_list: Dict[str, bool] = json.loads(request.body)
            assign = Assign.objects.get(id=assign_id)
            attendance_class_queryset: QuerySet[
                AttendanceClass
            ] = AttendanceClass.objects.filter(date__date=now.date(), assign=assign)
            student_ids: List[str] = [student_id for student_id in attendance_list]
            print(student_ids, attendance_list)
            students: QuerySet[Student] = Student.objects.filter(id__in=student_ids)
            course_period: str = assign.period
            course_start_time_str, course_end_time_str = course_period.split(" - ")
            course_start_time, course_end_time = [
                datetime.strptime(course_start_time_str, "%H:%M").time(),
                datetime.strptime(course_end_time_str, "%H:%M").time(),
            ]
            if not (course_start_time <= now.time() <= course_end_time):
                return JsonResponse(
                    {"error": "Cannot update attendance outside of course period"}
                )
            if attendance_class_queryset.exists():
                attendance_class: AttendanceClass = attendance_class_queryset.first()
                _update_or_create_attendance(
                    attendance_list=attendance_list,
                    students=students,
                    attendance_class=attendance_class,
                )
                return JsonResponse(
                    {"success": "Attendance has been updated successfull"}
                )
            attendance_class: AttendanceClass = AttendanceClass(assign=assign)
            attendance_class.save()
            _update_or_create_attendance(
                attendance_list=attendance_list,
                students=students,
                attendance_class=attendance_class,
            )
            return JsonResponse({"success": "huh"})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Assign.DoesNotExist:
            return JsonResponse({"error": "group does not exists"}, status=400)


def _update_or_create_attendance(
    attendance_list: Dict[str, bool],
    students: QuerySet[Student],
    attendance_class: AttendanceClass,
) -> bool:
    try:
        if attendance_class is None:
            assign = students.first().group.assign_set.first()
            attendance_class = AttendanceClass(assign=assign)
            attendance_class.save()

        for student in students:
            student_id = str(student.id)
            attendance_status = attendance_list.get(student_id, False)
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                attendance_class=attendance_class,
                defaults={"is_present": attendance_status},
            )
        return True
    except Exception as err:
        print(
            f"WARNING _update_or_create_attendance function did not end properly, it raised error: {err}"
        )
        return False


@login_required
def teachers(request: HttpRequest) -> HttpResponse:
    # if not request.user.is_staff:
    # return redirect("main:dashboard")
    if request.method == "POST":
        form: Form = CreateTeacherForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("main:teachers")
        else:
            print(form.errors)
            return
    form: Form = CreateTeacherForm()
    teachers: QuerySet[Teacher] = Teacher.objects.all()
    return render(request, "main/teachers.html", {"teachers": teachers, "form": form})


@login_required
def register_student(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    if request.user.is_staff:
        return HttpResponseForbidden()
    if request.method == "POST":
        print(request.POST)
        form: Form = RegisterStudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("main:register_student")
        else:
            messages.error(
                request,
                mark_safe(form.errors),
            )
            return redirect("main:register_student")
    teacher: Teacher = request.user.teacher
    students: QuerySet[Student] = Student.objects.filter(
        group=None, course__dept=teacher.dept
    ).select_related("course")
    groups: QuerySet[Class] = Class.objects.filter(dept=teacher.dept)
    form: Form = RegisterStudentForm(teacher=teacher)
    return render(
        request,
        "main/register_student.html",
        {"students": students, "form": form, "groups": groups},
    )


@login_required
def students_view(request: HttpResponse) -> HttpResponse | HttpResponseForbidden:
    if request.user.is_staff:
        return HttpResponseForbidden()
    teacher: Teacher = request.user.teacher
    students: QuerySet[Student] = Student.objects.filter(
        group__dept=teacher.dept, course__dept=teacher.dept
    )
    context = {"students": students, "teacher": teacher}
    # return render(request, "template_name")


@login_required
def delete_teacher(request: HttpRequest, teacher_id: int):
    pass


@login_required
def move_student(
    request: HttpRequest, student_id: uuid.UUID, class_id: int
) -> JsonResponse:
    try:
        student: Student = Student.objects.get(id=student_id)
        group: Class = Class.objects.get(id=class_id)
    except Student.DoesNotExist or Class.DoesNotExist:
        messages.error(request, "something has burned up")
        return JsonResponse({"error": "either student or group object not found"})
    student.group: Class = group
    student.save()
    messages.success(
        request,
        mark_safe(
            f'{student.full_name} <a href="/groups/{group.id}">{group.name}</a> guruhiga muvaffaqiyatli ko\'chirildi.'
        ),
    )
    return JsonResponse({"success": True})


@login_required
def teacher(request: HttpRequest, teacher_id: uuid.UUID):
    teacher = Teacher.objects.get(id=teacher_id)

    return render(request, "main/teacher.html", {"teacher": teacher})
