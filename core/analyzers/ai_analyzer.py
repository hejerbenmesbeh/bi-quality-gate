"""
Étudiant 3: Analyseur IA avec OpenAI
====================================
Utilise ChatGPT pour une analyse intelligente du code.
"""

import json
from typing import List, Dict, Any, Optional

from django.conf import settings

try:
    from openai import OpenAI
    OPENAI_DISPONIBLE = True
except ImportError:
    OPENAI_DISPONIBLE = False


class AnalyseurIA:
    """
    Analyseur utilisant l'API OpenAI (ChatGPT)
    
    Analyse la LOGIQUE MÉTIER du code, pas juste la syntaxe.
    """
    
    def __init__(self):
        """Initialise la connexion OpenAI"""
        self.client = None
        self.actif = False
        
        config = settings.QUALITY_GATE_CONFIG
        api_key = config.get('OPENAI_API_KEY', '')
        
        if OPENAI_DISPONIBLE and api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                self.actif = True
                self.model = config.get('OPENAI_MODEL', 'gpt-3.5-turbo')
            except Exception as e:
                print(f"Erreur initialisation OpenAI: {e}")
    
    def analyser(self, contenu: str, outil: str, description: str = "") -> List[Dict[str, Any]]:
        """
        Analyse le code avec l'IA
        
        Args:
            contenu: Le code source
            outil: Le langage (SQL, Python, etc.)
            description: Description de ce que fait le code
        
        Returns:
            Liste des problèmes détectés
        """
        if not self.actif:
            return self._simulation_analyse(contenu, outil)
        
        return self._analyse_openai(contenu, outil, description)
    
    def _analyse_openai(self, contenu: str, outil: str, description: str) -> List[Dict[str, Any]]:
        """Appelle réellement l'API OpenAI"""
        
        prompt = f"""Tu es un expert en Business Intelligence et qualité de code.
Analyse le code {outil} suivant et identifie les problèmes potentiels.

DESCRIPTION DU CODE:
{description if description else "Non fournie"}

CODE À ANALYSER:
```{outil.lower()}
{contenu[:3000]}
```

Réponds UNIQUEMENT en JSON valide avec ce format exact:
{{
    "problemes": [
        {{
            "severite": "critique" ou "warning" ou "info",
            "categorie": "performance" ou "securite" ou "qualite" ou "lisibilite",
            "message": "Description claire du problème",
            "suggestion": "Comment corriger",
            "ligne": null
        }}
    ]
}}

Concentre-toi sur:
1. La logique métier (le code fait-il ce qu'il devrait?)
2. Les bonnes pratiques BI et data engineering
3. La performance pour les dashboards
4. La maintenabilité du code

Maximum 5 problèmes les plus importants.
Si le code est bon, retourne une liste vide.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un expert BI. Réponds toujours en JSON valide sans markdown."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            reponse_texte = response.choices[0].message.content.strip()
            
            # Nettoyer le JSON (enlever ```json si présent)
            if reponse_texte.startswith('```'):
                lignes = reponse_texte.split('\n')
                reponse_texte = '\n'.join(lignes[1:-1])
            
            data = json.loads(reponse_texte)
            
            problemes = []
            for p in data.get('problemes', []):
                problemes.append({
                    'severite': self._normaliser_severite(p.get('severite', 'info')),
                    'categorie': self._normaliser_categorie(p.get('categorie', 'lisibilite')),
                    'source': 'openai',
                    'message': f"🤖 {p.get('message', 'Problème détecté')}",
                    'suggestion': p.get('suggestion', ''),
                    'ligne': p.get('ligne'),
                    'code_erreur': 'AI'
                })
            
            return problemes
        
        except json.JSONDecodeError as e:
            print(f"Erreur parsing JSON OpenAI: {e}")
            return []
        except Exception as e:
            print(f"Erreur API OpenAI: {e}")
            return []
    
    def _simulation_analyse(self, contenu: str, outil: str) -> List[Dict[str, Any]]:
        """
        Mode simulation quand l'API n'est pas disponible
        Utile pour les tests sans consommer de crédits
        """
        problemes = []
        contenu_upper = contenu.upper()
        
        # Simulation 1: Agrégation sans GROUP BY
        agregations = ['SUM(', 'COUNT(', 'AVG(', 'MAX(', 'MIN(']
        if any(agg in contenu_upper for agg in agregations):
            if 'GROUP BY' not in contenu_upper and outil == 'SQL':
                problemes.append({
                    'severite': 'warning',
                    'categorie': 'qualite',
                    'source': 'openai',
                    'message': '🤖 [Simulé] Fonction d\'agrégation sans GROUP BY explicite',
                    'suggestion': 'Vérifiez si un GROUP BY est nécessaire',
                    'code_erreur': 'AI-SIM'
                })
        
        # Simulation 2: Code long sans commentaires
        lignes = contenu.split('\n')
        lignes_code = [l for l in lignes if l.strip() and not l.strip().startswith(('#', '--', '//'))]
        
        if len(lignes_code) > 20:
            nb_commentaires = sum(1 for l in lignes if any(c in l for c in ['#', '--', '//']))
            if nb_commentaires < 3:
                problemes.append({
                    'severite': 'info',
                    'categorie': 'lisibilite',
                    'source': 'openai',
                    'message': '🤖 [Simulé] Code complexe avec peu de commentaires',
                    'suggestion': 'Ajoutez des commentaires pour expliquer la logique métier',
                    'code_erreur': 'AI-SIM'
                })
        
        # Simulation 3: Requête sans optimisation
        if outil == 'SQL' and 'SELECT' in contenu_upper:
            if 'INDEX' not in contenu_upper and 'ORDER BY' in contenu_upper:
                if 'LIMIT' not in contenu_upper and 'TOP' not in contenu_upper:
                    problemes.append({
                        'severite': 'warning',
                        'categorie': 'performance',
                        'source': 'openai',
                        'message': '🤖 [Simulé] ORDER BY sans LIMIT peut être lent sur grandes tables',
                        'suggestion': 'Ajoutez un LIMIT ou vérifiez les index',
                        'code_erreur': 'AI-SIM'
                    })
        
        return problemes
    
    def _normaliser_severite(self, severite: str) -> str:
        """Normalise la sévérité"""
        mapping = {
            'critical': 'critique',
            'critique': 'critique',
            'error': 'critique',
            'warning': 'warning',
            'warn': 'warning',
            'info': 'info',
            'information': 'info'
        }
        return mapping.get(severite.lower(), 'info')
    
    def _normaliser_categorie(self, categorie: str) -> str:
        """Normalise la catégorie"""
        mapping = {
            'performance': 'performance',
            'perf': 'performance',
            'security': 'securite',
            'securite': 'securite',
            'quality': 'qualite',
            'qualite': 'qualite',
            'data_quality': 'qualite',
            'readability': 'lisibilite',
            'lisibilite': 'lisibilite',
            'style': 'style'
        }
        return mapping.get(categorie.lower(), 'lisibilite')
    
    def est_actif(self) -> bool:
        """Retourne True si l'API est configurée"""
        return self.actif