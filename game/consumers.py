import json
from channels.generic.websocket import AsyncWebsocketConsumer


class GameConsumer(AsyncWebsocketConsumer):
    room_states = {}

    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = f'game_{self.game_id}'
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.room_group_name not in self.room_states:
            self.room_states[self.room_group_name] = {
                'players': {},
                'current_idx': 0,
                'scores': {'A': 0, 'B': 0},
                'player_scores': {},
                'blocked_teams': [],
                'game_active': False
            }

        state = self.room_states[self.room_group_name]
        # Авто-распределение по командам
        players = state['players']
        if self.user.username not in players:
            team = 'A' if len(players) % 2 == 0 else 'B'
            players[self.user.username] = {'team': team}

        await self.channel_layer.group_send(
            self.room_group_name, {'type': 'room_update_message', 'players': players}
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        # Если сервер ребутнулся, а игрок шлет экшен, восстанавливаем базу комнаты
        if self.room_group_name not in self.room_states:
            return  # Либо шлем сигнал REFRESH_PAGE на фронт

        state = self.room_states[self.room_group_name]

        if action == 'join_team':
            team = data.get('team')
            if self.user.username in state['players']:
                state['players'][self.user.username]['team'] = team
            await self.channel_layer.group_send(
                self.room_group_name, {'type': 'room_update_message', 'players': state['players']}
            )

        elif action == 'start_game':
            state.update({
                'game_active': True,
                'current_idx': 0,
                'scores': {'A': 0, 'B': 0},
                'player_scores': {},
                'blocked_teams': []
            })
            await self.channel_layer.group_send(self.room_group_name, {'type': 'game_start_broadcast'})

        elif action == 'submit_answer':
            if not state['game_active']: return

            user_team = state['players'].get(self.user.username, {}).get('team')
            if not user_team or user_team in state['blocked_teams']:
                return

            is_correct = data.get('is_correct')
            total_questions = data.get('total_questions', 10)  # Фронт должен прислать сколько всего вопросов

            if is_correct:
                state['scores'][user_team] += 1
                username = self.user.username
                state['player_scores'][username] = state['player_scores'].get(username, 0) + 1
                state['blocked_teams'] = []

                # ПРОВЕРКА НА КОНЕЦ ИГРЫ
                if state['current_idx'] >= total_questions - 1:
                    state['game_active'] = False
                    await self.channel_layer.group_send(self.room_group_name, {
                        'type': 'game_over_broadcast',
                        'final_scores': state['scores'],
                        'winner_team': user_team,
                        'player_stats': state['player_scores']
                    })
                else:
                    state['current_idx'] += 1
                    await self.channel_layer.group_send(self.room_group_name, {
                        'type': 'next_question_broadcast',
                        'winner_name': username,
                        'new_scores': state['scores'],
                        'player_stats': state['player_scores'],
                        'new_idx': state['current_idx']
                    })
            else:
                if user_team not in state['blocked_teams']:
                    state['blocked_teams'].append(user_team)

                is_everyone_blocked = len(state['blocked_teams']) >= 2
                if is_everyone_blocked:
                    state['blocked_teams'] = []

                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'team_blocked_broadcast',
                    'team': user_team,
                    'user': self.user.username,
                    'reset_all': is_everyone_blocked
                })

    # Методы-рассыльщики (броадкасты)
    async def game_start_broadcast(self, event):
        await self.send(text_data=json.dumps({'type': 'GAME_START'}))

    async def game_over_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'GAME_OVER',
            'scores': event['final_scores'],
            'player_stats': event['player_stats']
        }))

    async def next_question_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'NEXT_QUESTION',
            'new_idx': event['new_idx'],
            'scores': event['new_scores'],
            'player_stats': event['player_stats'],
            'last_winner': event['winner_name']
        }))

    async def team_blocked_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'TEAM_BLOCKED',
            'team': event['team'],
            'user': event['user'],
            'reset_all': event['reset_all']
        }))

    async def room_update_message(self, event):
        await self.send(text_data=json.dumps({'type': 'ROOM_UPDATE', 'players': event['players']}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if self.room_group_name in self.room_states:
            players = self.room_states[self.room_group_name]['players']
            players.pop(self.user.username, None)
            if not players:
                self.room_states.pop(self.room_group_name, None)
            else:
                await self.channel_layer.group_send(
                    self.room_group_name, {'type': 'room_update_message', 'players': players}
                )