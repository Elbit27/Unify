from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Faculty(models.Model):
    name = models.CharField(max_length=255, verbose_name="Факультет")

    class Meta:
        verbose_name = "Факультет"
        verbose_name_plural = "Факультеты"

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField(max_length=50, verbose_name="Группа")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="groups")
    start_year = models.PositiveIntegerField(default=timezone.now().year, verbose_name="Год поступления")

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    @property
    def current_course(self):
        now = timezone.now()
        current_academic_year = now.year if now.month >= 9 else now.year - 1
        course = current_academic_year - self.start_year + 1
        return max(1, min(course, 4))

    def __str__(self):
        return f"{self.name} ({self.current_course} курс)"


class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название кафедры")
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="departments")

    class Meta:
        verbose_name = "Кафедра"
        verbose_name_plural = "Кафедры"

    def __str__(self):
        return f"{self.name} ({self.faculty.name})"


class Subject(models.Model):
    name = models.CharField(max_length=255, verbose_name="Предмет")
    credits = models.PositiveSmallIntegerField(verbose_name="Кредиты")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    def __str__(self):
        return f"{self.name} ({self.credits} кр.)"

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name="Роль")
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Факультет")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Группа")
    subjects = models.ManyToManyField(
        'Subject',
        blank=True,
        related_name='teachers',
        verbose_name='Преподаваемые предметы'
    )
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Кафедра")

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",
        blank=True,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class SemesterPlan(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="plans")
    course_number = models.PositiveSmallIntegerField(verbose_name="Курс")
    semester = models.PositiveSmallIntegerField(
        choices=((1, '1 семестр'), (2, '2 семестр')),
        verbose_name="Семестр"
    )

    class Meta:
        verbose_name = "Учебный план на семестр"
        verbose_name_plural = "Учебные планы"
        unique_together = ('group', 'course_number', 'semester') # Чтобы не создать два одинаковых плана

    def __str__(self):
        return f"{self.group.name} | {self.course_number} курс | {self.semester} сем."

class SemesterSubject(models.Model):
    plan = models.ForeignKey(SemesterPlan, on_delete=models.CASCADE, related_name="subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})

    class Meta:
        verbose_name = "Предмет плана"
        verbose_name_plural = "Предметы плана"

    def __str__(self):
        # Это то, что ты увидишь в выпадающем списке
        return f"{self.subject.name} | {self.plan.group.name} ({self.plan.course_number} курс)"