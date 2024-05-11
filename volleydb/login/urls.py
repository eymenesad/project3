from django.urls import path
from . import views
from .views import login_view, dashboard_view, jury_dashboard_view, manager_dashboard_view, player_dashboard_view, coach_dashboard_view

urlpatterns=[
    path('', views.login_view, name='login'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('jury_dashboard/', jury_dashboard_view, name='jury_dashboard'),
    path('coach_dashboard/', coach_dashboard_view, name='coach_dashboard'),
    path('player_dashboard/', player_dashboard_view, name='player_dashboard'),
    path('manager_dashboard/', manager_dashboard_view, name='manager_dashboard'),
]