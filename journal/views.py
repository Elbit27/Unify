from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, F
from django.utils import timezone
from django.http import JsonResponse
from account.models import Subject, Group, User, SemesterSubject
from schedule.models import Attendance, Lesson
from .models import Grade
import json


@login_required
def subject_list_view(request):
    if request.user.role != 'teacher':
        return redirect('profile')

    now = timezone.now()
    default_year = now.year if now.month >= 9 else now.year - 1
    default_sem = 2 if 2 <= now.month <= 8 else 1

    selected_year = int(request.GET.get('year', default_year))
    selected_sem = int(request.GET.get('semester', default_sem))

    subjects = Subject.objects.filter(
        semestersubject__teacher=request.user,
        semestersubject__plan__semester=selected_sem,
        semestersubject__plan__group__start_year=selected_year - F('semestersubject__plan__course_number') + 1
    ).distinct()

    years_range = range(default_year - 2, default_year + 1)

    return render(request, 'journal/subjects.html', {
        'subjects': subjects,
        'years_range': years_range,
        'current_year': selected_year,
        'current_semester': selected_sem,
    })

@login_required
def group_list_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    groups = Group.objects.filter(
        plans__subjects__subject=subject,
        plans__subjects__teacher=request.user
    ).annotate(
        course_from_plan=F('plans__course_number')
    ).distinct()

    return render(request, 'journal/groups.html', {
        'subject': subject,
        'groups': groups
    })


@login_required
def teacher_journal_view(request, subject_id, group_id):
    subject = get_object_or_404(Subject, id=subject_id)
    group = get_object_or_404(Group, id=group_id)

    # Это ключевой объект: он связывает всё воедино
    sem_subject = get_object_or_404(SemesterSubject, subject=subject, plan__group=group, teacher=request.user)

    semester = sem_subject.plan.semester
    students = User.objects.filter(group=group, role='student').order_by('last_name')

    if request.method == 'POST':
        for student in students:
            m1 = request.POST.get(f'm1_{student.id}', 0)
            m2 = request.POST.get(f'm2_{student.id}', 0)
            final = request.POST.get(f'final_{student.id}', 0)

            Grade.objects.update_or_create(
                student=student,
                subject=subject,
                semester=semester,
                defaults={
                    'module_1': float(m1) if m1 else 0,
                    'module_2': float(m2) if m2 else 0,
                    'final_exam': float(final) if final else 0,
                }
            )
        return redirect(request.path)

    lessons = Lesson.objects.filter(course=sem_subject).order_by('date', 'lesson_number')

    absents = Attendance.objects.filter(lesson__in=lessons, is_present=False)
    absent_map = {f"{a.student_id}_{a.lesson_id}" for a in absents}

    for student in students:
        student.current_grade = Grade.objects.filter(
            student=student,
            subject=subject,
            semester=semester
        ).first()

    return render(request, 'journal/journal_table.html', {
        'subject': subject,
        'group': group,
        'students': students,
        'lessons': lessons,
        'absent_map': absent_map,
    })

@login_required
@require_POST
def update_attendance_ajax(request):
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        lesson_id = data.get('lesson_id')
        is_absent = data.get('is_absent')

        if is_absent:
            Attendance.objects.update_or_create(
                student_id=student_id,
                lesson_id=lesson_id,
                defaults={'is_present': False}
            )
        else:
            Attendance.objects.filter(student_id=student_id, lesson_id=lesson_id).delete()

        return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)