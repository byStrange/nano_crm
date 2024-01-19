import uuid

from django.db import models


class Dept(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    dept = models.ForeignKey("core.Dept", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    shortname = models.CharField(max_length=50, default="X")
    price = models.IntegerField()

    def __str__(self):
        return self.name

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    class Meta:
        abstract = True

class DeptMixin(models.Model):
    dept = models.ForeignKey("core.Dept", on_delete=models.CASCADE)

    class Meta:
        abstract = True