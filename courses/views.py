import json
import uuid
from calendar import monthrange
from datetime import datetime
from typing import Dict, List

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.forms import Form
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import redirect, render
from django.template.defaulttags import register
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View

from accounts.forms import CreateTeacherForm
from accounts.helpers import generate_token
from accounts.models import Chef, RegisterToken, Teacher
from core.models import Course
from courses.forms import CreateClassForm, CreateCourseForm, RegisterStudentForm
from courses.models import Assign, Attendance, AttendanceClass, Class, Student
from payments.forms import StudentPaymentForm
from payments.models import Price, StudentPayment

print(timezone.now())
print(datetime.now())


def is_valid_user(request: HttpRequest) -> bool:
    if request.user.user_type in ("teacher", "chef") and hasattr(request.user, "dept"):  # type: ignore
        return True
    return False


def is_chef(request: HttpRequest) -> bool:
    if is_valid_user(request):
        return request.user.user_type == "chef"  # type: ignore
    return False


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


@register.filter(name="generate_month_days")
def generate_month_days(year, month):
    _, last_day = monthrange(year, month)
    return [datetime(year, month, day) for day in range(1, last_day + 1)]

@register.filter(name="get_now")
def get_now():
    return timezone.localtime(timezone.now()).date()

@register.filter
def get_attendance_on_day(student, day):
    try:
        print(day)
        attendance: Attendance = Attendance.objects.get(student=student, date=day)
        print("ATTENDANCE EXISTS", attendance.is_present, day)
        return attendance.is_present
    except Attendance.DoesNotExist:
        print("ATTENDANCE does not  EXISTS", day)
        return None


@register.filter
def get_attendance_class_on_day(assign, day):
    try:
        a = AttendanceClass.objects.get(assign=assign, date__day=day)
        return True
    except AttendanceClass.DoesNotExist:
        return None


@login_required
def index(
    request: HttpRequest,
) -> HttpResponse | HttpResponsePermanentRedirect | HttpResponseRedirect:
    user = request.user
    if request.user.is_authenticated:
        context = {}
        if user.user_type == "teacher":  # type: ignore
            user = Teacher.objects.get(user=user)
            teacher_assigns = Assign.objects.filter(teacher=user).select_related(
                "class_id", "course", "price"
            )
            total_salary = 0
            students_length = 0
            for i in teacher_assigns:
                percentage_per_student = i.price.percentage  # type: ignore
                price_of_this_group = i.course.price
                students_length += i.class_id.student_set.count()  # type: ignore
                for i in range(i.class_id.student_set.count()):
                    total_salary += price_of_this_group / 100 * percentage_per_student
            else:
                context["total_salary"] = total_salary
                context["students_length"] = students_length

            context["teacher_assigns"] = teacher_assigns
        elif user.user_type == "chef":  # type: ignore
            user = Chef.objects.select_related("user").get(user=user)
            students_length = Student.objects.filter(
                groups__dept=user.user.dept
            ).count()
            context["students_length"] = students_length
            assigns = (
                Assign.objects.filter(course_id__dept=user.user.dept)
                .select_related("course", "class_id")
                .all()
            )
            total_salary = 0
            for assign in assigns:
                price_of_this_group = assign.course.price  # type: ignore
                for i in range(assign.class_id.student_set.count()):
                    total_salary += price_of_this_group
            else:
                context["teacher_assigns"] = assigns
                context["total_salary"] = total_salary

        return render(request, "courses/dashboard.html", context)
    else:
        return redirect("accounts:login")


@login_required
def courses(request):
    if request.user.user_type == "chef" and hasattr(request.user, "dept"):
        if request.method == "POST":
            form = CreateCourseForm(request.POST)
            if form.is_valid():
                print("form is valid")
                course = form.save(commit=False)
                print("errro raised here")
                course.dept = request.user.dept
                course.save()
                print("error on saving")
                messages.success(request, "Course created successfully")
                return redirect("courses:courses")
            else:
                messages.error(request, form.errors.as_text())
                return redirect("courses:courses")
        dept_courses = Course.objects.filter(dept=request.user.dept)
        form = CreateCourseForm()
        return render(
            request, "courses/courses.html", {"courses": dept_courses, "form": form}
        )
    return JsonResponse({"error": "not allowed"})


@login_required
def edit_course(request, course_id):
    if is_chef(request):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return render(request, "courses/404.html", status=404)
        if request.method == "POST":
            form = CreateCourseForm(request.POST, instance=course)
            if form.is_valid():
                form.save()
                messages.success(request, "Course edited successfully")
                return redirect("courses:course", course_id=course_id)
            else:
                messages.error(request, form.errors.as_text())
                return redirect("courses:course", course_id=course_id)
        form = CreateCourseForm(
            initial={
                "name": course.name,
                "shortname": course.shortname,
                "price": course.price,
            }
        )
        return render(request, "courses/course.html", {"form": form, "course": course})
    else:
        return render(request, "403.html", status=403)


class GroupsView(View):
    template_name = "courses/groups.html"
    form_class = CreateClassForm

    def get(self, request: HttpRequest) -> HttpResponse:
        user = request.user
        form: Form = self.form_class(dept=user.dept)  # type: ignore
        assign_objects = Assign.objects.select_related("class_id", "course", "teacher")

        if hasattr(user, "teacher"):
            assign_objects = assign_objects.filter(teacher=user.teacher)  # type: ignore
        elif hasattr(request.user, "chef"):
            assign_objects = assign_objects.filter(class_id__dept=user.dept)  # type: ignore
        return render(
            request,
            self.template_name,
            {
                "assign_objects": assign_objects,
                "form": form,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse | ValidationError:
        form: Form = self.form_class(request.POST, dept=request.user.dept)  # type: ignore
        if form.is_valid():
            return self.handle_valid_form(form, request)
        else:
            print("Form is invalid")
            groups: QuerySet[Class] = Class.objects.all()
            return render(request, self.template_name, {"groups": groups, "form": form})

    def handle_valid_form(
        self, form: Form, request: HttpRequest
    ) -> HttpResponse | ValidationError:
        group: Class = Class(
            name=form.cleaned_data["name"], day=form.cleaned_data["day"]
        )
        if request.user.user_type in ("chef", "teacher") and hasattr(request.user, "dept"):  # type: ignore
            return self.create_teacher_group(form, group, request)
        else:
            return self.handle_staff_error()

    def create_teacher_group(
        self, form: Form, group: Class, request: HttpRequest
    ) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
        course_id: int = form.cleaned_data.get("course")
        teacher_id: str = form.cleaned_data.get("teacher")
        percentage: int = form.cleaned_data.get("percentage")
        course: Course = Course.objects.get(id=course_id)
        teacher = Teacher.objects.get(id=teacher_id)
        group.dept = request.user.dept  # type: ignore
        group.save()
        assign: Assign = Assign(
            class_id=group,
            course=course,
            teacher=teacher,
            period=form.cleaned_data["time"],
            day=form.cleaned_data["day"],
        )
        assign.save()
        print(assign)
        Price.objects.create(percentage=percentage, assign=assign, dept=teacher.dept)

        messages.success(request, "You've successfully created a group")
        return redirect("courses:groups")

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
    monthly_attendance = assign.get_monthly_attendance(2024, 1)
    print(monthly_attendance)
    attendance_class_queryset: QuerySet[
        AttendanceClass
    ] = AttendanceClass.objects.filter(date=now.date(), assign=assign)
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
        attendance_class: AttendanceClass | None = attendance_class_queryset.first()
        attendances = attendance_class.attendance_set.select_related("student").all()  # type: ignore

    students: QuerySet[Student] = assign.class_id.student_set.all()  # type: ignore
    print(period_end)
    return render(
        request,
        "courses/group.html",
        {
            "monthly_attendance": monthly_attendance,
            "attendance_class_exists": attendance_class_exists,
            "assign": assign,
            "students": students,
            "current_date": datetime.now(),
            "attendances": attendances,
            "out_of_period": period_end,
        },
    )


@login_required
def take_attendance(request: HttpRequest, assign_id: int) -> JsonResponse:
    if request.method == "POST":
        try:
            now: datetime = datetime.now()
            data = json.loads(request.body)
            attendance_list: Dict[str, bool] = data.get("data")

            date = data.get("date")
            if not date:
                date = now.date()
            else:
                date = datetime.strptime(date, "%Y-%m-%d").date()


            print("GOT DATA AS", date)

            assign = Assign.objects.get(id=assign_id)
            print(date)
            attendance_class_queryset = AttendanceClass.objects.filter(date=date, assign=assign)

            print(AttendanceClass.objects.filter(date="2024-01-01"))
            student_ids: List[str] = [student_id for student_id in attendance_list]
            students: QuerySet[Student] = Student.objects.filter(id__in=student_ids)
            course_period: str = assign.period
            course_start_time_str, course_end_time_str = course_period.split(" - ")
            course_start_time, course_end_time = [
                datetime.strptime(course_start_time_str, "%H:%M").time(),
                datetime.strptime(course_end_time_str, "%H:%M").time(),
            ]

            if not (course_start_time <= now.time() <= course_end_time) and request.user.user_type != "chef":  # type: ignore
                return JsonResponse(
                    {"error": "Cannot update attendance outside of course period"}
                )
            if attendance_class_queryset.exists():
                attendance_class: AttendanceClass = attendance_class_queryset.first()  # type: ignore
                print("Attendance exists: id=", attendance_class.pk)
                _update_or_create_attendance(
                    attendance_list=attendance_list,
                    students=students,
                    attendance_class=attendance_class,
                )
                return JsonResponse(
                    {"success": "Attendance has been updated successfull"}
                )
            attendance_class: AttendanceClass = AttendanceClass(
                assign=assign, date=date
            )
            print(
                "ATTendance class did not found, creating new one with \ndate: ", date
            )
            print(attendance_class.date)
            attendance_class.save()

            a = AttendanceClass.objects.filter(date=date, assign=assign)
            print(a)
            print("saved and id=", attendance_class.pk)
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
    return JsonResponse({"error": "Only POST method allowed"})


def _update_or_create_attendance(
    attendance_list: Dict[str, bool],
    students: QuerySet[Student],
    attendance_class: AttendanceClass,
) -> bool:
    try:
        if attendance_class is None:
            assign = students.first().group.assign_set.first()  # type: ignore
            attendance_class = AttendanceClass(assign=assign)
            attendance_class.save()

        for student in students:
            student_id = str(student.id)
            print(student_id, attendance_list.get(student_id))
            attendance_status = attendance_list.get(student_id, False)
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                attendance_class=attendance_class,
                defaults={
                    "is_present": attendance_status,
                    "date": attendance_class.date,
                },
            )
            print(attendance, created)
        return True
    except Exception as err:
        print(
            f"WARNING _update_or_create_attendance function did not end properly, it raised error: {err}"
        )
        return False


@login_required
def teachers(request: HttpRequest) -> HttpResponse:
    # if not request.user.is_staff:
    # return redirect("courses:dashboard")
    if is_chef(request):
        if request.method == "POST":
            form: CreateTeacherForm = CreateTeacherForm(request.POST, dept=request.user.dept)  # type: ignore
            if form.is_valid():
                teacher = form.save(commit=False)
                teacher.dept = request.user.dept  # type: ignore
                teacher.save()
                token = generate_token()
                register_token = RegisterToken(dept=request.user.dept, teacher=teacher, token=token)  # type: ignore
                register_token.save()
                return redirect("courses:teachers")
        form: CreateTeacherForm = CreateTeacherForm(dept=request.user.dept)  # type: ignore
        teachers: QuerySet[Teacher] = (
            Teacher.objects.filter(dept=request.user.dept)  # type: ignore
            .prefetch_related("assign_set", "assign_set__class_id")
            .all()
        )
        return render(
            request, "courses/teachers.html", {"teachers": teachers, "form": form}
        )
    else:
        return render(request, "403.html", status=403)


@login_required
def register_student(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    if is_valid_user(request):
        if request.method == "POST":
            print(request.POST)
            form: RegisterStudentForm = RegisterStudentForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect("courses:register_student")
            else:
                messages.error(
                    request,
                    mark_safe(form.errors),
                )
                return redirect("courses:register_student")
        students: QuerySet[Student] = Student.objects.filter(
            groups=None, course__dept=request.user.dept  # type: ignore
        ).select_related("course")
        groups: QuerySet[Class] = Class.objects.filter(dept=request.user.dept)  # type: ignore
        form: RegisterStudentForm = RegisterStudentForm(dept=request.user.dept)  # type: ignore
        return render(
            request,
            "courses/register_student.html",
            {"students": students, "form": form, "groups": groups},
        )
    else:
        return JsonResponse(
            {
                "error": "you have no access to this page or there is a problem with your accont"
            }
        )


@login_required  # type: ignore
def student_view(request: HttpRequest, student_id: str):
    try:
        student = Student.objects.prefetch_related("groups").get(id=student_id)
    except Student.DoesNotExist:
        return render(request, "404.html")
    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "update":
            form = RegisterStudentForm(request.POST, instance=student)
            print(form)
            if form.is_valid():
                form.save()
                print(student.full_name)
                messages.success(request, "student updated successfully")
                return redirect("courses:student", student_id=student.id)
            else:
                messages.error(
                    request,
                    "Error while updating student, make sure you've filled all required fields",
                )
                return redirect("courses:student", student_id=student.id)
        elif form_type == "payment":
            form = StudentPaymentForm(request.POST, student=student)
            if form.is_valid():
                payment = form.save(commit=False)
                payment.student = student
                payment.dept = request.user.dept  # type: ignore
                payment.save()
                messages.success(request, "payment created successfully")
                return redirect("courses:student", student_id=student.id)
            else:
                messages.error(request, "Make sure to fill price and choose the group")
                return redirect("courses:student", student_id=student.id)
    form = RegisterStudentForm(
        initial={
            "full_name": student.full_name,
            "groups": student.groups.all(),
            "address": student.address,
            "phone_numbers": student.phone_numbers,
            "course": student.course,
            "condition": student.condition,
        },
    )
    payments = (
        StudentPayment.objects.select_related("assign__class_id")
        .filter(student=student)
        .all()
    )
    payment_form = StudentPaymentForm(student=student)
    return render(
        request,
        "courses/student.html",
        {
            "student": student,
            "form": form,
            "payment_form": payment_form,
            "payments": payments,
        },
    )


@login_required
def students_view(request: HttpRequest) -> HttpResponse | HttpResponseForbidden:
    if request.user.is_staff:  # type: ignore
        return HttpResponseForbidden()
    teacher: Teacher = request.user.teacher  # type: ignore
    students: QuerySet[Student] = Student.objects.filter(
        group__dept=teacher.user.dept, course__dept=teacher.user.dept  # type: ignore
    )
    context = {"students": students, "teacher": teacher}
    return render(request, "template_name", context)


@login_required  # type: ignore
def delete_teacher(
    request: HttpRequest, teacher_id: str
) -> HttpResponse | JsonResponse:
    if is_chef(request):
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            if hasattr(teacher.user, "dept") and teacher.user.dept is not None:  # type: ignore
                if not teacher.user.dept == request.user.dept:  # type: ignore
                    messages.error(
                        request,
                        "You have no access to delete this teacher, department of this teacher does not match to yours",
                    )
                    return redirect("courses:teachers")
            else:
                messages.error(
                    request,
                    "You can't delete this teacher, teacher has no department, first attach teacher to a department of yours",
                )
                return redirect("courses:teachers")
        except Teacher.DoesNotExist:
            return JsonResponse({"error": "Teacher not found"})
        if request.method == "POST":
            teacher.delete()
            return redirect("courses:teachers")
        return JsonResponse({})
    return JsonResponse(
        {
            "error": "You have no access to delete this teacher",
            "details": "you are not registered as chef user",
        }
    )
    # return render(request, "courses/confirm_delete.html", {"name": teacher.full_name})


@login_required
def move_student(
    request: HttpRequest, student_id: uuid.UUID, class_id: int
) -> JsonResponse:
    try:
        student: Student = Student.objects.get(id=student_id)
        group: Class = Class.objects.get(id=class_id)
        student.groups.add(group)  # type: ignore
        student.save()
    except Student.DoesNotExist or Class.DoesNotExist:
        messages.error(request, "something has burned up")
        return JsonResponse({"error": "either student or group object not found"})
    messages.success(
        request,
        mark_safe(
            f'{student.full_name} <a href="/groups/{group.id}">{group.name}</a> guruhiga muvaffaqiyatli ko\'chirildi.'  # type: ignore
        ),
    )
    return JsonResponse({"success": True})


@login_required
def teacher(request: HttpRequest, teacher_id: uuid.UUID):
    if is_chef(request):
        teacher = Teacher.objects.prefetch_related("courses").get(id=teacher_id)
        if request.method == "POST":
            form = CreateTeacherForm(request.POST, instance=teacher, dept=request.user.dept)  # type: ignore
            if form.is_valid():
                form.save()
                messages.success(request, "Teacher updated successfully")
                return redirect("courses:teacher", teacher_id=teacher.id)
            else:
                messages.error(request, "correct the error below")
                return render(
                    request, "courses/teacher.html", {"teacher": teacher, "form": form}
                )
        form = CreateTeacherForm(
            dept=request.user.dept,  # type: ignore
            initial={
                "full_name": teacher.full_name,
                "working_days": teacher.working_days,
                "working_time": teacher.working_time,
                "courses": teacher.courses.all(),
                "address": teacher.address,
                "phone_numbers": teacher.phone_numbers,
            },
        )
        return render(
            request, "courses/teacher.html", {"teacher": teacher, "form": form}
        )
    return render(request, "403.html", status=403)
