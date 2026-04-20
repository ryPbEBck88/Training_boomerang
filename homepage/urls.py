from django.urls import path
from django.contrib.auth import views as auth_views

from . import sop_views, views
from .forms import SiteLoginForm


urlpatterns = [
    path('', views.index, name='homepage_index'),
    path('chaevye/', views.chaevye, name='tip_jar'),
    path('spasibo/', views.tip_thanks, name='tip_thanks'),
    path('avtory/', views.authors_page, name='site_authors'),
    path('boomerang/', sop_views.boomerang_sop_hub, name='boomerang_test'),
    path(
        'boomerang/sop/<slug:slug>/',
        sop_views.boomerang_sop_intro,
        name='boomerang_sop_intro',
    ),
    path(
        'boomerang/sop/<slug:slug>/start/',
        sop_views.boomerang_sop_start,
        name='boomerang_sop_start',
    ),
    path(
        'boomerang/sop/<slug:slug>/play/',
        sop_views.boomerang_sop_play,
        name='boomerang_sop_play',
    ),
    path(
        'boomerang/sop/<slug:slug>/results/',
        sop_views.boomerang_sop_results,
        name='boomerang_sop_results',
    ),
    path("register/", views.register, name="register"),
    path("register/sent/", views.register_verify_sent, name="register_verify_sent"),
    path("register/resend/", views.resend_activation, name="register_resend_activation"),
    path(
        "activate/<uidb64>/<token>/",
        views.activate_account,
        name="activate_account",
    ),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=SiteLoginForm,
            redirect_authenticated_user=True,
            next_page="homepage_index",
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="homepage_index"), name="logout"),
]