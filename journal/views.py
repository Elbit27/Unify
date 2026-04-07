from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from account.models import Subject, Group, User, SemesterSubject
from .models import Grade
from django.utils import timezone
from django.db.models import F


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
    """Шаг 3: Ведомость оценок (Исправлено под новую структуру)"""
    subject = get_object_or_404(Subject, id=subject_id)
    group = get_object_or_404(Group, id=group_id)

    sem_subject = get_object_or_404(
        SemesterSubject,
        subject=subject,
        plan__group=group,
        teacher=request.user
    )

    plan = sem_subject.plan
    semester = int(request.GET.get('semester', plan.semester))
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
                course=plan.course_number,
                defaults={
                    'module_1': float(m1) if m1 else 0,
                    'module_2': float(m2) if m2 else 0,
                    'final_exam': float(final) if final else 0,
                }
            )
        messages.success(request, "Ведомость успешно обновлена!")
        return redirect(request.get_full_path())

    grades = Grade.objects.filter(subject=subject, semester=semester, student__group=group)
    grades_dict = {g.student_id: g for g in grades}

    for student in students:
        student.current_grade = grades_dict.get(student.id)

    return render(request, 'journal/journal_table.html', {
        'subject': subject,
        'group': group,
        'students': students,
        'semester': semester
    })