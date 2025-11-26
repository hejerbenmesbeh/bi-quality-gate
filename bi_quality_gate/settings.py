"""
Étudiant 1: Configuration Django
================================
Ce fichier configure tout le projet Django.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Clé secrète Django (à changer en production!)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'votre-cle-secrete-dev')

# Mode debug (désactiver en production)
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ===== APPLICATIONS INSTALLÉES =====
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Notre application
    'core',
    
    # Formulaires améliorés (optionnel)
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bi_quality_gate.urls'

# ===== TEMPLATES =====
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Dossier templates global
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bi_quality_gate.wsgi.application'

# ===== BASE DE DONNÉES =====
# SQLite pour le développement (simple, pas besoin d'installer quoi que ce soit)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===== INTERNATIONALISATION =====
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ===== FICHIERS STATIQUES (CSS, JS) =====
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ===== FICHIERS MÉDIA (uploads) =====
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===== CONFIGURATION CRISPY FORMS =====
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== CONFIGURATION QUALITY GATE (Personnalisée) =====
QUALITY_GATE_CONFIG = {
    # API OpenAI
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    'OPENAI_MODEL': 'gpt-3.5-turbo',
    
    # Seuils de qualité
    'SCORE_MINIMUM': 70,
    'PENALITE_CRITIQUE': 30,
    'PENALITE_WARNING': 10,
    'PENALITE_INFO': 2,
    
    # Configuration Flake8
    'FLAKE8_MAX_LINE_LENGTH': 120,
    'FLAKE8_IGNORE': ['E203', 'W503'],
    
    # Configuration Bandit
    'BANDIT_SEVERITY': 'LOW',
}