from django.contrib.auth.models import User
from rest_framework import serializers

from schedule_server import models
from schedule_server.models import Subject, ClassType, Teacher, Class


class UserSerializer(serializers.HyperlinkedModelSerializer):
    subjects = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Subject.objects.all(), required=False)
    teachers = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Teacher.objects.all(), required=False)
    class_types = serializers.PrimaryKeyRelatedField(many=True, queryset=models.ClassType.objects.all(), required=False)
    classes = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Class.objects.all(), required=False)
    times = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Time.objects.all(), required=False)
    tasks = serializers.PrimaryKeyRelatedField(many=True, queryset=models.Task.objects.all(), required=False)

    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = User.objects.create(username=validated_data['username'])
        user.set_password(validated_data['password'])
        if 'is_staff' in validated_data:
            user.is_staff = validated_data['is_staff']
        user.save()
        return user

    class Meta:
        model = User
        fields = ['url', 'username', 'password', 'is_staff',
                  'subjects', 'teachers', 'class_types', 'classes', 'times', 'tasks']


# class GroupSerializer(serializers.HyperlinkedModelSerializer):
#     class Meta:
#         model = Group
#         fields = ['url', 'name']


class SubjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = models.Subject
        fields = ['id', 'title', 'color', 'owner', 'created']


class TeacherSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(allow_blank=True)
    email = serializers.CharField(allow_blank=True)
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = models.Teacher
        fields = ['id', 'name', 'phone', 'email', 'owner', 'created']


class ClassTypeSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = models.ClassType
        fields = ['id', 'title', 'is_custom', 'owner', 'created']


class ClassSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    subject = SubjectSerializer()
    type = ClassTypeSerializer()
    teacher = TeacherSerializer(required=False)

    class Meta:
        model = models.Class
        fields = ['id', 'subject', 'type', 'teacher', 'location', 'owner', 'created']

    def create(self, validated_data):
        subject, _ = Subject.objects.get_or_create(owner=validated_data['owner'], **validated_data.pop('subject'))
        class_type, _ = ClassType.objects.get_or_create(owner=validated_data['owner'], **validated_data.pop('type'))
        if 'teacher' in validated_data:
            teacher, _ = Teacher.objects.get_or_create(owner=validated_data['owner'], **validated_data.pop('teacher'))
        else:
            teacher = None
        return Class.objects.create(subject=subject, type=class_type, teacher=teacher, **validated_data)


class TimeSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = models.Time
        fields = ['id', 'class', 'period', 'days_of_week', 'date_start',
                  'date_end', 'time_start', 'time_end', 'owner', 'created']


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = models.Task
        fields = ['id', 'title', 'description', 'priority', 'is_completed',
                  'class', 'due_date', 'completed_at', 'owner', 'created']
