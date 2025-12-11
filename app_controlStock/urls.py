from django.urls import path
from . import views

app_name = 'app_controlStock'

urlpatterns = [
    path('setup-mock/', views.setup_mock, name='setup_mock'),  # ← PRIMERO
    path('', views.controlStock_view, name='controlStock'),
    path('pendientes/', views.controlPendientes_view, name='controlPendientes'),
    path('registrar/', views.stockControlado_view, name='stockControlado'),
    path('logout/', views.logout_view, name='logout'),
]