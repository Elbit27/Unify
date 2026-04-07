from django.shortcuts import render
from .models import Lesson

def schedule_view(request):
    user = request.user

    if user.role == 'student':
        lessons = Lesson.objects.filter(course__plan__group=user.group)
    else:
        lessons = Lesson.objects.filter(course__teacher=user)

    lessons = lessons.select_related(
        'course__subject',
        'course__plan__group',
        'course__teacher',
        'room__campus'
    ).order_by('date', 'lesson_number')

    days = {i: [] for i in range(1, 7)}

    for lesson in lessons:
        day_num = lesson.date.weekday() + 1
        if day_num in days:
            days[day_num].append(lesson)

    return render(request, 'schedule/schedule.html', {'schedule': days})