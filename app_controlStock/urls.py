from django.urls import path
from . import views

app_name = 'app_controlStock'

urlpatterns = [
    path('', views.controlStock_view, name='controlStock'),
    path('pendientes/', views.controlPendientes_view, name='controlPendientes'),
    path('logout/', views.logout_view, name='logout'),
]