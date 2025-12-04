from django.urls import path
from . import views

app_name = 'app_controlStock'

urlpatterns = [
    path('', views.controlStock_view, name='controlStock'),
    path('logout/', views.logout_view, name='logout'),
    # path('', views.index, name='index'),
]
