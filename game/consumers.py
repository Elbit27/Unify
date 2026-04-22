import json
from django.core.cache import cache
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Team


class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        self.cache_key = f'game_state_{self.game_id}'  # Ключ для Redis
        self.user = self.scope.get('user')

        is_teacher = getattr(self.user, 'role', None) == 'teacher'

        state = cache.get(self.cache_key)
        if state and state.get('game_active') and not is_teacher:
            await self.accept()  # Сначала принимаем, чтобы отправить сообщение об ошибке
            await self.send(text_data=json.dumps({
                'type': 'ERROR',
                'message': 'Игра уже началась, вход воспрещен.'
            }))
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.user and self.user.is_authenticated:
            await database_sync_to_async(self.ensure_player_exists)()
            await self.broadcast_room_update()

    def ensure_player_exists(self):
        from .models import Player
        Player.objects.get_or_create(user=self.user, game_id=self.game_id)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get('action')

        # --- ЛОГИКА ДО НАЧАЛА ИГРЫ ---
        if action == 'create_team':
            team_name = data.get('name')
            await database_sync_to_async(Team.objects.create)(
                game_id=self.game_id,
                name=team_name
            )
            await self.broadcast_room_update()

        elif action == 'join_team':
            team_id = data.get('team_id')
            await database_sync_to_async(self.update_player_team)(team_id)
            await self.broadcast_room_update()

        elif action == 'delete_team':
            # Проверяем, что удаляет учитель (или тот, кто имеет права)
            if hasattr(self.user, 'role') and self.user.role == 'teacher':
                team_id = data.get('team_id')
                await database_sync_to_async(self.perform_delete_team)(team_id)
                await self.broadcast_room_update()

        # --- ЛОГИКА ИГРЫ С ИСПОЛЬЗОВАНИЕМ КЭША ---
        elif action == 'start_game':
            if hasattr(self.user, 'role') and self.user.role == 'teacher':
                lobby_data = await database_sync_to_async(self.get_lobby_data)()
                initial_state = {
                    'current_idx': 0,
                    'scores': {},
                    'player_scores': {},
                    'blocked_teams': [],
                    'game_active': True
                }
                # Сохраняем в Redis на 2 часа (7200 сек)
                cache.set(self.cache_key, initial_state, 7200)
                kick_list = [
                    username for username, p in lobby_data['players'].items()
                    if p['team_id'] is None and not p['is_teacher']
                ]

                await self.channel_layer.group_send(
                    self.room_group_name, {
                        'type': 'game_start_broadcast',
                        'kick_list': kick_list
                    }
                )

        elif action == 'reset_game':
            # Только учитель может сбросить игру
            if hasattr(self.user, 'role') and self.user.role == 'teacher':
                # 1. Удаляем состояние игры из кэша
                cache.delete(self.cache_key)

                # 2. Оповещаем всех участников, что игра сброшена
                await self.channel_layer.group_send(
                    self.room_group_name, {
                        'type': 'game_reset_broadcast'
                    }
                )

        elif action == 'submit_answer':
            lock_key = f"lock_game_submit_{self.game_id}"
            with cache.lock(lock_key, timeout=5):
                state = cache.get(self.cache_key)
                if not state or not state.get('game_active'):
                    return
                lobby_data = await database_sync_to_async(self.get_lobby_data)()
                user_info = lobby_data['players'].get(self.user.username, {})
                team_id = str(user_info.get('team_id')) if user_info.get('team_id') else None
                all_teams = [str(t['id']) for t in lobby_data['teams']]
                total_teams_count = len(all_teams)
                max_blocked = max(1, total_teams_count - 1)
                if not team_id or team_id in state['blocked_teams']:
                    return
                is_correct = data.get('is_correct')
                total_q = data.get('total_questions', 0)
                current_answer_text = data.get('answer_text')
                if is_correct:
                    state['scores'][team_id] = state['scores'].get(team_id, 0) + 1
                    state['player_scores'][self.user.username] = state['player_scores'].get(self.user.username, 0) + 1
                    state['blocked_teams'] = []  # При верном ответе разблокируем всех
                    winner_name = self.user.first_name if self.user.first_name else self.user.username
                    if state['current_idx'] >= total_q - 1:
                        state['game_active'] = False
                        cache.set(self.cache_key, state, 7200)  # Сохраняем перед выходом из лока
                        team_names = {str(t['id']): t['name'] for t in lobby_data['teams']}
                        await self.channel_layer.group_send(self.room_group_name, {
                            'type': 'game_over_broadcast',
                            'scores': state['scores'],
                            'team_names': team_names,
                            'player_stats': state['player_scores']
                        })
                    else:
                        state['current_idx'] += 1
                        cache.set(self.cache_key, state, 7200)  # Сохраняем перед выходом из лока
                        await self.channel_layer.group_send(self.room_group_name, {
                            'type': 'next_question_broadcast',
                            'new_idx': state['current_idx'],
                            'new_scores': state['scores'],
                            'player_stats': state['player_scores'],
                            'winner_name': winner_name,
                            'correct_answer': current_answer_text
                        })
                else:
                    if team_id not in state['blocked_teams']:
                        state['blocked_teams'].append(team_id)
                    while len(state['blocked_teams']) > max_blocked:
                        state['blocked_teams'].pop(0)
                    if len(state['blocked_teams']) >= total_teams_count:
                        state['blocked_teams'] = []
                    cache.set(self.cache_key, state, 7200)  # Сохраняем изменения
                    await self.channel_layer.group_send(self.room_group_name, {
                        'type': 'team_blocked_broadcast',
                        'team': team_id,
                        'wrong_answer': current_answer_text,
                        'blocked_list': state['blocked_teams']

                    })

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ---

    def update_player_team(self, team_id):
        from .models import Player, Team
        try:
            team = Team.objects.get(id=team_id, game_id=self.game_id)
            Player.objects.update_or_create(
                user=self.user, game_id=self.game_id,
                defaults={'team': team}
            )
        except Team.DoesNotExist:
            pass

    def perform_delete_team(self, team_id):
        from .models import Team, Player
        try:
            team = Team.objects.get(id=team_id, game_id=self.game_id)
            Player.objects.filter(team=team).update(team=None)
            team.delete()
        except Team.DoesNotExist:
            pass

    async def broadcast_room_update(self):
        data = await database_sync_to_async(self.get_lobby_data)()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'room_update_message',
                'players': data['players'],
                'teams': data['teams']
            }
        )

    def get_lobby_data(self):
        from .models import Player, Team
        teams = Team.objects.filter(game_id=self.game_id)
        teams_list = [{'id': t.id, 'name': t.name} for t in teams]

        players = Player.objects.filter(game_id=self.game_id).select_related('team', 'user')

        players_dict = {}
        for p in players:
            display_name = p.user.username
            if p.user.first_name:
                if p.user.last_name:
                    display_name = f"{p.user.first_name} {p.user.last_name[0]}."
                else:
                    display_name = p.user.first_name

            is_teacher = getattr(p.user, 'role', None) == 'teacher'

            players_dict[p.user.username] = {
                'display_name': display_name,
                'team_name': p.team.name if p.team else "Без команды",
                'team_id': p.team.id if p.team else None,
                'is_teacher': is_teacher

            }

        return {'teams': teams_list, 'players': players_dict}

    async def room_update_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ROOM_UPDATE',
            'players': event.get('players', {}),
            'teams': event.get('teams', [])
        }))

    async def game_start_broadcast(self, event):
        kick_list = event.get('kick_list', [])

        # Если текущий пользователь в списке тех, кто не выбрал команду
        if self.user.username in kick_list:
            await self.send(text_data=json.dumps({
                'type': 'KICKED',
                'reason': 'Вы не успели вступить в команду до начала игры.'
            }))
            await self.close()
        else:
            await self.send(text_data=json.dumps({'type': 'GAME_START'}))

    async def team_blocked_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'TEAM_BLOCKED',
            'team': event['team'],
            'wrong_answer': event.get('wrong_answer'),
            'blocked_list': event.get('blocked_list', [])
        }))

    async def next_question_broadcast(self, event):
        lobby_data = await database_sync_to_async(self.get_lobby_data)()
        team_names = {str(t['id']): t['name'] for t in lobby_data['teams']}
        await self.send(text_data=json.dumps({
            'type': 'NEXT_QUESTION',
            'new_idx': event['new_idx'],
            'scores': event['new_scores'],
            'team_names': team_names,
            'player_stats': event['player_stats'],
            'winner_name': event.get('winner_name'),
            'correct_answer': event.get('correct_answer')
        }))

    async def game_over_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'GAME_OVER',
            'scores': event['scores'],
            'team_names': event.get('team_names', {}),
            'player_stats': event['player_stats']
        }))

    async def disconnect(self, close_code):
        if self.user and self.user.is_authenticated:
            await database_sync_to_async(self.remove_player_from_game)()

        # Проверяем, остался ли кто-то в группе Channels
        # Если это был последний участник, сбрасываем состояние игры в кэше
        remaining_players_count = await database_sync_to_async(self.get_players_count)()

        if remaining_players_count == 0:
            cache.delete(self.cache_key)  # Полностью удаляем игру из памяти Redis
            # Опционально: можно удалить и замок, если он остался
            cache.delete(f"lock_game_submit_{self.game_id}")

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.broadcast_room_update()

    def get_players_count(self):
        from .models import Player
        return Player.objects.filter(game_id=self.game_id).count()

    def remove_player_from_game(self):
        from .models import Player
        Player.objects.filter(user=self.user, game_id=self.game_id).delete()

    async def game_reset_broadcast(self, event):
        # Отправляем сообщение напрямую в WebSocket фронтенда
        await self.send(text_data=json.dumps({
            'type': 'GAME_RESET'
        }))