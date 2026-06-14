# -*- coding: utf-8 -*-
"""Correspondances neutres (langue-indépendantes).

Les LABELS traduits des catégories et des pays vivent dans build/i18n/<lang>.json
(clés "categories" et "countries"). Ici on ne garde que :
  - la catégorie source (FR, telle qu'écrite dans data/source.json) -> clé stable
  - le pays source (FR) -> (code ISO, drapeau emoji)
"""

# Catégorie source (FR, dans source.json) -> clé stable
CAT_KEY = {
    "Généraliste / autre":        "general",
    "Actualités et médias":       "news",
    "Sport":                      "sport",
    "Automobile":                 "auto",
    "Culture et divertissement":  "culture",
    "Technologie":                "tech",
    "Emploi et formation":        "jobs",
    "Radio et audio":             "audio",
    "Lifestyle":                  "lifestyle",
    "Commerce et consommation":   "retail",
    "Finance et économie":        "finance",
    "Maison et immobilier":       "home",
    "Voyage et tourisme":         "travel",
    "Santé et bien-être":         "health",
    "Technique / test":           "technical",
    "Cuisine":                    "food",
    "Sécurité":                   "security",
    "Animaux":                    "animals",
    "Opérateur télécom":          "operator",
}
CAT_FALLBACK = "general"

# Pays source (FR) -> (code ISO, drapeau)
COUNTRY_META = {
    "Allemagne":                  ("DE", "🇩🇪"),
    "France":                     ("FR", "🇫🇷"),
    "Espagne":                    ("ES", "🇪🇸"),
    "Royaume-Uni":                ("GB", "🇬🇧"),
    "Italie":                     ("IT", "🇮🇹"),
    "États-Unis":                 ("US", "🇺🇸"),
    "Autriche":                   ("AT", "🇦🇹"),
    "Canada":                     ("CA", "🇨🇦"),
    "Pologne":                    ("PL", "🇵🇱"),
    "Union européenne":           ("EU", "🇪🇺"),
    "Danemark":                   ("DK", "🇩🇰"),
    "Monaco":                     ("MC", "🇲🇨"),
    "Portugal":                   ("PT", "🇵🇹"),
    "Suisse":                     ("CH", "🇨🇭"),
    "Suède":                      ("SE", "🇸🇪"),
    "International / indéterminé": ("INT", "🌐"),
}
COUNTRY_FALLBACK = ("INT", "🌐")
