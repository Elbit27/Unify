from django.db import models
from django.conf import settings
from datetime import timedelta

LESSON_TYPES = (
        ('lecture', 'Лекция'),
        ('practice', 'Практика'),
        ('lab', 'Лабораторная'),
    )

DAYS = (
    (1, 'Понедельник'), (2, 'Вторник'), (3, 'Среда'),
    (4, 'Четверг'), (5, 'Пятница'), (6, 'Суббота'),
)

LESSON_TIMES = (
    (1, '08:00 – 09:20'),
    (2, '09:30 – 10:50'),
    (3, '11:00 – 12:20'),
    (4, '12:30 – 13:50'),
)

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
    course = models.ForeignKey('users.SemesterSubject', on_delete=models.CASCADE, related_name='lessons', verbose_name="Курс")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, verbose_name="Кабинет")
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, verbose_name="Тип занятия")
    date = models.DateField(verbose_name="Дата занятия")
    lesson_number = models.IntegerField(choices=LESSON_TIMES, verbose_name="Пара №")

    @staticmethod
    def generate(start_date, end_date):
        slots = ScheduleSlot.objects.all()
        print(f"Найдено слотов в базе: {slots.count()}")  # ОТЛАДКА

        current_date = start_date
        created_count = 0

        while current_date <= end_date:
            current_weekday = current_date.weekday() + 1
            day_slots = slots.filter(day_of_week=current_weekday)

            if day_slots.exists():
                print(f"Нашел {day_slots.count()} слотов для даты {current_date}")  # ОТЛАДКА

            for slot in day_slots:
                obj, created = Lesson.objects.get_or_create(
                    course=slot.semester_subject,
                    date=current_date,
                    lesson_number=slot.lesson_number,
                    lesson_type=slot.lesson_type,
                    defaults={'room': slot.room}
                )
                if created:
                    created_count += 1

            current_date += timedelta(days=1)
        return created_count

    class Meta:
        verbose_name = "Занятие (факт)"
        verbose_name_plural = "Занятия (факты)"
        unique_together = ('room', 'date', 'lesson_number')

    def __str__(self):
        return f"{self.date} | Пара №{self.lesson_number} | {self.course.subject.name} ({self.course.plan.group.name})"


class ScheduleSlot(models.Model):
    semester_subject = models.ForeignKey('users.SemesterSubject', on_delete=models.CASCADE)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='practice', verbose_name="Тип занятия")
    day_of_week = models.IntegerField(choices=DAYS, verbose_name="День недели")
    lesson_number = models.IntegerField(choices=LESSON_TIMES, verbose_name="Пара №")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Расписание (шаблон)"
        verbose_name_plural = "Расписание (шаблоны)"

    def __str__(self):
        return f"{self.get_day_of_week_display()} | {self.get_lesson_number_display()} | {self.semester_subject}"


class Attendance(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='attendances'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Занятие"
    )
    is_present = models.BooleanField(default=True, verbose_name="Присутствует")
    class Meta:
        unique_together = ('student', 'lesson')
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"

    def __str__(self):
        status = "Был" if self.is_present else "Н/Б"
        return f"{self.student} | {self.lesson.date} | {status}"
