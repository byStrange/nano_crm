from django import forms

from main.models import (DAYS_OF_WEEK, Class, Course, Student, Teacher,
                         time_slots)
from django.db.models.query import QuerySet
from django.db import models

from typing import Dict, List, Tuple

from main.models import Class, Course, Student, Teacher, time_slots, DAYS_OF_WEEK

DEFAULT_INPUT_ATTRS: Dict[str, str] = {"class": "form-control"}
Fields = List[str] | Tuple[str]
Widgets = Dict[str, forms.Widget]


class CreateClassForm(forms.Form):
    name: forms.CharField = forms.CharField(
        max_length=254, widget=forms.TextInput(attrs=DEFAULT_INPUT_ATTRS)
    )
    day: forms.MultipleChoiceField = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        initial=["Monday", "Wednesday", "Friday"],
    )
    time: forms.ChoiceField = forms.ChoiceField(choices=time_slots)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"] = forms.ChoiceField(
            choices=Course.objects.all().values_list("id", "name"),
        )


class CreateTeacherForm(forms.ModelForm):
    class Meta:
        model: models.Model = Teacher
        fields: Fields = [
            "full_name",
            "working_days",
            "working_time",
            "courses",
            "address",
            "phone_numbers",
        ]
        widgets: Widgets = {
            "full_name": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "working_days": forms.Select(attrs=DEFAULT_INPUT_ATTRS),
            "working_time": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "faculties": forms.SelectMultiple(attrs=DEFAULT_INPUT_ATTRS),
            "address": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "phone_numbers": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
        }


class RegisterStudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        teacher: Teacher | None = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields["course"].queryset: QuerySet = Course.objects.filter(
                dept=teacher.dept
            )

    class Meta:
        model: models.Model = Student
        fields: Fields = [
            "full_name",
            "address",
            "phone_numbers",
            "course",
            "condition",
        ]
        widgets: Widgets = {
            "full_name": forms.TextInput(
                attrs={**DEFAULT_INPUT_ATTRS, "placeholder": "Ismi", "required": True}
            ),
            "address": forms.TextInput(
                attrs={
                    **DEFAULT_INPUT_ATTRS,
                    "placeholder": "Manzili",
                    "required": True,
                }
            ),
            "phone_numbers": forms.TextInput(
                attrs={
                    **DEFAULT_INPUT_ATTRS,
                    "placeholder": "Telefon raqamlari",
                    "required": True,
                }
            ),
            "course": forms.Select(
                attrs={
                    **DEFAULT_INPUT_ATTRS,
                    "placeholder": "Yo'nalishi",
                    "required": True,
                }
            ),
        }
