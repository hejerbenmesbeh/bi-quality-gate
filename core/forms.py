"""
Étudiant 1: Formulaires Django
==============================
Les formulaires permettent de valider les données entrées par l'utilisateur.
"""

from django import forms
from .models import AnalyseCode, OutilBI


class AnalyseCodeForm(forms.Form):
    """
    Formulaire pour soumettre du code à analyser
    
    Note: On utilise un Form simple plutôt qu'un ModelForm
    car on veut plus de contrôle sur le processus.
    """
    
    nom_fichier = forms.CharField(
        max_length=255,
        label="Nom du fichier",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: etl_ventes.py, dashboard_query.sql'
        }),
        help_text="Donnez un nom à votre fichier"
    )
    
    outil = forms.ChoiceField(
        choices=OutilBI.choices,
        label="Langage / Outil",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Sélectionnez le langage de votre code"
    )
    
    contenu_code = forms.CharField(
        label="Code source",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': 'Collez votre code ici...',
            'style': 'font-family: monospace;'
        }),
        help_text="Collez le code que vous souhaitez analyser"
    )
    
    description = forms.CharField(
        required=False,
        label="Description (optionnel)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Décrivez ce que fait ce code...'
        }),
        help_text="Aide l'IA à mieux comprendre votre code"
    )
    
    # Options d'analyse
    utiliser_flake8 = forms.BooleanField(
        required=False,
        initial=True,
        label="Utiliser Flake8 (Style Python)",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    utiliser_bandit = forms.BooleanField(
        required=False,
        initial=True,
        label="Utiliser Bandit (Sécurité)",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    utiliser_ia = forms.BooleanField(
        required=False,
        initial=True,
        label="Utiliser l'analyse IA (OpenAI)",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_contenu_code(self):
        """
        Validation personnalisée du code
        
        Cette méthode est appelée automatiquement par Django
        """
        code = self.cleaned_data.get('contenu_code', '')
        
        # Vérifier que le code n'est pas vide
        if not code.strip():
            raise forms.ValidationError("Le code ne peut pas être vide")
        
        # Vérifier la taille minimale
        if len(code.strip()) < 10:
            raise forms.ValidationError("Le code semble trop court pour être analysé")
        
        # Vérifier la taille maximale (éviter les abus)
        if len(code) > 50000:  # ~50Ko
            raise forms.ValidationError("Le code est trop long (maximum 50 000 caractères)")
        
        return code
    
    def clean(self):
        """
        Validation globale du formulaire
        """
        cleaned_data = super().clean()
        outil = cleaned_data.get('outil')
        utiliser_flake8 = cleaned_data.get('utiliser_flake8')
        utiliser_bandit = cleaned_data.get('utiliser_bandit')
        
        # Flake8 et Bandit ne fonctionnent qu'avec Python
        if outil != 'Python':
            if utiliser_flake8 or utiliser_bandit:
                # Désactiver silencieusement au lieu d'erreur
                cleaned_data['utiliser_flake8'] = False
                cleaned_data['utiliser_bandit'] = False
        
        return cleaned_data


class UploadFileForm(forms.Form):
    """
    Formulaire alternatif pour uploader un fichier
    """
    
    fichier = forms.FileField(
        label="Fichier à analyser",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.py,.sql,.dax,.m,.txt'
        }),
        help_text="Formats acceptés: .py, .sql, .dax, .m, .txt"
    )
    
    description = forms.CharField(
        required=False,
        label="Description",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )
    
    def clean_fichier(self):
        """Valide le fichier uploadé"""
        fichier = self.cleaned_data.get('fichier')
        
        if fichier:
            # Vérifier l'extension
            extensions_valides = ['.py', '.sql', '.dax', '.m', '.txt']
            ext = '.' + fichier.name.split('.')[-1].lower()
            
            if ext not in extensions_valides:
                raise forms.ValidationError(
                    f"Extension non supportée. Extensions valides: {', '.join(extensions_valides)}"
                )
            
            # Vérifier la taille (max 1 Mo)
            if fichier.size > 1024 * 1024:
                raise forms.ValidationError("Le fichier est trop volumineux (max 1 Mo)")
        
        return fichier