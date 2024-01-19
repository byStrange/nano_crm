from django import forms

from payments.models import StudentPayment
from core.constants import DEFAULT_INPUT_ATTRS
from courses.models import Assign

class StudentPaymentForm(forms.ModelForm):
    def __init__(self, *args, student, **kwargs):
        super().__init__(*args, **kwargs)
        if student:
            groups = student.groups.all()
            self.fields["assign"].queryset =  Assign.objects.filter(class_id__in=groups).select_related("class_id")

    class Meta:
        model = StudentPayment
        fields = ["amount", "assign"]
        widgets = {
            "amount": forms.TextInput(attrs=DEFAULT_INPUT_ATTRS),
            "assign": forms.Select(attrs=DEFAULT_INPUT_ATTRS)
        }