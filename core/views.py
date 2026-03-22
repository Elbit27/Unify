from django.shortcuts import render
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required
from game.models import Game

def frontpage(request):
    return render(request, 'core/frontpage.html')

@login_required
def profile_view(request):
    user_games = Game.objects.filter(created_by=request.user).order_by('-created_at')

    context = {
        'user': request.user,
        'games': user_games,
        'games_count': user_games.count(),
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