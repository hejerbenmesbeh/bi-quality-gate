"""
Étudiant 1: Interface d'Administration Django
=============================================
Permet de gérer les données via /admin/
"""

from django.contrib import admin
from .models import AnalyseCode, Probleme


class ProblemeInline(admin.TabularInline):
    """
    Affiche les problèmes directement dans la page d'une analyse
    """
    model = Probleme
    extra = 0  # Pas de lignes vides supplémentaires
    readonly_fields = ['severite', 'categorie', 'source', 'message', 'ligne']
    can_delete = False


@admin.register(AnalyseCode)
class AnalyseCodeAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les analyses
    """
    
    # Colonnes affichées dans la liste
    list_display = [
        'nom_fichier',
        'outil',
        'score',
        'est_approuve',
        'nb_critiques',
        'nb_warnings',
        'date_creation'
    ]
    
    # Filtres dans la sidebar
    list_filter = [
        'est_approuve',
        'outil',
        'date_creation'
    ]
    
    # Recherche
    search_fields = ['nom_fichier', 'description']
    
    # Champs en lecture seule
    readonly_fields = [
        'score',
        'est_approuve',
        'temps_analyse',
        'nb_problemes_total',
        'nb_critiques',
        'nb_warnings',
        'nb_infos',
        'nb_flake8',
        'nb_bandit',
        'nb_openai',
        'nb_manuel',
        'date_creation'
    ]
    
    # Organisation des champs
    fieldsets = (
        ('Informations', {
            'fields': ('nom_fichier', 'outil', 'description', 'auteur')
        }),
        ('Code', {
            'fields': ('contenu_code',),
            'classes': ('collapse',)  # Replié par défaut
        }),
        ('Résultats', {
            'fields': (
                'score',
                'est_approuve',
                'temps_analyse',
                'nb_problemes_total'
            )
        }),
        ('Détails par sévérité', {
            'fields': ('nb_critiques', 'nb_warnings', 'nb_infos')
        }),
        ('Détails par outil', {
            'fields': ('nb_flake8', 'nb_bandit', 'nb_openai', 'nb_manuel')
        }),
    )
    
    # Inclure les problèmes
    inlines = [ProblemeInline]


@admin.register(Probleme)
class ProblemeAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour les problèmes
    """
    
    list_display = [
        'get_analyse_nom',
        'severite',
        'categorie',
        'source',
        'ligne',
        'message_court'
    ]
    
    list_filter = ['severite', 'categorie', 'source']
    
    search_fields = ['message', 'analyse__nom_fichier']
    
    def get_analyse_nom(self, obj):
        return obj.analyse.nom_fichier
    get_analyse_nom.short_description = "Fichier"
    
    def message_court(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_court.short_description = "Message"