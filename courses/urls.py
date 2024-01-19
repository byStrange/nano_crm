from django.shortcuts import redirect
from django.urls import path

from courses.views import (
    GroupsView,
    delete_teacher,
    group,
    courses,
    edit_course,
    index,
    move_student,
    register_student,
    student_view,
    students_view,
    take_attendance,
    teacher,
    teachers,
)

app_name: str = "courses"

urlpatterns = [
    path("", lambda request: redirect("courses:dashboard"), name="index"),
    path("dashboard/", index, name="dashboard"),
    path("groups/", GroupsView.as_view(), name="groups"),
    path("groups/<int:assign_id>/", group, name="group"),
    path("groups/<int:assign_id>/attendance/", take_attendance, name="attendance"),
    path("courses/", courses, name="courses"),
    path("courses/<int:course_id>/", edit_course, name="course"),
    # teacher related
    path("teachers/", teachers, name="teachers"),
    path("teachers/<uuid:teacher_id>/", teacher, name="teacher"),
    path("teachers/<uuid:teacher_id>/delete/", delete_teacher, name="delete_teacher"),
    # student related
    path("register/", register_student, name="register_student"),
    path("students/", students_view, name="students"),
    path("students/<uuid:student_id>/", student_view, name="student"),
    path(
        "students/<uuid:student_id>/move/<int:class_id>/",
        move_student,
        name="move_student",
    ),
]
