# -*- coding: utf-8 -*-
"""Tables de correspondance (catégories, pays, drapeaux) et chaînes i18n."""

# Catégorie source (FR) -> (clé stable, label EN)
CATEGORIES = {
    "Généraliste / autre":        ("general",   "General / other"),
    "Actualités et médias":       ("news",      "News & media"),
    "Sport":                      ("sport",     "Sports"),
    "Automobile":                 ("auto",      "Automotive"),
    "Culture et divertissement":  ("culture",   "Culture & entertainment"),
    "Technologie":                ("tech",      "Technology"),
    "Emploi et formation":        ("jobs",      "Jobs & training"),
    "Radio et audio":             ("audio",     "Radio & audio"),
    "Lifestyle":                  ("lifestyle", "Lifestyle"),
    "Commerce et consommation":   ("retail",    "Retail & shopping"),
    "Finance et économie":        ("finance",   "Finance & economy"),
    "Maison et immobilier":       ("home",      "Home & real estate"),
    "Voyage et tourisme":         ("travel",    "Travel & tourism"),
    "Santé et bien-être":         ("health",    "Health & wellness"),
    "Technique / test":           ("technical", "Technical / test"),
    "Cuisine":                    ("food",      "Food & cooking"),
    "Sécurité":                   ("security",  "Security"),
    "Animaux":                    ("animals",   "Animals"),
}

# Pays source (FR) -> (code, drapeau emoji, nom EN)
COUNTRIES = {
    "Allemagne":                   ("DE", "🇩🇪", "Germany"),
    "France":                      ("FR", "🇫🇷", "France"),
    "Espagne":                     ("ES", "🇪🇸", "Spain"),
    "Royaume-Uni":                 ("GB", "🇬🇧", "United Kingdom"),
    "Italie":                      ("IT", "🇮🇹", "Italy"),
    "États-Unis":                  ("US", "🇺🇸", "United States"),
    "Autriche":                    ("AT", "🇦🇹", "Austria"),
    "Canada":                      ("CA", "🇨🇦", "Canada"),
    "Pologne":                     ("PL", "🇵🇱", "Poland"),
    "Union européenne":            ("EU", "🇪🇺", "European Union"),
    "Danemark":                    ("DK", "🇩🇰", "Denmark"),
    "Monaco":                      ("MC", "🇲🇨", "Monaco"),
    "Portugal":                    ("PT", "🇵🇹", "Portugal"),
    "Suisse":                      ("CH", "🇨🇭", "Switzerland"),
    "Suède":                       ("SE", "🇸🇪", "Sweden"),
    "International / indéterminé":  ("INT", "🌐", "International / undetermined"),
}
COUNTRY_FALLBACK = ("INT", "🌐", "International / undetermined")
