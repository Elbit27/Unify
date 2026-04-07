from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Grade(models.Model):
    SEMESTER_CHOICES = (
        (1, '1 семестр'),
        (2, '2 семестр'),
    )

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                limit_choices_to={'role': 'student'}, related_name='grades')
    subject = models.ForeignKey('users.Subject', on_delete=models.CASCADE)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    course = models.PositiveIntegerField(default=1)

    module_1 = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    module_2 = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    final_exam = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    def save(self, *args, **kwargs):
        if not self.pk and self.student and self.student.group:
            self.course = self.student.group.course
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('student', 'subject', 'semester', 'course')
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"

    @property
    def total_score(self):
        return (self.module_1 * 0.4) + (self.module_2 * 0.4) + (self.final_exam * 0.2)

    def __str__(self):
        return f"{self.student.username} | {self.subject.name} | Сем {self.semester}: {self.total_score}"



