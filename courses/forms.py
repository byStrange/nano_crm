from django import forms

from core.constants import DEFAULT_INPUT_ATTRS, DAYS_OF_WEEK, time_slots
from accounts.models import Teacher
from core.models import Course, Dept
from courses.models import Student

class CreateCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = ["dept"]
        widgets = {
            "name": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "shortname": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "price": forms.NumberInput(attrs=DEFAULT_INPUT_ATTRS),
        }


class CreateClassForm(forms.Form):
    def __init__(self, *args, dept, **kwargs):
        super().__init__(*args, **kwargs)  # type: ignore
        if dept:
            self.fields["teacher"] = forms.ChoiceField(
                choices=Teacher.objects.filter(dept=dept).values_list("id", "full_name")
            )
            self.fields["course"] = forms.ChoiceField(
                choices=Course.objects.filter(dept=dept).values_list("id", "name"),
            )

    name = forms.CharField(
        max_length=254, widget=forms.TextInput(attrs=DEFAULT_INPUT_ATTRS)
    )
    day = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        initial=["Monday", "Wednesday", "Friday"],
    )
    time = forms.ChoiceField(choices=time_slots)
    percentage = forms.IntegerField(widget=forms.NumberInput(attrs=DEFAULT_INPUT_ATTRS))


class RegisterStudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        teacher: Teacher | None = kwargs.pop("teacher", None)
        dept: Dept | None = kwargs.pop("dept", None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields["course"].queryset = Course.objects.filter(dept=teacher.dept)
        elif dept:
            self.fields["course"].queryset = Course.objects.filter(dept=dept)

    class Meta:
        model = Student
        fields = [
            "full_name",
            "address",
            "phone_numbers",
            "course",
            "condition",
            "groups"
        ]
        widgets = {
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
