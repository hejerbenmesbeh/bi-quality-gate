"""
Étudiant 2: Analyseur Statique (Règles Manuelles)
=================================================
Règles personnalisées pour SQL, DAX, et compléments Python.
"""

from typing import List, Dict, Any
import re


class AnalyseurStatique:
    """
    Analyseur avec des règles manuelles pour tous les langages BI
    """
    
    def analyser(self, contenu: str, outil: str) -> List[Dict[str, Any]]:
        """
        Lance l'analyse selon le type d'outil
        
        Args:
            contenu: Le code source
            outil: Le langage (SQL, Python, DAX, PowerQuery)
        
        Returns:
            Liste de dictionnaires représentant les problèmes
        """
        if outil == 'SQL':
            return self._analyser_sql(contenu)
        elif outil == 'Python':
            return self._analyser_python(contenu)
        elif outil == 'DAX':
            return self._analyser_dax(contenu)
        elif outil == 'PowerQuery':
            return self._analyser_power_query(contenu)
        
        return []
    
    def _analyser_sql(self, contenu: str) -> List[Dict[str, Any]]:
        """Règles pour le SQL"""
        problemes = []
        contenu_upper = contenu.upper()
        lignes = contenu.split('\n')
        
        # Règle 1: SELECT *
        if 'SELECT *' in contenu_upper:
            for i, ligne in enumerate(lignes):
                if 'SELECT *' in ligne.upper():
                    problemes.append({
                        'severite': 'warning',
                        'categorie': 'performance',
                        'source': 'manuel',
                        'message': 'SELECT * détecté - charge toutes les colonnes inutilement',
                        'suggestion': 'Listez uniquement les colonnes nécessaires',
                        'ligne': i + 1,
                        'code_erreur': 'SQL001'
                    })
                    break
        
        # Règle 2: JOIN sans ON
        if 'JOIN' in contenu_upper and 'ON' not in contenu_upper:
            problemes.append({
                'severite': 'critique',
                'categorie': 'qualite',
                'source': 'manuel',
                'message': 'JOIN sans clause ON - produit un produit cartésien',
                'suggestion': 'Ajoutez une condition ON: JOIN table ON t1.id = t2.id',
                'code_erreur': 'SQL002'
            })
        
        # Règle 3: Données sensibles
        donnees_sensibles = ['PASSWORD', 'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD', 'SALAIRE']
        for donnee in donnees_sensibles:
            if donnee in contenu_upper:
                problemes.append({
                    'severite': 'critique',
                    'categorie': 'securite',
                    'source': 'manuel',
                    'message': f'Donnée sensible détectée: {donnee}',
                    'suggestion': 'Masquez avec HASH() ou excluez du dashboard',
                    'code_erreur': 'SQL003'
                })
                break
        
        # Règle 4: Pas de WHERE avec JOIN
        if 'JOIN' in contenu_upper and 'WHERE' not in contenu_upper:
            problemes.append({
                'severite': 'warning',
                'categorie': 'performance',
                'source': 'manuel',
                'message': 'JOIN sans WHERE - risque de charger trop de données',
               'suggestion': 'Ajoutez des filtres WHERE pour limiter les résultats',
                'code_erreur': 'SQL004'
            })
        
        # Règle 5: Pas d'alias (AS)
        if 'SELECT' in contenu_upper and ' AS ' not in contenu_upper:
            problemes.append({
                'severite': 'info',
                'categorie': 'lisibilite',
                'source': 'manuel',
                'message': 'Aucun alias (AS) utilisé - code moins lisible',
                'suggestion': 'Utilisez des alias: SELECT COUNT(*) AS total_ventes',
                'code_erreur': 'SQL005'
            })
        
        # Règle 6: Date en dur
        annees = ['2023', '2024', '2025']
        for annee in annees:
            if annee in contenu and 'GETDATE' not in contenu_upper and 'CURRENT' not in contenu_upper:
                problemes.append({
                    'severite': 'warning',
                    'categorie': 'qualite',
                    'source': 'manuel',
                    'message': f'Année {annee} codée en dur',
                    'suggestion': 'Utilisez GETDATE() ou CURRENT_DATE pour des dates dynamiques',
                    'code_erreur': 'SQL006'
                })
                break
        
        # Règle 7: Pas de LIMIT
        if 'SELECT' in contenu_upper and 'LIMIT' not in contenu_upper and 'TOP' not in contenu_upper:
            if 'WHERE' not in contenu_upper:
                problemes.append({
                    'severite': 'warning',
                    'categorie': 'performance',
                    'source': 'manuel',
                    'message': 'SELECT sans LIMIT ni WHERE - risque de surcharge',
                    'suggestion': 'Ajoutez LIMIT ou TOP pour limiter les résultats',
                    'code_erreur': 'SQL007'
                })
        
        return problemes
    
    def _analyser_python(self, contenu: str) -> List[Dict[str, Any]]:
        """Règles complémentaires pour Python (en plus de Flake8/Bandit)"""
        problemes = []
        lignes = contenu.split('\n')
        
        # Règle 1: Import *
        for i, ligne in enumerate(lignes):
            if 'from' in ligne and 'import *' in ligne:
                problemes.append({
                    'severite': 'warning',
                    'categorie': 'lisibilite',
                    'source': 'manuel',
                    'message': 'Import * détecté - importe tout le module',
                    'suggestion': 'Importez uniquement ce dont vous avez besoin',
                    'ligne': i + 1,
                    'code_erreur': 'PY001'
                })
        
        # Règle 2: Pas de docstring
        if 'def ' in contenu and '"""' not in contenu and "'''" not in contenu:
            problemes.append({
                'severite': 'info',
                'categorie': 'lisibilite',
                'source': 'manuel',
                'message': 'Fonctions sans docstrings',
                'suggestion': 'Ajoutez des docstrings pour documenter vos fonctions',
                'code_erreur': 'PY002'
            })
        
        # Règle 3: print() en production
        if 'print(' in contenu:
            count = contenu.count('print(')
            if count > 3:
                problemes.append({
                    'severite': 'info',
                    'categorie': 'qualite',
                    'source': 'manuel',
                    'message': f'{count} print() détectés - utilisez logging en production',
                    'suggestion': 'Remplacez print() par logging.info()',
                    'code_erreur': 'PY003'
                })
        
        # Règle 4: Pas de gestion d'erreur avec fichiers
        if ('open(' in contenu or 'read_csv' in contenu or 'read_excel' in contenu):
            if 'try' not in contenu and 'except' not in contenu:
                problemes.append({
                    'severite': 'warning',
                    'categorie': 'qualite',
                    'source': 'manuel',
                    'message': 'Lecture de fichier sans gestion d\'erreur',
                    'suggestion': 'Entourez avec try/except pour gérer les erreurs',
                    'code_erreur': 'PY004'
                })
        
        return problemes
    
    def _analyser_dax(self, contenu: str) -> List[Dict[str, Any]]:
        """Règles pour DAX (Power BI)"""
        problemes = []
        contenu_upper = contenu.upper()
        
        # Règle 1: CALCULATE sans contexte clair
        if 'CALCULATE' in contenu_upper:
            if 'FILTER' not in contenu_upper and 'ALL' not in contenu_upper:
                problemes.append({
                    'severite': 'info',
                    'categorie': 'lisibilite',
                    'source': 'manuel',
                    'message': 'CALCULATE sans FILTER explicite',
                    'suggestion': 'Vérifiez que le contexte de filtre est bien défini',
                    'code_erreur': 'DAX001'
                })
        
        # Règle 2: Utilisation de SUMX sur grande table
        if 'SUMX' in contenu_upper or 'AVERAGEX' in contenu_upper:
            problemes.append({
                'severite': 'warning',
                'categorie': 'performance',
                'source': 'manuel',
                'message': 'Fonction itérative (SUMX/AVERAGEX) détectée',
                'suggestion': 'Vérifiez les performances sur grandes tables, préférez SUM si possible',
                'code_erreur': 'DAX002'
            })
        
        # Règle 3: Pas de commentaires
        if '--' not in contenu and '//' not in contenu:
            if len(contenu) > 200:
                problemes.append({
                    'severite': 'info',
                    'categorie': 'lisibilite',
                    'source': 'manuel',
                    'message': 'Mesure DAX complexe sans commentaires',
                    'suggestion': 'Ajoutez des commentaires pour expliquer la logique',
                    'code_erreur': 'DAX003'
                })
        
        return problemes
    
    def _analyser_power_query(self, contenu: str) -> List[Dict[str, Any]]:
        """Règles pour Power Query (M)"""
        problemes = []
        
        # Règle 1: Pas de let...in
        if 'let' not in contenu.lower() or 'in' not in contenu.lower():
            problemes.append({
                'severite': 'warning',
                'categorie': 'lisibilite',
                'source': 'manuel',
                'message': 'Structure let...in non détectée',
                'suggestion': 'Utilisez let...in pour structurer votre code M',
                'code_erreur': 'PQ001'
            })
        
        # Règle 2: Chemins en dur
        if 'C:\\' in contenu or 'D:\\' in contenu or '/Users/' in contenu:
            problemes.append({
                'severite': 'critique',
                'categorie': 'qualite',
                'source': 'manuel',
                'message': 'Chemin de fichier codé en dur détecté',
                'suggestion': 'Utilisez des paramètres Power Query pour les chemins',
                'code_erreur': 'PQ002'
            })
        
        return problemes