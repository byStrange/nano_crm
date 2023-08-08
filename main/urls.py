from django.urls import path
from django.shortcuts import redirect
from main.views import (
    index,
    GroupsView,
    group,
    teachers,
    register_student,
    teacher,
    move_student,
    delete_teacher,
    students_view,
    take_attendance
)

app_name = "main"

urlpatterns = [
    path("", lambda request: redirect("main:dashboard"), name="dashboard"),
    path("dashboard/", index, name="dashboard"),
    path("groups/", GroupsView.as_view(), name="groups"),
    path("groups/<int:assign_id>/", group, name="group"),
    path("groups/<int:assign_id>/attendance/", take_attendance, name="attendance"),
    # teacher related
    path("teachers/", teachers, name="teachers"),
    path("teachers/<uuid:teacher_id>/", teacher, name="teacher"),
    path("teachers/<int:teacher_id>/delete/", delete_teacher, name="delete_teacher"),
    # student related
    path("register/", register_student, name="register_student"),
    path("students/", students_view, name="students"),
    path("students/<uuid:student_id>/move/<int:class_id>/", move_student, name="move_student"),
]
