from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='ar_index'),
    path('pvp/', views.ar_pvp_lobby, name='ar_pvp_lobby'),
    path('pvp/create/', views.ar_pvp_create_room, name='ar_pvp_create_room'),
    path('pvp/join/', views.ar_pvp_join_room, name='ar_pvp_join_room'),
    path('pvp/room/<str:code>/', views.ar_pvp_room, name='ar_pvp_room'),
    path('pvp/api/<str:code>/state/', views.ar_pvp_state, name='ar_pvp_state'),
    path('pvp/api/<str:code>/round/', views.ar_pvp_round, name='ar_pvp_round'),
    path('pvp/api/<str:code>/ready/', views.ar_pvp_toggle_ready, name='ar_pvp_toggle_ready'),
    path('pvp/api/<str:code>/answer/', views.ar_pvp_submit_answer, name='ar_pvp_submit_answer'),
    path('pvp/api/<str:code>/next/', views.ar_pvp_next_round, name='ar_pvp_next_round'),
    path('series/', views.ar_series, name='ar_series'),
    path('neighbors/', views.ar_neighbors, name='ar_neighbors'),
    path('completes/', views.ar_completes, name='ar_completes'),
    path('completes-intersection/', views.ar_completes_intersection, name='ar_completes_intersection'),
    path('series-stake/', views.ar_series_stake, name='ar_series_stake'),
    path('ar_bets/', views.ar_bets, name='ar_bets'),
    path('roulette/', views.ar_roulette, name='ar_roulette'),
    path('color_in_cash/', views.ar_roulette, name='ar_color_in_cash'),
    path('payout_through_cash/', views.ar_payout_through_cash, name='ar_payout_through_cash'),
    path('bet_reveal/', views.ar_bet_reveal, name='ar_bet_reveal'),
    path('mix/', views.ar_mix, name='ar_mix'),
    path('mix/to-ptc/', views.ar_mix_to_ptc, name='ar_mix_to_ptc'),
    path('mix/continue/', views.ar_mix_continue, name='ar_mix_continue'),
]
