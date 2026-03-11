"""
WebSocket consumers for PvP mode.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import Room, RoomPlayer, GameState
from .game_ar import generate_ar_neighbors_state, check_ar_neighbors_answer


class PvpGameConsumer(AsyncWebsocketConsumer):
    """Consumer for PvP games - connects users to rooms, broadcasts moves."""

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room_id')
        if not self.room_id:
            await self.close()
            return
        self.room_group_name = f'pvp_room_{self.room_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # For ar_neighbors: when 2 players, generate state and broadcast
        room = await self._get_room()
        player_count = await self._get_room_player_count() if room else 0
        if room and room.game_type == 'ar_neighbors' and player_count >= 2:
            state = await self._get_or_create_ar_neighbors_state()
            if state:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_message',
                        'action': 'state',
                        'payload': state,
                    }
                )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                action = data.get('action', '')
                payload = data.get('payload', {})

                if action == 'move':
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'game_message',
                            'action': 'move',
                            'payload': payload,
                            'user_id': self.scope['user'].id if self.scope['user'].is_authenticated else None,
                        }
                    )

                elif action == 'check' and payload:
                    room = await self._get_room()
                    if room and room.game_type == 'ar_neighbors':
                        gs = await self._get_game_state()
                        if gs and 'center' in gs:
                            ok, expected = await database_sync_to_async(
                                lambda: check_ar_neighbors_answer(
                                    payload.get('cell1'), payload.get('cell2'),
                                    payload.get('cell4'), payload.get('cell5'),
                                    gs['center']
                                )
                            )()
                            await self.channel_layer.group_send(
                                self.room_group_name,
                                {
                                    'type': 'game_message',
                                    'action': 'result',
                                    'payload': {
                                        'ok': ok,
                                        'expected': list(expected) if expected else [],
                                        'user_id': self.scope['user'].id if self.scope['user'].is_authenticated else None,
                                    },
                                }
                            )
            except json.JSONDecodeError:
                pass

    @database_sync_to_async
    def _get_room(self):
        try:
            return Room.objects.get(pk=self.room_id)
        except (Room.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def _get_room_player_count(self):
        return RoomPlayer.objects.filter(room_id=self.room_id).count()

    @database_sync_to_async
    def _get_game_state(self):
        try:
            room = Room.objects.get(pk=self.room_id)
            gs = GameState.objects.filter(room=room).first()
            return gs.state if gs else None
        except (Room.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def _get_or_create_ar_neighbors_state(self):
        try:
            room = Room.objects.get(pk=self.room_id)
            gs, _ = GameState.objects.get_or_create(room=room, defaults={'state': {}})
            if not gs.state or 'center' not in gs.state:
                gs.state = generate_ar_neighbors_state()
                gs.save(update_fields=['state'])
            return gs.state
        except (Room.DoesNotExist, ValueError):
            return None

    async def game_message(self, event):
        """Broadcast game message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': event.get('type', 'game_message'),
            'action': event.get('action'),
            'payload': event.get('payload', {}),
            'user_id': event.get('user_id'),
        }))
