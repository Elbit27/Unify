from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Lesson, ScheduleSlot, Room
from datetime import timedelta
from django.utils import timezone
import datetime
import random
from django.shortcuts import get_object_or_404
from django.db import transaction
from account.models import Group, SemesterSubject


@login_required
def schedule_view(request):
    user = request.user
    now = timezone.now().date()

    end_date = now + timedelta(days=6)

    if user.role == 'student':
        if not user.group:
            return render(request, 'schedule/schedule.html', {'error': 'Вы не привязаны к группе'})
        lessons_queryset = Lesson.objects.filter(course__plan__group=user.group)
    else:
        lessons_queryset = Lesson.objects.filter(course__teacher=user)

    lessons = lessons_queryset.filter(
        date__range=[now, end_date]
    ).select_related(
        'course__subject', 'course__plan__group', 'course__teacher', 'room__campus'
    ).order_by('date', 'lesson_number')

    days = {i: [] for i in range(1, 7)}

    for lesson in lessons:
        day_num = lesson.date.weekday() + 1
        days[day_num].append(lesson)  # Добавляем ВСЕ пары без исключения

    return render(request, 'schedule/schedule.html', {
        'schedule': days,
        'start_date': now,
        'end_date': end_date,
        'current_day_num': now.weekday() + 1
    })


@login_required
def generate_slots_view(request, group_id):
    if not request.user.is_staff:
        return redirect('profile')

    group = get_object_or_404(Group, id=group_id)
    ScheduleSlot.objects.filter(semester_subject__plan__group=group).delete()

    subjects = list(SemesterSubject.objects.filter(plan__group=group))
    random.shuffle(subjects)

    days = [1, 2, 3, 4, 5, 6]
    slots = [1, 2, 3, 4]
    created_count = 0

    with transaction.atomic():
        for item in subjects:
            credits_value = item.subject.credits
            subject_name = item.subject.name.lower()
            needed_pairs = max(1, credits_value // 2)

            # --- ЛОГИКА ОПРЕДЕЛЕНИЯ ТИПОВ ЗАНЯТИЙ ---
            types_to_assign = []

            if "физическая культура" in subject_name or "физкультура" in subject_name:
                # Физра — всегда только практика
                types_to_assign = ['practice'] * needed_pairs

            elif credits_value >= 4:
                types_to_assign.append('lecture')
                if "анализ" in subject_name:
                    types_to_assign.append('practice')
                elif subject_name == "математика":
                    types_to_assign.append('practice')
                else:
                    types_to_assign.append('lab')

                while len(types_to_assign) < needed_pairs:
                    types_to_assign.append('lab' if "математика" not in subject_name else 'practice')

            else:
                types_to_assign = ['practice']

            # --- РАССТАНОВКА ПО ДНЯМ ---
            shuffled_days = days.copy()
            random.shuffle(shuffled_days)

            for l_type in types_to_assign:
                placed = False
                for day in shuffled_days:
                    if placed: break

                    for slot_num in slots:
                        group_busy = ScheduleSlot.objects.filter(
                            day_of_week=day,
                            lesson_number=slot_num,
                            semester_subject__plan__group=group
                        ).exists()

                        teacher_busy = ScheduleSlot.objects.filter(
                            day_of_week=day,
                            lesson_number=slot_num,
                            semester_subject__teacher=item.teacher
                        ).exists()

                        if not group_busy and not teacher_busy:
                            ScheduleSlot.objects.create(
                                semester_subject=item,
                                day_of_week=day,
                                lesson_number=slot_num,
                                lesson_type=l_type,  # Используем наш определенный тип
                                room=Room.objects.first()
                            )
                            placed = True
                            created_count += 1
                            # Чтобы Лекция и Лаба одного предмета не стояли в один день:
                            if len(shuffled_days) > 1:
                                shuffled_days.remove(day)
                            break

    messages.success(request, f"Умное расписание создано! Расставлено типов: {created_count}")
    return redirect('schedule')

@login_required
def generate_schedule_view(request):
    if not (request.user.role == 'teacher' or request.user.is_staff):
        return redirect('profile')

    # Устанавливаем четкую дату начала семестра
    start_date = datetime.date(2026, 1, 19)

    # Устанавливаем дату конца (например, конец мая или через 140 дней от старта)
    end_date = start_date + datetime.timedelta(days=140)

    try:
        count = Lesson.generate(start_date, end_date)
        messages.success(request, f"Сгенерировано {count} занятий (период: {start_date} — {end_date})")
    except Exception as e:
        messages.error(request, f"Ошибка при генерации: {e}")

    return redirect('journal-subjects')