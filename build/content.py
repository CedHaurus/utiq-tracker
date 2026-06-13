# -*- coding: utf-8 -*-
"""Registre des langues et chargement du contenu i18n.

Le contenu éditorial de chaque langue est un fichier build/i18n/<lang>.json.
Pour ajouter une langue : déposer le JSON correspondant (même schéma que en.json)
et l'ajouter à LANGS. Le build ignore une langue dont le JSON est absent.
"""
import os
import json

SOCIAL = {
    "site":   "https://christopheboutry.com",
    "x":      "https://x.com/Ced_haurus",
    "github": "https://github.com/CedHaurus",
    "repo":   "https://github.com/CedHaurus/utiq-tracker",
}
CONSENT_HUB = "https://consenthub.utiq.com/"

# Ordre d'affichage. fr en tête (racine), puis le reste.
LANGS = ["fr", "en", "de", "es", "it", "pl", "da", "pt", "sv"]

LANG_NAMES = {
    "fr": "Français", "en": "English", "de": "Deutsch", "es": "Español",
    "it": "Italiano", "pl": "Polski", "da": "Dansk", "pt": "Português", "sv": "Svenska",
}
LANG_LOCALE = {
    "fr": "fr_FR", "en": "en_GB", "de": "de_DE", "es": "es_ES",
    "it": "it_IT", "pl": "pl_PL", "da": "da_DK", "pt": "pt_PT", "sv": "sv_SE",
}

# Pays « maison » par défaut d'une langue (bouton de filtre pays, avant l'affinage
# JS selon le pays réel du navigateur).
LANG_HOME = {
    "fr": "FR", "en": "GB", "de": "DE", "es": "ES", "it": "IT",
    "pl": "PL", "da": "DK", "pt": "PT", "sv": "SE",
}

I18N_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n")


def load_content():
    """Charge {lang: bundle} pour chaque langue dont le JSON existe (ordre LANGS)."""
    content = {}
    for lang in LANGS:
        p = os.path.join(I18N_DIR, lang + ".json")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                content[lang] = json.load(f)
    return content
