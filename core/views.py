from django.shortcuts import render
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required
from game.models import Game
from django.core.cache import cache
from account.models import SemesterPlan, SemesterSubject

def frontpage(request):
    return render(request, 'core/frontpage.html')


@login_required
def profile_view(request):
    user = request.user

    grades_sem1 = []
    grades_sem2 = []

    if user.role == 'student' and user.group:
        current_course = user.group.current_course

        plan_items = SemesterSubject.objects.filter(
            plan__group=user.group,
            plan__course_number=current_course
        ).select_related('subject', 'plan', 'teacher')

        user_grades = {g.subject_id: g for g in user.grades.all()}

        for item in plan_items:
            grade_obj = user_grades.get(item.subject.id)

            data = {
                'subject': item.subject,
                'teacher': item.teacher,
                'module_1': grade_obj.module_1 if grade_obj else '-',
                'module_2': grade_obj.module_2 if grade_obj else '-',
                'final_exam': grade_obj.final_exam if grade_obj else '-',
                'total_display': 0
            }

            if grade_obj:
                m1 = grade_obj.module_1 or 0
                m2 = grade_obj.module_2 or 0
                exam = grade_obj.final_exam or 0

                total = round((m1 * 0.4) + (m2 * 0.4) + (exam * 0.2))

                data.update({
                    'module_1': int(grade_obj.module_1 if grade_obj.module_1 is not None else 0),
                    'module_2': int(grade_obj.module_2 if grade_obj.module_2 is not None else 0),
                    'final_exam': grade_obj.final_exam if grade_obj.final_exam is not None else 0,
                    'total_display': total
                })

            if item.plan.semester == 1:
                grades_sem1.append(data)
            else:
                grades_sem2.append(data)

    # Логика с кэшем игр (без изменений)
    user_games = Game.objects.filter(created_by=user).order_by('-created_at')
    for game in user_games:
        cache_key = f'game_state_{game.id}'
        state = cache.get(cache_key)
        game.is_active_now = state.get('game_active', False) if state else False

    context = {
        'user': user,
        'games': user_games,
        'grades_sem1': grades_sem1,
        'grades_sem2': grades_sem2,
    }
    return render(request, 'core/profile.html', context)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet): # Только чтение
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Юзер видит только свои уведомления
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread(self, request):  # ДОБАВЬ 'request' СЮДА
        unread_notes = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread_notes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        # Находим все непрочитанные уведомления текущего юзера и обновляем их разом
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'status': 'all marked as read'})