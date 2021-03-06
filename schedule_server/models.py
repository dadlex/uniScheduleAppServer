from django.db import models
from django.db.models import UniqueConstraint


class Subject(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='subjects', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    color = models.CharField(max_length=6)

    class Meta:
        ordering = ['created']
        constraints = [
            UniqueConstraint(fields=['owner', 'title'], name='unique_subject_title_per_user')
        ]


class Teacher(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='teachers', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=100, default='')
    email = models.CharField(max_length=1000, default='')

    class Meta:
        ordering = ['created']
        constraints = [
            UniqueConstraint(fields=['owner', 'name'], name='unique_teacher_name_per_user')
        ]


class ClassType(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='class_types', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    is_custom = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['owner', 'title'], name='unique_class_type_title_per_user')
        ]


class Class(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='classes', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    type = models.ForeignKey(ClassType, on_delete=models.SET_NULL, null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    location = models.CharField(max_length=1000, default='')


class Time(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='times', on_delete=models.CASCADE)
    class_ = models.ForeignKey(Class, name='class', on_delete=models.CASCADE)
    period = models.CharField(max_length=100, null=True)
    days_of_week = models.CharField(max_length=100, null=True)
    date_start = models.DateField(null=True)
    date_end = models.DateField(null=True)
    time_start = models.TimeField()
    time_end = models.TimeField()

    class Meta:
        ordering = ['time_start']


class Task(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100, null=True)
    priority = models.IntegerField(choices=[(0, 'none'), (1, 'low'), (2, 'medium'), (3, 'high')], default=0)
    is_completed = models.BooleanField(default=False)
    class_ = models.ForeignKey(Class, name='class', on_delete=models.CASCADE, null=True)
    due_date = models.CharField(max_length=100, null=True)
    completed_at = models.CharField(max_length=100, null=True)

    class Meta:
        ordering = ['-due_date']
