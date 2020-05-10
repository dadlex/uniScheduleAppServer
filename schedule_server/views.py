import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from schedule_server import models, serializers
from schedule_server.models import Task
from schedule_server.occurances import is_occurrence
from schedule_server.permissions import IsOwnerOrAdmin
from schedule_server.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    class IsThisUserOrAdmin(permissions.BasePermission):
        def has_object_permission(self, request, view, obj):
            return bool(request.user) and (request.user.is_staff or obj.id == request.user.id)

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = []
        elif self.action == 'list':
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [self.IsThisUserOrAdmin]
        return [permission() for permission in permission_classes]


# class GroupViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint that allows groups to be viewed or edited.
#     """
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
#     permission_classes = [permissions.IsAdminUser]


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SubjectSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Subject.objects.all()
        return self.request.user.subjects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TeacherSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Teacher.objects.all()
        return self.request.user.teachers.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ClassTypeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ClassTypeSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.ClassType.objects.all()
        return self.request.user.class_types.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ClassViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ClassSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Class.objects.all()
        return self.request.user.classes.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TimeViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TimeSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Time.objects.all()
        return self.request.user.times.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TaskSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Task.objects.all()
        return self.request.user.tasks.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# val dateDOW = date.dayOfWeek
#
# val db = readableDatabase
# val args = arrayOf(format(date), "%$dateDOW%")
# val cursor = db.rawQuery(
#     """
#     SELECT classId, dateStart, period FROM times
#     WHERE dateStart <= ?
#     AND (dateEnd >= ?1 OR dateEnd IS NULL)
#     AND (daysOfWeek LIKE ?2 OR daysOfWeek IS NULL)""", args
# )
#
# val classIdColumn = cursor.getColumnIndex("classId")
# val dateStartColumn = cursor.getColumnIndex("dateStart")
# val periodColumn = cursor.getColumnIndex("period")
#
# val classIds = arrayListOf<Long>()
# var startDate: LocalDate
# var recurrence: Period?
# while (cursor.moveToNext()) {
# startDate = LocalDate.parse(cursor.getString(dateStartColumn))
# recurrence = if (!cursor.isNull(periodColumn)) {
# Period.parse(cursor.getString(periodColumn))
# } else null
#
# if (isOccurrence(date, startDate, recurrence)) {
# classIds.add(cursor.getLong(classIdColumn))
# }
# }
# cursor.close()

# return db.rawQuery(
#     """
#     SELECT classes._id,
#     subjects.title AS subject,
#     colors.color AS color,
#     classTypes.title AS type,
#     times.timeStart, timeEnd,
#     location,
#     teachers.name AS teacher FROM classes
#     INNER JOIN subjects ON classes.subjectId = subjects._id
#     INNER JOIN colors ON subjects.colorId = colors._id
#     INNER JOIN times ON times.classId = classes._id
#     INNER JOIN classTypes ON classes.typeId = classTypes._id
#     LEFT JOIN teachers ON classes.teacherId = teachers._id
#     WHERE classes._id IN (${format(classIds)})
#     ORDER BY timeStart ASC""", null
# )


@api_view(['GET'])
def schedule(request, date, format=None):
    try:
        year, month, day = date.split('-')
        viewing_date = datetime.date(int(year), int(month), int(day))
    except ValueError:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        weekday = viewing_date.weekday() + 1
        times = models.Time.objects.filter(
            Q(owner_id=request.user.id),
            Q(date_start__lte=viewing_date),
            Q(date_end__gte=viewing_date) | Q(date_end__isnull=True),
            Q(days_of_week__contains=weekday) | Q(days_of_week__isnull=True)
        )
        times = [time for time in times
                 if is_occurrence(viewing_date, time.date_start, datetime.timedelta(int(time.period)))]

        # return db.rawQuery(
        #     """
        #     SELECT classes._id,
        #     subjects.title AS subject,
        #     colors.color AS color,
        #     classTypes.title AS type,
        #     times.timeStart, timeEnd,
        #     location,
        #     teachers.name AS teacher FROM classes
        #     INNER JOIN subjects ON classes.subjectId = subjects._id
        #     INNER JOIN colors ON subjects.colorId = colors._id
        #     INNER JOIN times ON times.classId = classes._id
        #     INNER JOIN classTypes ON classes.typeId = classTypes._id
        #     LEFT JOIN teachers ON classes.teacherId = teachers._id
        #     WHERE classes._id IN (${format(classIds)})
        #     ORDER BY timeStart ASC""", null
        # )

        response = []
        for time in times:
            class_ = models.Class.objects.get(id=time.class_id)
            time = serializers.TimeSerializer(time).data
            time.pop('class')

            item = serializers.ClassSerializer(class_).data
            item['time_start'] = time['time_start']
            item['time_end'] = time['time_end']
            response.append(item)
        return Response(response)
