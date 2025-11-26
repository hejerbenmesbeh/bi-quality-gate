"""
Étudiant 4: Service d'Analyse (Logique Métier)
==============================================
Orchestre tous les analyseurs et crée les résultats.
"""

import time
from typing import Dict, Any, List

from django.conf import settings

from .models import AnalyseCode, Probleme
from .analyzers import AnalyseurStatique, AnalyseurPythonTools, AnalyseurIA
from django.db import models


class QualityGateService:
    """
    Service principal qui coordonne l'analyse de code
    
    C'est le "chef d'orchestre" qui:
    1. Reçoit le code à analyser
    2. Appelle chaque analyseur
    3. Agrège les résultats
    4. Sauvegarde en base de données
    """
    
    def __init__(self):
        """Initialise tous les analyseurs"""
        self.analyseur_statique = AnalyseurStatique()
        self.analyseur_python = AnalyseurPythonTools()
        self.analyseur_ia = AnalyseurIA()
        self.config = settings.QUALITY_GATE_CONFIG
    
    def analyser_code(
        self,
        nom_fichier: str,
        outil: str,
        contenu: str,
        description: str = "",
        auteur=None,
        options: Dict[str, bool] = None
    ) -> AnalyseCode:
        """
        Lance une analyse complète et sauvegarde les résultats
        
        Args:
            nom_fichier: Nom du fichier
            outil: Langage (SQL, Python, etc.)
            contenu: Code source
            description: Description du code
            auteur: Utilisateur Django (optionnel)
            options: Options d'analyse (flake8, bandit, ia)
        
        Returns:
            Instance AnalyseCode avec tous les résultats
        """
        debut = time.time()
        tous_les_problemes: List[Dict] = []
        
        # Options par défaut
        if options is None:
            options = {
                'utiliser_flake8': True,
                'utiliser_bandit': True,
                'utiliser_ia': True
            }
        
        # ===== ÉTAPE 1: Analyse statique (règles manuelles) =====
        problemes_manuels = self.analyseur_statique.analyser(contenu, outil)
        tous_les_problemes.extend(problemes_manuels)
        
        # ===== ÉTAPE 2: Flake8 + Bandit (Python uniquement) =====
        problemes_flake8 = []
        problemes_bandit = []
        
        if outil == 'Python':
            if options.get('utiliser_flake8', True):
                flake8, _ = self.analyseur_python.analyser(contenu)
                problemes_flake8 = flake8
                tous_les_problemes.extend(flake8)
            if options.get('utiliser_bandit', True):
                _, bandit = self.analyseur_python.analyser(contenu)
                problemes_bandit = bandit
                tous_les_problemes.extend(bandit)
        
        # ===== ÉTAPE 3: Analyse IA =====
        problemes_ia = []
        if options.get('utiliser_ia', True):
            problemes_ia = self.analyseur_ia.analyser(contenu, outil, description)
            tous_les_problemes.extend(problemes_ia)
        
        # ===== ÉTAPE 4: Calcul du score =====
        score = self._calculer_score(tous_les_problemes)
        
        # ===== ÉTAPE 5: Décision finale =====
        nb_critiques = sum(1 for p in tous_les_problemes if p.get('severite') == 'critique')
        seuil = self.config.get('SCORE_MINIMUM', 70)
        est_approuve = nb_critiques == 0 and score >= seuil
        
        temps_analyse = time.time() - debut
        
        # ===== ÉTAPE 6: Sauvegarde en base de données =====
        analyse = AnalyseCode.objects.create(
            nom_fichier=nom_fichier,
            outil=outil,
            contenu_code=contenu,
            description=description,
            score=score,
            est_approuve=est_approuve,
            temps_analyse=temps_analyse,
            nb_problemes_total=len(tous_les_problemes),
            nb_critiques=nb_critiques,
            nb_warnings=sum(1 for p in tous_les_problemes if p.get('severite') == 'warning'),
            nb_infos=sum(1 for p in tous_les_problemes if p.get('severite') == 'info'),
            nb_flake8=len(problemes_flake8),
            nb_bandit=len(problemes_bandit),
            nb_openai=len(problemes_ia),
            nb_manuel=len(problemes_manuels),
            auteur=auteur
        )
        
        # Sauvegarder chaque problème
        for prob in tous_les_problemes:
            Probleme.objects.create(
                analyse=analyse,
                severite=prob.get('severite', 'info'),
                categorie=prob.get('categorie', 'lisibilite'),
                source=prob.get('source', 'manuel'),
                message=prob.get('message', ''),
                suggestion=prob.get('suggestion', ''),
                ligne=prob.get('ligne'),
                colonne=prob.get('colonne'),
                code_erreur=prob.get('code_erreur', '')
            )
        
        return analyse
    
    def _calculer_score(self, problemes: List[Dict]) -> int:
        """
        Calcule le score de qualité (0-100)
        
        Pénalités:
        - Critique: -30 points
        - Warning: -10 points
        - Info: -2 points
        """
        score = 100
        
        penalite_critique = self.config.get('PENALITE_CRITIQUE', 30)
        penalite_warning = self.config.get('PENALITE_WARNING', 10)
        penalite_info = self.config.get('PENALITE_INFO', 2)
        
        for p in problemes:
            severite = p.get('severite', 'info')
            if severite == 'critique':
                score -= penalite_critique
            elif severite == 'warning':
                score -= penalite_warning
            else:
                score -= penalite_info
        
        return max(0, score)
    
    def get_statistiques_globales(self) -> Dict[str, Any]:
        """
        Retourne des statistiques globales sur toutes les analyses
        """
        from django.db.models import Avg, Count, Sum
        
        total = AnalyseCode.objects.count()
        
        if total == 0:
            return {
                'total_analyses': 0,
                'score_moyen': 0,
                'taux_approbation': 0,
                'par_outil': {},
                'problemes_frequents': []
            }
        
        stats = AnalyseCode.objects.aggregate(
            score_moyen=Avg('score'),
            total_approuve=Count('id', filter=models.Q(est_approuve=True)),
            total_problemes=Sum('nb_problemes_total')
        )
        
        # Stats par outil
        par_outil = AnalyseCode.objects.values('outil').annotate(
            count=Count('id'),
            score_moyen=Avg('score')
        )
        
        # Problèmes les plus fréquents
        from django.db.models import Count
        problemes_frequents = Probleme.objects.values('code_erreur', 'message').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return {
            'total_analyses': total,
            'score_moyen': round(stats['score_moyen'] or 0, 1),
            'taux_approbation': round((stats['total_approuve'] / total) * 100, 1),
            'total_problemes': stats['total_problemes'] or 0,
            'par_outil': {item['outil']: item for item in par_outil},
            'problemes_frequents': list(problemes_frequents)
        }
    
    def get_outils_status(self) -> Dict[str, bool]:
        """Retourne le statut de disponibilité des outils"""
        python_status = self.analyseur_python.get_status()
        
        return {
            'flake8': python_status.get('flake8', False),
            'bandit': python_status.get('bandit', False),
            'openai': self.analyseur_ia.est_actif(),
            'regles_manuelles': True
        }