from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .forms import SiteLoginForm


urlpatterns = [
    path('', views.index, name='homepage_index'),
    path('chaevye/', views.chaevye, name='tip_jar'),
    path('spasibo/', views.tip_thanks, name='tip_thanks'),
    path('avtory/', views.authors_page, name='site_authors'),
    path('boomerang/', views.boomerang_test, name='boomerang_test'),
    path("register/", views.register, name="register"),
    path("register/sent/", views.register_verify_sent, name="register_verify_sent"),
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