"""
Étudiant 4: Routes de l'application
===================================
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    path('analyser/', views.analyser, name='analyser'),
    path('resultat/<int:pk>/', views.resultat, name='resultat'),
    path('historique/', views.historique, name='historique'),
    path('detail/<int:pk>/', views.detail_analyse, name='detail'),
    path('supprimer/<int:pk>/', views.supprimer_analyse, name='supprimer'),
    
    # Export
    path('exporter/<int:pk>/<str:format>/', views.exporter_rapport, name='exporter'),
    
    # API JSON
    path('api/analyser/', views.api_analyser, name='api_analyser'),
    path('api/statistiques/', views.api_statistiques, name='api_stats'),
]