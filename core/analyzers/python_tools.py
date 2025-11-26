"""
Étudiant 2: Analyseur Python avec Flake8 et Bandit
==================================================
Utilise les outils professionnels pour analyser le code Python.
"""

import os
import json
import subprocess
import tempfile
import shutil
from typing import List, Dict, Any, Tuple

from django.conf import settings


class AnalyseurPythonTools:
    """
    Utilise Flake8 et Bandit pour analyser le code Python
    """
    
    def __init__(self):
        """Vérifie la disponibilité des outils"""
        self.flake8_disponible = shutil.which('flake8') is not None
        self.bandit_disponible = shutil.which('bandit') is not None
        
        # Récupérer la configuration depuis settings.py
        self.config = settings.QUALITY_GATE_CONFIG
    
    def analyser(self, contenu: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Analyse le code Python avec Flake8 et Bandit
        
        Args:
            contenu: Le code Python à analyser
        
        Returns:
            Tuple (problemes_flake8, problemes_bandit)
        """
        problemes_flake8 = []
        problemes_bandit = []
        
        # Créer un fichier temporaire
        fichier_temp = self._creer_fichier_temp(contenu)
        
        try:
            # Exécuter Flake8
            if self.flake8_disponible:
                problemes_flake8 = self._executer_flake8(fichier_temp)
            
            # Exécuter Bandit
            if self.bandit_disponible:
                problemes_bandit = self._executer_bandit(fichier_temp)
        
        finally:
            # Toujours supprimer le fichier temporaire
            self._supprimer_fichier_temp(fichier_temp)
        
        return problemes_flake8, problemes_bandit
    
    def _creer_fichier_temp(self, contenu: str) -> str:
        """Crée un fichier temporaire avec le code"""
        fd, chemin = tempfile.mkstemp(suffix='.py', prefix='qg_')
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(contenu)
        
        return chemin
    
    def _supprimer_fichier_temp(self, chemin: str):
        """Supprime le fichier temporaire"""
        try:
            if os.path.exists(chemin):
                os.remove(chemin)
        except Exception:
            pass
    
    def _executer_flake8(self, chemin_fichier: str) -> List[Dict[str, Any]]:
        """
        Exécute Flake8 et parse les résultats
        """
        problemes = []
        
        try:
            # Construire la commande
            max_length = self.config.get('FLAKE8_MAX_LINE_LENGTH', 120)
            ignore = ','.join(self.config.get('FLAKE8_IGNORE', []))
            
            commande = [
                'flake8',
                f'--max-line-length={max_length}',
                '--format=%(row)d:%(col)d:%(code)s:%(text)s',
                chemin_fichier
            ]
            
            if ignore:
                commande.insert(2, f'--ignore={ignore}')
            
            # Exécuter
            resultat = subprocess.run(
                commande,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parser la sortie
            for ligne in resultat.stdout.strip().split('\n'):
                if ligne:
                    probleme = self._parser_flake8(ligne)
                    if probleme:
                        problemes.append(probleme)
        
        except subprocess.TimeoutExpired:
            problemes.append({
                'severite': 'warning',
                'categorie': 'performance',
                'source': 'flake8',
                'message': 'Timeout Flake8 - code trop long ou complexe',
                'code_erreur': 'TIMEOUT'
            })
        except Exception as e:
            print(f"Erreur Flake8: {e}")
        
        return problemes
    
    def _parser_flake8(self, ligne: str) -> Dict[str, Any]:
        """Parse une ligne de sortie Flake8"""
        try:
            parties = ligne.split(':')
            if len(parties) >= 4:
                num_ligne = int(parties[0])
                colonne = int(parties[1])
                code = parties[2]
                message = ':'.join(parties[3:]).strip()
                
                severite, categorie = self._classifier_flake8(code)
                
                return {
                    'severite': severite,
                    'categorie': categorie,
                    'source': 'flake8',
                    'message': f'[{code}] {message}',
                    'suggestion': self._suggestion_flake8(code),
                    'ligne': num_ligne,
                    'colonne': colonne,
                    'code_erreur': code
                }
        except Exception:
            pass
        
        return None
    
    def _classifier_flake8(self, code: str) -> Tuple[str, str]:
        """Détermine sévérité et catégorie selon le code Flake8"""
        type_erreur = code[0] if code else 'E'
        
        if type_erreur == 'F':
            if code in ['F401', 'F841']:
                return 'warning', 'style'
            return 'critique', 'qualite'
        elif type_erreur == 'E':
            if code.startswith('E5'):
                return 'info', 'style'
            return 'warning', 'style'
        elif type_erreur == 'W':
            return 'info', 'style'
        elif type_erreur == 'C':
            return 'warning', 'complexite'
        
        return 'info', 'style'
    
    def _suggestion_flake8(self, code: str) -> str:
        """Retourne une suggestion pour l'erreur Flake8"""
        suggestions = {
            'E501': 'Raccourcissez la ligne (max 120 caractères)',
            'E302': 'Ajoutez 2 lignes vides avant la fonction',
            'E303': 'Supprimez les lignes vides en trop',
            'E401': 'Un import par ligne',
            'E711': "Utilisez 'is None' au lieu de '== None'",
            'F401': 'Supprimez l\'import non utilisé',
            'F841': 'Supprimez la variable non utilisée',
            'W291': 'Supprimez les espaces en fin de ligne',
            'W292': 'Ajoutez une ligne vide à la fin du fichier',
        }
        return suggestions.get(code, 'Consultez la documentation PEP8')
    
    def _executer_bandit(self, chemin_fichier: str) -> List[Dict[str, Any]]:
        """
        Exécute Bandit et parse les résultats JSON
        """
        problemes = []
        
        try:
            severity = self.config.get('BANDIT_SEVERITY', 'LOW').lower()
            
            commande = [
                'bandit',
                '-f', 'json',
                f'--severity-level={severity}',
                chemin_fichier
            ]
            
            resultat = subprocess.run(
                commande,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if resultat.stdout:
                data = json.loads(resultat.stdout)
                
                for issue in data.get('results', []):
                    probleme = self._parser_bandit(issue)
                    if probleme:
                        problemes.append(probleme)
        
        except subprocess.TimeoutExpired:
            problemes.append({
                'severite': 'warning',
                'categorie': 'securite',
                'source': 'bandit',
                'message': 'Timeout Bandit - code trop long',
                'code_erreur': 'TIMEOUT'
            })
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Erreur Bandit: {e}")
        
        return problemes
    
    def _parser_bandit(self, issue: dict) -> Dict[str, Any]:
        """Parse un résultat Bandit"""
        try:
            severity = issue.get('severity', 'LOW').upper()
            
            if severity == 'HIGH':
                severite = 'critique'
            elif severity == 'MEDIUM':
                severite = 'warning'
            else:
                severite = 'info'
            
            code = issue.get('test_id', 'B000')
            
            return {
                'severite': severite,
                'categorie': 'securite',
                'source': 'bandit',
                'message': f"[{code}] {issue.get('issue_text', 'Problème de sécurité')}",
                'suggestion': self._suggestion_bandit(code),
                'ligne': issue.get('line_number'),
                'code_erreur': code
            }
        except Exception:
            return None
    
    def _suggestion_bandit(self, code: str) -> str:
        """Retourne une suggestion pour l'erreur Bandit"""
        suggestions = {
            'B105': 'Utilisez os.getenv() pour les mots de passe',
            'B106': 'Ne stockez jamais les mots de passe dans le code',
            'B107': 'Utilisez un gestionnaire de secrets',
            'B301': 'Pickle est dangereux, utilisez JSON',
            'B303': 'MD5/SHA1 obsolètes, utilisez SHA256',
            'B307': 'eval() dangereux, utilisez ast.literal_eval()',
            'B602': 'Évitez subprocess avec shell=True',
            'B608': 'Injection SQL possible, utilisez des requêtes paramétrées',
        }
        return suggestions.get(code, 'Consultez la documentation Bandit')
    
    def get_status(self) -> Dict[str, bool]:
        """Retourne le statut des outils"""
        return {
            'flake8': self.flake8_disponible,
            'bandit': self.bandit_disponible
        }