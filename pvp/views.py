from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db.models import Count

from .models import Room, RoomPlayer


@login_required(login_url='/accounts/login/')
def pvp_index(request):
    """PvP lobby - create or find game."""
    return render(request, 'pvp/index.html', {
        'room_game_types': Room.GAME_TYPES,
    })


@login_required(login_url='/accounts/login/')
def room_create(request):
    """Create a new PvP room."""
    game_type = request.GET.get('game') or request.POST.get('game', 'ar_neighbors')
    if game_type not in dict(Room.GAME_TYPES):
        game_type = 'ar_neighbors'
    room = Room.objects.create(game_type=game_type, status='waiting')
    RoomPlayer.objects.create(room=room, user=request.user)
    return redirect('pvp_room_detail', room_id=str(room.pk))


@login_required(login_url='/accounts/login/')
def room_find(request):
    """Find a waiting room or create new."""
    game_type = request.GET.get('game', 'ar_neighbors')
    if game_type not in dict(Room.GAME_TYPES):
        game_type = 'ar_neighbors'
    room = Room.objects.filter(
        game_type=game_type,
        status='waiting',
    ).exclude(players__user=request.user).annotate(
        np=Count('players')
    ).filter(np__lt=2).order_by('created_at').first()
    if room and room.players.count() < 2:
        RoomPlayer.objects.get_or_create(room=room, user=request.user)
        room.status = 'active'
        room.save()
        return redirect('pvp_room_detail', room_id=str(room.pk))
    return redirect(reverse('pvp_room_create') + '?game=' + game_type)


@login_required(login_url='/accounts/login/')
def room_detail(request, room_id):
    """Room detail - play PvP game."""
    room = get_object_or_404(Room, pk=room_id)
    if not room.players.filter(user=request.user).exists():
        if room.players.count() >= 2:
            return redirect('pvp_index')
        RoomPlayer.objects.create(room=room, user=request.user)
    ws_scheme = 'wss' if request.is_secure() else 'ws'
    ws_url = f'{ws_scheme}://{request.get_host()}/ws/pvp/room/{room_id}/'
    return render(request, 'pvp/room.html', {
        'room': room,
        'ws_url': ws_url,
    })
