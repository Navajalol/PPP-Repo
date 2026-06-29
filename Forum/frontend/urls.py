from django.urls import path
from . import views

urlpatterns = [
    path('', views.frontend, name = 'frontend'),
    path('run/' , views.run_query, name='run_query'), 
    path('debug/', views.debug_settings, name='debug'),
]