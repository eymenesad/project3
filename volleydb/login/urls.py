from django.urls import path
from . import views
from .views import login_view, dashboard_view

urlpatterns=[
    path('', views.login_view, name='login'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
]