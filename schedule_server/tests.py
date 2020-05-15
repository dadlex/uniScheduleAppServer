from datetime import datetime, timedelta
from operator import itemgetter

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from schedule_server import models, serializers, views
from schedule_server.occurances import get_closest_future_occurrence, is_occurrence


class OccurrenceDetectionTests(TestCase):

    def test_get_closest_future_occurrence(self):
        test_data = [
            (datetime(2020, 1, 2), datetime(2020, 1, 1), timedelta(1), datetime(2020, 1, 2)),
            (datetime(2020, 1, 2), datetime(2020, 1, 1), timedelta(5), datetime(2020, 1, 6)),
            (datetime(2020, 12, 31), datetime(2020, 1, 1), timedelta(2), datetime(2021, 1, 1)),
            (datetime(2020, 5, 10), datetime(2020, 5, 10), timedelta(14), datetime(2020, 5, 10)),
            (datetime(2020, 5, 11), datetime(2020, 5, 10), timedelta(14), datetime(2020, 5, 18)),
        ]
        for today, start, recurrence, expected_result in test_data:
            occurrence = get_closest_future_occurrence(today, start, recurrence)
            self.assertEqual(occurrence, expected_result)

    def test_is_occurrence(self):
        test_data = [
            (datetime(2020, 1, 1), datetime(2020, 1, 1), None, True),
            (datetime(2020, 1, 2), datetime(2020, 1, 1), timedelta(1), True),
            (datetime(2020, 1, 2), datetime(2020, 1, 1), timedelta(2), False),
        ]
        for today, start, recurrence, expected_result in test_data:
            occurrence = is_occurrence(today, start, recurrence)
            self.assertIs(occurrence, expected_result)


class RegistrationTests(APITestCase):
    USERNAME = 'test-user'
    PASSWORD = 'test-password'

    def test_register_user(self):
        """FR_Id_1
        The system must grant access to the registration procedure to all unauthorized users

        FR_Id_43
        The server must be able to accept requests to create new users.

        FR_Id_44
        User data must be stored in a database, and passwords must be encrypted with a hash function
        """
        response = self.client.post(reverse('user-list'), {
            'username': self.USERNAME,
            'password': self.PASSWORD
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get()
        self.assertEqual(user.username, self.USERNAME)
        self.assertTrue(user.check_password(self.PASSWORD))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_register_existing_user(self):
        """FR_Id_3
        If the user entered incorrect data during registration, the system must prohibit saving registration data
        """
        url = reverse('user-list')
        body = {'username': self.USERNAME, 'password': self.PASSWORD}
        response = self.client.post(url, body)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_register_user_without_username(self):
        """FR_Id_3
        If the user entered incorrect data during registration, the system must prohibit saving registration data
        """
        url = reverse('user-list')
        body = {'username': ' ', 'password': self.PASSWORD}
        response = self.client.post(url, body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.all())

    def test_register_user_without_password(self):
        """FR_Id_3
        If the user entered incorrect data during registration, the system must prohibit saving registration data
        """
        url = reverse('user-list')
        body = {'username': self.USERNAME, 'password': ''}
        response = self.client.post(url, body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.all())

    def test_user_list_permissions(self):
        url = reverse('user-list')
        self.client.login(username='simple_user', password='1234')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        User.objects.create_user(username='simple_user', password='1234').save()
        self.client.login(username='simple_user', password='1234')
        url = reverse('user-detail', args=[1])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LoginTests(APITestCase):

    def test_login(self):
        """FR_Id_7
        When logging in to the system if the authorization data is entered correctly
        the user gets access to their account and application
        """
        data_url = reverse('subject-list')
        username = 'test-user'
        password = 'test-password'
        self.client.post(reverse('user-list'), {
            'username': username,
            'password': password
        })
        self.client.login(username=username, password=password)
        response = self.client.get(data_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_wrong_credentials(self):
        """FR_Id_6
        When user is trying to log in, the system must check the username and password entered by the user
        and return an error message if the user is not found or the password is not correct

        FR_Id_45
        When receiving the user's authorization data, the server must search for a record about this user
        in the database and, if there is no record, send a corresponding message to the client
        """
        data_url = reverse('subject-list')
        self.client.login(username='simple_user', password='1234')
        response = self.client.get(data_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SubjectTests(APITestCase):

    def setUp(self):
        self.superuser_credentials = dict(username='admin', password='admin')
        self.user_credentials = dict(username='user', password='user')
        self.superuser = User.objects.create_superuser(**self.superuser_credentials)
        self.user = User.objects.create_user(**self.user_credentials)
        self.superuser.save()
        self.user.save()
        self.client.login(**self.user_credentials)

    def test_add_subject(self):
        """FR_Id_16
        The system should allow the user to add new subjects.

        FR_Id_18
        The system should allow the user to enter the following information about the subject:
        1) Name
        2) Color mark
        """
        response = self.client.post(reverse('subject-list'), {
            'title': 'Test Subject',
            'color': '000000'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_privileges(self):
        admin_subject = models.Subject(title='Admin subject', color='000000', owner=self.superuser)
        regular_subject = models.Subject(title='Regular subject', color='000000', owner=self.user)
        admin_subject.save()
        regular_subject.save()
        self.client.login(**self.superuser_credentials)
        response = self.client.get(reverse('subject-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.SubjectSerializer().to_representation(admin_subject),
            serializers.SubjectSerializer().to_representation(regular_subject)
        ])
        self.client.login(**self.user_credentials)
        response = self.client.get(reverse('subject-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.SubjectSerializer().to_representation(regular_subject)
        ])


class TeacherTests(APITestCase):

    def setUp(self):
        self.superuser_credentials = dict(username='admin', password='admin')
        self.user_credentials = dict(username='user', password='user')
        self.superuser = User.objects.create_superuser(**self.superuser_credentials)
        self.user = User.objects.create_user(**self.user_credentials)
        self.superuser.save()
        self.user.save()
        self.client.login(**self.user_credentials)

    def test_add_teacher(self):
        """FR_Id20
        The system should allow the user to add new teachers.

        FR_Id_22
        The system should allow the user to enter the following information about the teacher:
        1) name
        2) phone number
        3) email address
        """
        response = self.client.post(reverse('teacher-list'), {
            'name': 'Test Teacher',
            'phone': '+7 (999) 111-22-33',
            'email': 'cool_teacher@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_privileges(self):
        admin_teacher = models.Teacher(name='Admin teacher', owner=self.superuser)
        regular_teacher = models.Teacher(name='Regular teacher', owner=self.user)
        admin_teacher.save()
        regular_teacher.save()
        self.client.login(**self.superuser_credentials)
        response = self.client.get(reverse('teacher-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.TeacherSerializer().to_representation(admin_teacher),
            serializers.TeacherSerializer().to_representation(regular_teacher)
        ])
        self.client.login(**self.user_credentials)
        response = self.client.get(reverse('teacher-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.TeacherSerializer().to_representation(regular_teacher)
        ])


class ClassTypeTests(APITestCase):

    def setUp(self):
        self.superuser_credentials = dict(username='admin', password='admin')
        self.user_credentials = dict(username='user', password='user')
        self.superuser = User.objects.create_superuser(**self.superuser_credentials)
        self.user = User.objects.create_user(**self.user_credentials)
        self.superuser.save()
        self.user.save()
        self.client.login(**self.user_credentials)

    def test_add_teacher(self):
        """FR_Id19
        When selecting a class type, the user can either select an existing type or add a new one
        """
        response = self.client.post(reverse('class-type-list'), {
            'title': 'Test Class Type'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_privileges(self):
        admin_class_type = models.ClassType(title='Admin class type', owner=self.superuser)
        regular_class_type = models.ClassType(title='Regular class type', owner=self.user)
        admin_class_type.save()
        regular_class_type.save()
        self.client.login(**self.superuser_credentials)
        response = self.client.get(reverse('class-type-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.ClassTypeSerializer().to_representation(admin_class_type),
            serializers.ClassTypeSerializer().to_representation(regular_class_type)
        ])
        self.client.login(**self.user_credentials)
        response = self.client.get(reverse('class-type-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.ClassTypeSerializer().to_representation(regular_class_type)
        ])


class ClassesTests(APITestCase):

    def setUp(self):
        self.superuser_credentials = dict(username='admin', password='admin')
        self.user_credentials = dict(username='user', password='user')
        self.superuser = User.objects.create_superuser(**self.superuser_credentials)
        self.user = User.objects.create_user(**self.user_credentials)
        self.superuser.save()
        self.user.save()
        self.client.login(**self.user_credentials)

    def test_add_class(self):
        """FR_Id_13
        The system must allow the user to add classes on a specific date.

        FR_Id_14
        The system should allow the user to enter the following information about the class:
        1) subject
        2) class Type
        3) start time
        4) end time
        5) repeatability of the class
        6) date of the lesson
        7) location of the lesson
        8) teacher
        """
        response = self.client.post(reverse('subject-list'), {
            'title': 'Test Subject',
            'color': '000000'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('class-type-list'), {
            'title': 'Test Class Type',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('teacher-list'), {
            'name': 'Test Teacher',
            'phone': '+7 (999) 111-22-33',
            'email': 'cool_teacher@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(reverse('class-list'), {
            'subject': serializers.SubjectSerializer().to_representation(models.Subject.objects.get()),
            'type': serializers.ClassTypeSerializer().to_representation(models.ClassType.objects.get()),
            'teacher': serializers.TeacherSerializer().to_representation(models.Teacher.objects.get()),
            'location': 'Test Location',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        class_ = models.Class.objects.get()
        self.assertEqual(class_.subject, models.Subject.objects.get())
        self.assertEqual(class_.type, models.ClassType.objects.get())
        self.assertEqual(class_.teacher, models.Teacher.objects.get())
        self.assertEqual(class_.location, 'Test Location')
        self.assertTrue(class_.created)
        self.assertEqual(class_.owner, self.user)

        response = self.client.post(reverse('time-list'), {
            'class': models.Class.objects.get().id,
            'period': '14',
            'days_of_week': '1,2,3',
            'date_start': '2020-01-01',
            'date_end': '2020-12-31',
            'time_start': '10:00',
            'time_end': '12:00',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_privileges(self):
        admin_subject = models.Subject(title='Admin subject', color='000000', owner=self.superuser)
        regular_subject = models.Subject(title='Regular subject', color='000000', owner=self.user)
        admin_subject.save()
        regular_subject.save()
        admin_class_type = models.ClassType(title='Admin class type', owner=self.superuser)
        regular_class_type = models.ClassType(title='Regular class type', owner=self.user)
        admin_class_type.save()
        regular_class_type.save()
        admin_class = models.Class(subject=admin_subject, type=admin_class_type, owner=self.superuser)
        regular_class = models.Class(subject=regular_subject, type=regular_class_type, owner=self.user)
        admin_class.save()
        regular_class.save()
        self.client.login(**self.superuser_credentials)
        response = self.client.get(reverse('class-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.ClassSerializer().to_representation(admin_class),
            serializers.ClassSerializer().to_representation(regular_class)
        ])
        self.client.login(**self.user_credentials)
        response = self.client.get(reverse('class-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.ClassSerializer().to_representation(regular_class)
        ])


class TimeTests(APITestCase):

    def setUp(self):
        self.superuser_credentials = dict(username='admin', password='admin')
        self.user_credentials = dict(username='user', password='user')
        self.superuser = User.objects.create_superuser(**self.superuser_credentials)
        self.user = User.objects.create_user(**self.user_credentials)
        self.superuser.save()
        self.user.save()
        self.client.login(**self.user_credentials)

    def test_privileges(self):
        times = []
        for user in (self.user, self.superuser):
            subject = models.Subject(title=f'{user.username} subject', color='000000', owner=user)
            subject.save()
            class_type = models.ClassType(title=f'{user.username} class type', owner=user)
            class_type.save()
            class_ = models.Class(subject=subject, type=class_type, owner=user)
            class_.save()
            time = models.Time(**{'class': class_}, period=7, date_start='2020-01-01', date_end='2020-12-31',
                               days_of_week='1,2', time_start='10:00:00', time_end='11:30:00', owner=user)
            time.save()
            times.append(time)

        times = [serializers.TimeSerializer().to_representation(time) for time in times]
        self.client.login(**self.superuser_credentials)
        response = self.client.get(reverse('time-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, times)
        self.client.login(**self.user_credentials)
        response = self.client.get(reverse('time-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [times[0]])


class ScheduleTests(APITestCase):

    def setUp(self):
        """There are 3 classes in 2020 each week: mon tue - class1, tue wed - class2, wed thu - class3"""
        user = User.objects.create_user(username='test-user', password='test-password')
        user.save()
        self.client.login(username='test-user', password='test-password')
        subject1 = models.Subject(title='Subject 1', owner=user)
        subject2 = models.Subject(title='Subject 2', owner=user)
        subject3 = models.Subject(title='Subject 3', owner=user)
        subject1.save()
        subject2.save()
        subject3.save()
        class_type = models.ClassType(title='Test Class Type', owner=user)
        class_type.save()
        class1 = models.Class(subject=subject1, type=class_type, owner=user)
        class2 = models.Class(subject=subject2, type=class_type, owner=user)
        class3 = models.Class(subject=subject3, type=class_type, owner=user)
        class1.save()
        class2.save()
        class3.save()
        common = dict(period=7, date_start='2020-01-01', date_end='2020-12-31', owner=user)

        def c(cls):
            return {'class': cls}

        time1 = models.Time(**c(class1), days_of_week='1,2', time_start='10:00:00', time_end='11:30:00', **common)
        time2 = models.Time(**c(class2), days_of_week='2,3', time_start='12:00:00', time_end='13:30:00', **common)
        time3 = models.Time(**c(class3), days_of_week='3,4', time_start='14:00:00', time_end='15:30:00', **common)
        time1.save()
        time2.save()
        time3.save()
        self.schedule_item1 = self.build_schedule_item(class1, time1)
        self.schedule_item2 = self.build_schedule_item(class2, time2)
        self.schedule_item3 = self.build_schedule_item(class3, time3)

    @staticmethod
    def build_schedule_item(class_, time):
        item = serializers.ClassSerializer(class_).data
        time = serializers.TimeSerializer(time).data
        item['time_start'] = time['time_start']
        item['time_end'] = time['time_end']
        return item

    def test_schedule(self):
        """FR_Id_10
        When you change the viewing date, the schedule for the selected date is displayed.

        FR_Id_11
        If no classes are set for the date that the user is viewing, a message about no classes is displayed.

        FR_Id_12
        Classes are displayed in ascending order (sorted by start time).
        """
        test_data = [
            ('2020-01-01', [self.schedule_item2, self.schedule_item3]),
            ('2020-01-02', [self.schedule_item3]),
            ('2020-01-03', []),
            ('2020-01-04', []),
            ('2020-01-05', []),
            ('2020-01-06', [self.schedule_item1]),
            ('2020-01-07', [self.schedule_item1, self.schedule_item2]),
            ('2020-01-08', [self.schedule_item2, self.schedule_item3]),
            ('2020-01-09', [self.schedule_item3]),
            ('2020-01-10', []),
            ('2020-01-11', []),
            ('2020-01-12', []),
            ('2020-01-13', [self.schedule_item1]),
            ('2020-01-14', [self.schedule_item1, self.schedule_item2]),
        ]
        for date, schedule in test_data:
            response = self.client.get(reverse(views.schedule, kwargs={'date': date}))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, schedule)

    def test_schedule_invalid_date(self):
        response = self.client.get(reverse(views.schedule, kwargs={'date': '2020-13-32'}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskTests(APITestCase):

    def setUp(self):
        self.superuser_credentials = dict(username='admin', password='admin')
        self.user_credentials = dict(username='user', password='user')
        self.superuser = User.objects.create_superuser(**self.superuser_credentials)
        self.user = User.objects.create_user(**self.user_credentials)
        self.superuser.save()
        self.user.save()
        self.client.login(**self.user_credentials)

    def test_add_task(self):
        """FR_Id_24
        The system must grant the user access to add tasks.

        FR_Id_25
        the System should allow the user to enter the following information about the issue:
        1) title
        2) description
        3) date
        4) priority (possible values: none, low, medium, high)
        """
        for priority in (0, 1, 2, 3):
            response = self.client.post(reverse('task-list'), {
                'title': 'Tesk task',
                'description': 'Test description',
                'priority': priority,
                'due_date': '2020-01-01',
            })
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_tasks(self):
        """FR_Id_26
        Issues are displayed grouped by date and sorted by priority.
        """
        tasks = [
            models.Task(title='Task1', due_date='2020-01-01', owner=self.user),
            models.Task(title='Task1', due_date='2020-01-03', owner=self.user),
            models.Task(title='Task1', due_date='2020-01-02', owner=self.user),
            models.Task(title='Task1', due_date='2020-01-04', owner=self.user)
        ]
        for task in tasks:
            task.save()
        tasks = [serializers.TaskSerializer().to_representation(task) for task in tasks]
        tasks = sorted(tasks, key=itemgetter('due_date'), reverse=True)
        response = self.client.get(reverse('task-list'))
        self.assertEqual(response.data, tasks)

    def test_privileges(self):
        admin_task = models.Task(title='Admin task', owner=self.superuser)
        regular_task = models.Task(title='Regular task', owner=self.user)
        admin_task.save()
        regular_task.save()
        self.client.login(**self.superuser_credentials)
        response = self.client.get(reverse('task-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.TaskSerializer().to_representation(admin_task),
            serializers.TaskSerializer().to_representation(regular_task)
        ])
        self.client.login(**self.user_credentials)
        response = self.client.get(reverse('task-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [
            serializers.TaskSerializer().to_representation(regular_task)
        ])
