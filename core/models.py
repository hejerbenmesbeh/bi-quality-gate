"""
Étudiant 1: Modèles de Base de Données
======================================
Ces modèles définissent la structure des données stockées.
Django va créer automatiquement les tables SQL correspondantes.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class OutilBI(models.TextChoices):
    """
    Les différents langages/outils supportés
    TextChoices = Enum Django qui se stocke comme texte en BDD
    """
    SQL = 'SQL', 'SQL'
    PYTHON = 'Python', 'Python'
    DAX = 'DAX', 'DAX (Power BI)'
    POWER_QUERY = 'PowerQuery', 'Power Query (M)'


class Severite(models.TextChoices):
    """Niveau de gravité d'un problème"""
    CRITIQUE = 'critique', 'Critique'
    WARNING = 'warning', 'Warning'
    INFO = 'info', 'Info'


class Categorie(models.TextChoices):
    """Type de problème détecté"""
    PERFORMANCE = 'performance', 'Performance'
    SECURITE = 'securite', 'Sécurité'
    QUALITE = 'qualite', 'Qualité des données'
    LISIBILITE = 'lisibilite', 'Lisibilité'
    STYLE = 'style', 'Style (PEP8)'
    COMPLEXITE = 'complexite', 'Complexité'


class SourceAnalyse(models.TextChoices):
    """D'où vient le problème détecté"""
    MANUEL = 'manuel', 'Règles manuelles'
    FLAKE8 = 'flake8', 'Flake8'
    BANDIT = 'bandit', 'Bandit'
    OPENAI = 'openai', 'OpenAI'


class AnalyseCode(models.Model):
    """
    Modèle principal: Une analyse de code
    
    Chaque fois qu'un utilisateur soumet du code, on crée une instance
    de ce modèle avec tous les résultats.
    """
    
    # Informations sur le code analysé
    nom_fichier = models.CharField(
        max_length=255,
        verbose_name="Nom du fichier",
        help_text="Ex: etl_ventes.py"
    )
    
    outil = models.CharField(
        max_length=20,
        choices=OutilBI.choices,
        default=OutilBI.PYTHON,
        verbose_name="Langage/Outil"
    )
    
    contenu_code = models.TextField(
        verbose_name="Code source",
        help_text="Le code à analyser"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Que fait ce code?"
    )
    
    # Résultats de l'analyse
    score = models.IntegerField(
        default=0,
        verbose_name="Score de qualité",
        help_text="Score de 0 à 100"
    )
    
    est_approuve = models.BooleanField(
        default=False,
        verbose_name="Approuvé pour production"
    )
    
    temps_analyse = models.FloatField(
        default=0.0,
        verbose_name="Temps d'analyse (secondes)"
    )
    
    # Statistiques par outil
    nb_problemes_total = models.IntegerField(default=0)
    nb_critiques = models.IntegerField(default=0)
    nb_warnings = models.IntegerField(default=0)
    nb_infos = models.IntegerField(default=0)
    nb_flake8 = models.IntegerField(default=0)
    nb_bandit = models.IntegerField(default=0)
    nb_openai = models.IntegerField(default=0)
    nb_manuel = models.IntegerField(default=0)
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'analyse"
    )
    
    auteur = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Analysé par"
    )
    
    class Meta:
        verbose_name = "Analyse de code"
        verbose_name_plural = "Analyses de code"
        ordering = ['-date_creation']  # Plus récent en premier
    
    def __str__(self):
        status = "✅" if self.est_approuve else "❌"
        return f"{status} {self.nom_fichier} - {self.score}/100"
    
    def get_score_color(self):
        """Retourne la couleur CSS selon le score"""
        if self.score >= 80:
            return "success"  # Vert
        elif self.score >= 60:
            return "warning"  # Orange
        return "danger"  # Rouge
    
    def get_status_badge(self):
        """Retourne le badge de statut"""
        if self.est_approuve:
            return '<span class="badge bg-success">APPROUVÉ</span>'
        return '<span class="badge bg-danger">REJETÉ</span>'


class Probleme(models.Model):
    """
    Un problème détecté dans le code
    
    Relation: Une analyse peut avoir plusieurs problèmes (OneToMany)
    """
    
    # Lien vers l'analyse parente
    analyse = models.ForeignKey(
        AnalyseCode,
        on_delete=models.CASCADE,  # Si on supprime l'analyse, on supprime les problèmes
        related_name='problemes',  # analyse.problemes.all()
        verbose_name="Analyse"
    )
    
    # Détails du problème
    severite = models.CharField(
        max_length=20,
        choices=Severite.choices,
        default=Severite.INFO
    )
    
    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        default=Categorie.LISIBILITE
    )
    
    source = models.CharField(
        max_length=20,
        choices=SourceAnalyse.choices,
        default=SourceAnalyse.MANUEL
    )
    
    message = models.TextField(
        verbose_name="Message d'erreur"
    )
    
    suggestion = models.TextField(
        blank=True,
        verbose_name="Suggestion de correction"
    )
    
    ligne = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Numéro de ligne"
    )
    
    colonne = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Numéro de colonne"
    )
    
    code_erreur = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Code erreur",
        help_text="Ex: E501, B105"
    )
    
    class Meta:
        verbose_name = "Problème"
        verbose_name_plural = "Problèmes"
        ordering = ['severite', 'ligne']
    
    def __str__(self):
        return f"[{self.severite}] {self.message[:50]}..."
    
    def get_severite_icon(self):
        """Retourne l'icône selon la sévérité"""
        icons = {
            'critique': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        return icons.get(self.severite, '•')
    
    def get_severite_color(self):
        """Retourne la classe CSS selon la sévérité"""
        colors = {
            'critique': 'danger',
            'warning': 'warning',
            'info': 'info'
        }
        return colors.get(self.severite, 'secondary')
    
    def get_source_badge_color(self):
        """Retourne la couleur du badge selon la source"""
        colors = {
            'flake8': 'purple',
            'bandit': 'pink',
            'openai': 'success',
            'manuel': 'secondary'
        }
        return colors.get(self.source, 'secondary')