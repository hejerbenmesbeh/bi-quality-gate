"""
Étudiant 4: Vues Django
=======================
Les vues gèrent les requêtes HTTP et retournent les réponses.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator
import json

from .models import AnalyseCode, Probleme
from .forms import AnalyseCodeForm, UploadFileForm
from .services import QualityGateService


def home(request):
    """
    Page d'accueil avec statistiques
    """
    service = QualityGateService()
    
    # Récupérer les statistiques
    stats = service.get_statistiques_globales()
    outils_status = service.get_outils_status()
    
    # Dernières analyses
    dernieres_analyses = AnalyseCode.objects.all()[:5]
    
    context = {
        'stats': stats,
        'outils_status': outils_status,
        'dernieres_analyses': dernieres_analyses,
    }
    
    return render(request, 'core/home.html', context)


def analyser(request):
    """
    Page pour soumettre du code à analyser
    """
    if request.method == 'POST':
        form = AnalyseCodeForm(request.POST)
        
        if form.is_valid():
            # Récupérer les données du formulaire
            nom_fichier = form.cleaned_data['nom_fichier']
            outil = form.cleaned_data['outil']
            contenu = form.cleaned_data['contenu_code']
            description = form.cleaned_data['description']
            
            # Options d'analyse
            options = {
                'utiliser_flake8': form.cleaned_data.get('utiliser_flake8', True),
                'utiliser_bandit': form.cleaned_data.get('utiliser_bandit', True),
                'utiliser_ia': form.cleaned_data.get('utiliser_ia', True),
            }
            
            # Lancer l'analyse
            service = QualityGateService()
            
            try:
                # Récupérer l'utilisateur si connecté
                auteur = request.user if request.user.is_authenticated else None
                
                analyse = service.analyser_code(
                    nom_fichier=nom_fichier,
                    outil=outil,
                    contenu=contenu,
                    description=description,
                    auteur=auteur,
                    options=options
                )
                
                # Message de succès
                if analyse.est_approuve:
                    messages.success(
                        request,
                        f"✅ Analyse terminée! Score: {analyse.score}/100 - APPROUVÉ"
                    )
                else:
                    messages.warning(
                        request,
                        f"⚠️ Analyse terminée! Score: {analyse.score}/100 - REJETÉ"
                    )
                
                # Rediriger vers les résultats
                return redirect('core:resultat', pk=analyse.pk)
            
            except Exception as e:
                messages.error(request, f"Erreur lors de l'analyse: {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire")
    else:
        form = AnalyseCodeForm()
    
    # Statut des outils
    service = QualityGateService()
    outils_status = service.get_outils_status()
    
    context = {
        'form': form,
        'outils_status': outils_status,
    }
    
    return render(request, 'core/analyze.html', context)


def resultat(request, pk):
    """
    Page de résultat d'une analyse
    """
    analyse = get_object_or_404(AnalyseCode, pk=pk)
    
    # Récupérer les problèmes groupés par source
    problemes_par_source = {
        'flake8': analyse.problemes.filter(source='flake8'),
        'bandit': analyse.problemes.filter(source='bandit'),
        'openai': analyse.problemes.filter(source='openai'),
        'manuel': analyse.problemes.filter(source='manuel'),
    }
    
    # Récupérer les problèmes par sévérité
    problemes_par_severite = {
        'critique': analyse.problemes.filter(severite='critique'),
        'warning': analyse.problemes.filter(severite='warning'),
        'info': analyse.problemes.filter(severite='info'),
    }
    
    context = {
        'analyse': analyse,
        'problemes': analyse.problemes.all(),
        'problemes_par_source': problemes_par_source,
        'problemes_par_severite': problemes_par_severite,
    }
    
    return render(request, 'core/result.html', context)


def historique(request):
    """
    Page d'historique de toutes les analyses
    """
    analyses_list = AnalyseCode.objects.all()
    
    # Filtres
    outil_filter = request.GET.get('outil', '')
    status_filter = request.GET.get('status', '')
    
    if outil_filter:
        analyses_list = analyses_list.filter(outil=outil_filter)
    
    if status_filter == 'approuve':
        analyses_list = analyses_list.filter(est_approuve=True)
    elif status_filter == 'rejete':
        analyses_list = analyses_list.filter(est_approuve=False)
    
    # Pagination
    paginator = Paginator(analyses_list, 10)
    page_number = request.GET.get('page')
    analyses = paginator.get_page(page_number)
    
    context = {
        'analyses': analyses,
        'outil_filter': outil_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'core/history.html', context)


def detail_analyse(request, pk):
    """
    Page de détail complet d'une analyse
    """
    analyse = get_object_or_404(AnalyseCode, pk=pk)
    
    context = {
        'analyse': analyse,
        'problemes': analyse.problemes.all().order_by('severite', 'ligne'),
    }
    
    return render(request, 'core/detail.html', context)


def supprimer_analyse(request, pk):
    """
    Supprime une analyse
    """
    analyse = get_object_or_404(AnalyseCode, pk=pk)
    
    if request.method == 'POST':
        nom = analyse.nom_fichier
        analyse.delete()
        messages.success(request, f"Analyse '{nom}' supprimée")
        return redirect('core:historique')
    
    return redirect('core:detail', pk=pk)


# ===== API JSON =====

def api_analyser(request):
    """
    API JSON pour analyser du code (POST)
    
    Exemple d'utilisation:
    curl -X POST http://localhost:8000/api/analyser/ \
         -H "Content-Type: application/json" \
         -d '{"nom_fichier": "test.py", "outil": "Python", "contenu": "print(1)"}'
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode POST requise'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        nom_fichier = data.get('nom_fichier', 'code.py')
        outil = data.get('outil', 'Python')
        contenu = data.get('contenu', '')
        description = data.get('description', '')
        
        if not contenu:
            return JsonResponse({'error': 'Le contenu est requis'}, status=400)
        
        service = QualityGateService()
        analyse = service.analyser_code(
            nom_fichier=nom_fichier,
            outil=outil,
            contenu=contenu,
            description=description
        )
        
        # Construire la réponse JSON
        response_data = {
            'id': analyse.pk,
            'nom_fichier': analyse.nom_fichier,
            'outil': analyse.outil,
            'score': analyse.score,
            'est_approuve': analyse.est_approuve,
            'temps_analyse': analyse.temps_analyse,
            'statistiques': {
                'total': analyse.nb_problemes_total,
                'critiques': analyse.nb_critiques,
                'warnings': analyse.nb_warnings,
                'infos': analyse.nb_infos,
            },
            'problemes': [
                {
                    'severite': p.severite,
                    'categorie': p.categorie,
                    'source': p.source,
                    'message': p.message,
                    'suggestion': p.suggestion,
                    'ligne': p.ligne,
                }
                for p in analyse.problemes.all()
            ]
        }
        
        return JsonResponse(response_data)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def api_statistiques(request):
    """
    API JSON pour les statistiques globales
    """
    service = QualityGateService()
    stats = service.get_statistiques_globales()
    
    return JsonResponse(stats)


def exporter_rapport(request, pk, format='json'):
    """
    Exporte un rapport en JSON ou HTML
    """
    analyse = get_object_or_404(AnalyseCode, pk=pk)
    
    if format == 'json':
        data = {
            'meta': {
                'version': '2.0',
                'date_analyse': analyse.date_creation.isoformat(),
            },
            'fichier': {
                'nom': analyse.nom_fichier,
                'outil': analyse.outil,
                'description': analyse.description,
            },
            'resultat': {
                'score': analyse.score,
                'est_approuve': analyse.est_approuve,
                'temps_analyse': analyse.temps_analyse,
            },
            'statistiques': {
                'total': analyse.nb_problemes_total,
                'critiques': analyse.nb_critiques,
                'warnings': analyse.nb_warnings,
                'infos': analyse.nb_infos,
                'flake8': analyse.nb_flake8,
                'bandit': analyse.nb_bandit,
                'openai': analyse.nb_openai,
                'manuel': analyse.nb_manuel,
            },
            'problemes': [
                {
                    'severite': p.severite,
                    'categorie': p.categorie,
                    'source': p.source,
                    'message': p.message,
                    'suggestion': p.suggestion,
                    'ligne': p.ligne,
                    'code_erreur': p.code_erreur,
                }
                for p in analyse.problemes.all()
            ]
        }
        
        response = HttpResponse(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="rapport_{analyse.pk}.json"'
        return response
    
    # Format HTML
    return render(request, 'core/rapport_export.html', {'analyse': analyse})