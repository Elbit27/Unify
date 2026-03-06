from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet
from . import serializers
from .models import Game
from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from .ai_services import generate_quiz_data


def game_list(request):
    games = Game.objects.all()
    return render(request, 'game/GameList.html', {'games': games})

def play_game(request, game_id):
    game = Game.objects.get(id=game_id)
    # Мы передаем игру, а вопросы подтянем через сериализатор или прямо в шаблоне
    return render(request, 'game/PlayGame.html', {'game': game})



# Эта функция НУЖНА для отображения страницы конструктора
def game_manage_page(request, pk=None):
    game = None
    if pk:
        # Важно подтянуть вопросы и ответы сразу (prefetch_related), чтобы не тормозило
        game = get_object_or_404(Game.objects.prefetch_related('questions__answers'), pk=pk)

    return render(request, 'game/CreateUpdateGame.html', {'game': game})

class GameViewSet(ModelViewSet):
    queryset = Game.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.GameSerializer
        elif self.action in ('create', 'update', 'partial_update', 'generate_ai'):
            return serializers.GameSerializer
        elif self.action in ('destroy', 'retrieve'):
            return serializers.GameDetailSerializer

    def get_permissions(self):
        # удалять может только автор поста или админ
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAdminUser(), ]
        return [permissions.IsAuthenticatedOrReadOnly(), ]

    @action(detail=False, methods=['post', 'get'], permission_classes=[permissions.IsAuthenticated])
    def generate_ai(self, request):
        topic = request.data.get('topic')
        if not topic:
            return Response({"error": "Укажите тему (topic)"}, status=400)

        try:
            ai_data = generate_quiz_data(topic)
            print(f"DEBUG AI DATA: {ai_data}")

            serializer = self.get_serializer(
                data=ai_data,
                context={'request': request}
            )

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)

            return Response({
                "error": "ИИ создал некорректные данные",
                "details": serializer.errors
            }, status=400)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
