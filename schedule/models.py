from django.db import models
from django.conf import settings

class Campus(models.Model):
    number = models.CharField(max_length=27, verbose_name="Корпус")

    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпуса"

    def __str__(self):
        return self.number


class Room(models.Model):
    number = models.CharField(max_length=999, verbose_name="Номер аудитории")
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name="rooms")

    class Meta:
        verbose_name = "Аудитория"
        verbose_name_plural = "Аудитории"

    def __str__(self):
        return f"{self.number} ({self.campus.number})"


class Lesson(models.Model):
    LESSON_TIMES = (
        (1, '08:00 – 09:20'),
        (2, '09:30 – 10:50'),
        (3, '11:00 – 12:20'),
        (4, '12:30 – 13:50'),
    )

    course = models.ForeignKey('users.SemesterSubject', on_delete=models.CASCADE, related_name='lessons', verbose_name="Курс")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, verbose_name="Кабинет")

    date = models.DateField(verbose_name="Дата занятия")
    lesson_number = models.IntegerField(choices=LESSON_TIMES, verbose_name="Пара №")

    class Meta:
        verbose_name = "Занятие (факт)"
        verbose_name_plural = "Занятия (факты)"
        unique_together = ('room', 'date', 'lesson_number')

    def __str__(self):
        return f"{self.date} | Пара №{self.lesson_number} | {self.course.subject.name} ({self.course.group.name})"


# class Attendance(models.Model):
#     lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendances')
#     student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Студент")
#     is_present = models.BooleanField(default=False, verbose_name="Присутствует")
#
#     class Meta:
#         verbose_name = "Посещаемость"
#         verbose_name_plural = "Посещаемость"
#         unique_together = ('lesson', 'student')
#
#     def __str__(self):
#         status = "Был" if self.is_present else "Н"
#         return f"{self.student.username} - {status} ({self.lesson.date})"