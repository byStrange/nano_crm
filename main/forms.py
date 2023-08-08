from django import forms
from main.models import Class, Course, Student, Teacher, time_slots, DAYS_OF_WEEK

DEFAULT_INPUT_ATTRS = {"class": "form-control"}


class CreateClassForm(forms.Form):
    name = forms.CharField(
        max_length=254, widget=forms.TextInput(attrs=DEFAULT_INPUT_ATTRS)
    )
    day = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        initial=["Monday", "Wednesday", "Friday"],
    )
    time = forms.ChoiceField(choices=time_slots)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"] = forms.ChoiceField(
            choices=Course.objects.all().values_list("id", "name"),
        )


class CreateTeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["full_name", "working_days", "working_time", "courses", "address", "phone_numbers"]
        widgets = {
            "full_name": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "working_days": forms.Select(attrs=DEFAULT_INPUT_ATTRS),
            "working_time": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "faculties": forms.SelectMultiple(attrs=DEFAULT_INPUT_ATTRS),
            "address": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "phone_numbers": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
        }


class RegisterStudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields["course"].queryset = Course.objects.filter(dept=teacher.dept)

    class Meta:
        model = Student
        fields = ["full_name", "address", "phone_numbers", "course", "condition"]
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
