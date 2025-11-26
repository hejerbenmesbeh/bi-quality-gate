"""
Script d'analyse pour GitHub Actions
====================================
Analyse les fichiers Python modifiés dans un commit/PR
et génère un rapport JSON pour GitHub Actions.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Ajouter le projet au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bi_quality_gate.settings')
import django
django.setup()

from core.services import QualityGateService


def get_modified_python_files():
    """
    Récupère la liste des fichiers Python modifiés
    """
    try:
        # Récupérer les fichiers modifiés depuis le dernier commit
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Filtrer uniquement les fichiers Python
        files = [
            f for f in result.stdout.strip().split('\n')
            if f.endswith('.py') and os.path.exists(f)
        ]
        
        return files
    except subprocess.CalledProcessError:
        print("⚠️ Impossible de récupérer les fichiers modifiés")
        return []


def analyze_file(filepath: str, service: QualityGateService):
    """
    Analyse un fichier avec le Quality Gate
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenu = f.read()
        
        # Analyser avec le service
        analyse = service.analyser_code(
            nom_fichier=filepath,
            outil='Python',
            contenu=contenu,
            description=f"Analyse automatique GitHub Actions"
        )
        
        return {
            'fichier': filepath,
            'score': analyse.score,
            'approuve': analyse.est_approuve,
            'critiques': analyse.nb_critiques,
            'warnings': analyse.nb_warnings,
            'infos': analyse.nb_infos,
            'flake8': analyse.nb_flake8,
            'bandit': analyse.nb_bandit,
            'openai': analyse.nb_openai
        }
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse de {filepath}: {e}")
        return None


def main():
    """
    Point d'entrée principal
    """
    print("🚀 Quality Gate - GitHub Actions Runner")
    print("=" * 60)
    
    # Récupérer les fichiers modifiés
    fichiers = get_modified_python_files()
    
    if not fichiers:
        print("ℹ️ Aucun fichier Python modifié")
        # Créer un rapport vide
        rapport = {
            'status': 'PASSED',
            'score': 100,
            'critiques': 0,
            'warnings': 0,
            'infos': 0,
            'flake8': 0,
            'bandit': 0,
            'openai': 0,
            'files': []
        }
    else:
        print(f"📁 {len(fichiers)} fichier(s) à analyser:")
        for f in fichiers:
            print(f"   - {f}")
        
        # Créer le service
        service = QualityGateService()
        
        # Analyser chaque fichier
        resultats = []
        for fichier in fichiers:
            print(f"\n🔍 Analyse de {fichier}...")
            resultat = analyze_file(fichier, service)
            if resultat:
                resultats.append(resultat)
                print(f"   Score: {resultat['score']}/100")
        
        # Calculer les statistiques globales
        if resultats:
            score_moyen = sum(r['score'] for r in resultats) // len(resultats)
            total_critiques = sum(r['critiques'] for r in resultats)
            total_warnings = sum(r['warnings'] for r in resultats)
            total_infos = sum(r['infos'] for r in resultats)
            
            rapport = {
                'status': 'PASSED' if total_critiques == 0 and score_moyen >= 70 else 'FAILED',
                'score': score_moyen,
                'critiques': total_critiques,
                'warnings': total_warnings,
                'infos': total_infos,
                'flake8': sum(r['flake8'] for r in resultats),
                'bandit': sum(r['bandit'] for r in resultats),
                'openai': sum(r['openai'] for r in resultats),
                'files': resultats
            }
        else:
            rapport = {
                'status': 'ERROR',
                'score': 0,
                'critiques': 0,
                'warnings': 0,
                'infos': 0,
                'flake8': 0,
                'bandit': 0,
                'openai': 0,
                'files': []
            }
    
    # Sauvegarder le rapport
    with open('quality_report.json', 'w') as f:
        json.dump(rapport, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTAT FINAL")
    print("=" * 60)
    print(f"Status: {rapport['status']}")
    print(f"Score: {rapport['score']}/100")
    print(f"❌ Critiques: {rapport['critiques']}")
    print(f"⚠️  Warnings: {rapport['warnings']}")
    print(f"ℹ️  Infos: {rapport['infos']}")
    print("=" * 60)
    
    # Retourner le code de sortie approprié
    if rapport['status'] == 'FAILED':
        print("❌ Quality Gate FAILED")
        sys.exit(1)
    else:
        print("✅ Quality Gate PASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()