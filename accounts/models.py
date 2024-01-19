import uuid
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import DeptMixin, UUIDMixin
TOKEN_EXPIRE = getattr(
    settings, "REGISTRATION_TOKEN_EXPIRATION_DURATION", timezone.timedelta(weeks=1)
)


class CustomUser(AbstractUser):
    USER_TYPES = (
        ("chef", "Chef of Department"),
        ("teacher", "Teacher"),
    )
    dept = models.ForeignKey(
        "core.Dept", on_delete=models.CASCADE, blank=True, null=True
    )
    user_type = models.CharField(
        max_length=10, choices=USER_TYPES, blank=True, null=True
    )

    @property
    def is_chef(self):
        return self.user_type == "chef"

    @property
    def is_teacher(self):
        return self.user_type == "teacher"


class Chef(UUIDMixin):
    full_name = models.CharField(max_length=254)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.full_name


class Teacher(DeptMixin, UUIDMixin):
    WORKING_DAYS_CHOICES = (
        ("workingdays", "ish kunlari"),
        ("everyotherday", "kun oralab"),
    )
    full_name = models.CharField(max_length=100)
    working_days = models.CharField(max_length=254, choices=WORKING_DAYS_CHOICES)
    working_time = models.CharField(max_length=254)
    courses = models.ManyToManyField("core.Course", blank=True)
    address = models.CharField(max_length=254, default="Andijon")
    phone_numbers = models.CharField(max_length=254, default="None")

    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.full_name


class RegisterToken(UUIDMixin, DeptMixin):
    token = models.CharField(max_length=32)
    teacher = models.OneToOneField("Teacher", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateTimeField(blank=True, null=True)

    def is_valid(self) -> bool:
        expire_duration = TOKEN_EXPIRE
        now = timezone.now()
        if self.valid_until:
            is_not_expired = (
                self.valid_until >= now and (self.valid_until - now) <= expire_duration
            )

            # Check if the token is associated with a teacher
            has_teacher = self.teacher.user is not None
            return is_not_expired and not has_teacher
        return False


@receiver(post_save, sender=CustomUser)
def chef_create(instance: CustomUser, created: bool, **kwargs):
    if created:
        user_type = instance.user_type
        if user_type == "chef" and hasattr(instance, "dept"):
            Chef.objects.create(full_name=instance.first_name, user=instance)


@receiver(post_save, sender=RegisterToken)
def update_validation(instance: RegisterToken, created, **kwargs):
    if created:
        instance.valid_until = TOKEN_EXPIRE + timezone.datetime.now()
        instance.save()
