from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html", authentication_form=LoginForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("matches/", views.matches, name="matches"),
    path("compare/", views.compare, name="compare"),
    path("history/", views.history, name="history"),
    path("history/<int:pk>/edit/", views.edit_history, name="history_edit"),
    path("history/<int:pk>/delete/", views.delete_history, name="history_delete"),
]
