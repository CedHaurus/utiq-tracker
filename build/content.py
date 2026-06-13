# -*- coding: utf-8 -*-
"""Contenu éditorial bilingue : chaînes UI, intro, FAQ, doc API, mentions légales."""

SOCIAL = {
    "site":   "https://christopheboutry.com",
    "legal":  "https://christopheboutry.com/mentions-legales/",
    "x":      "https://x.com/Ced_haurus",
    "github": "https://github.com/CedHaurus",
}

CONSENT_HUB = "https://consenthub.utiq.com/"

# ---------------------------------------------------------------------------
# Chaînes d'interface
# ---------------------------------------------------------------------------
UI = {
"fr": {
    "lang": "fr",
    "site_name": "Utiq Tracker",
    "tagline": "Référencement des sites internet et plateformes à travers le monde utilisant Utiq.",
    "nav_list": "Le référencement",
    "nav_faq": "FAQ Utiq",
    "nav_about": "À propos d’Utiq",
    "nav_optout": "Se désinscrire",
    "lang_switch": "EN",
    "lang_switch_label": "English version",
    "intro_html": (
        "<strong>Utiq</strong> est un mouchard publicitaire monté par quatre géants des télécoms "
        "(Deutsche Telekom, Orange, Telefónica, Vodafone) qui transforme votre opérateur en traceur : votre "
        "connexion mobile ou fixe — donc votre numéro, votre abonnement — devient un identifiant publicitaire "
        "qui vous suit de site en site, de navigateur en navigateur et d’appareil en appareil, que ni la "
        "navigation privée ni l’effacement des cookies n’arrêtent. <strong>Le problème : ce n’est plus un site "
        "qui vous piste, c’est votre propre fournisseur d’accès qui monnaie votre identité aux annonceurs.</strong>"
    ),
    "search_ph": "Rechercher un site, un domaine, un mot-clé…",
    "filter_scope": "Périmètre",
    "scope_all": "Tous",
    "scope_fr": "France",
    "scope_world": "Monde",
    "filter_cat": "Catégorie",
    "cat_all": "Toutes les catégories",
    "filter_country": "Pays / édition",
    "country_all": "Tous les pays",
    "results_one": "site référencé",
    "results_many": "sites référencés",
    "reset": "Réinitialiser",
    "slogan": "Souriez, vous êtes traqué.",
    "see_more": "Voir plus",
    "see_more_rest": "Voir plus ({n} restants)",
    "card_since": "Utiq depuis",
    "card_go": "Voir le site",
    "card_visit": "Ouvrir",
    "no_results": "Aucun site ne correspond à votre recherche.",
    "downloads": "Télécharger la liste",
    "dl_json": "JSON",
    "dl_csv": "CSV",
    "api_link": "Accès API (JSON)",
    "non_exhaustive": "Liste non exhaustive, soumise à modification.",
    "disclaimer": (
        "Ce site est un projet indépendant. Il n’a aucun lien avec Utiq SA/NV, ses opérateurs fondateurs "
        "ni aucune des marques citées. Les informations sont fournies à titre informatif."
    ),
    "footer_by": "Créé par",
    "footer_legal": "Mentions légales",
    "back_home": "← Retour à l’accueil",
    "meta_desc": (
        "Utiq Tracker recense les sites web et plateformes, en France et dans le monde, qui utilisent Utiq, "
        "le pistage publicitaire des opérateurs télécoms. Recherche plein texte, filtres, export JSON/CSV."
    ),
    "faq_title": "FAQ Utiq",
    "faq_intro": "Tout comprendre sur Utiq : ce que c’est, comment ça vous trace, comment vous y soustraire.",
    "about_title": "À propos d’Utiq",
    "method_title": "Méthodologie",
    "api_title": "Accès aux données (API JSON)",
},
"en": {
    "lang": "en",
    "site_name": "Utiq Tracker",
    "tagline": "An index of websites and platforms around the world that use Utiq.",
    "nav_list": "The index",
    "nav_faq": "Utiq FAQ",
    "nav_about": "About Utiq",
    "nav_optout": "Opt out",
    "lang_switch": "FR",
    "lang_switch_label": "Version française",
    "intro_html": (
        "<strong>Utiq</strong> is an advertising tracker built by four telecom giants (Deutsche Telekom, Orange, "
        "Telefónica, Vodafone) that turns your carrier into a tracker: your mobile or fixed connection — your "
        "number, your subscription — becomes an advertising ID that follows you from site to site, browser to "
        "browser and device to device, which neither private browsing nor clearing your cookies can stop. "
        "<strong>The catch: it’s no longer a website tracking you, it’s your own internet provider selling your "
        "identity to advertisers.</strong>"
    ),
    "search_ph": "Search a site, a domain, a keyword…",
    "filter_scope": "Scope",
    "scope_all": "All",
    "scope_fr": "France",
    "scope_world": "World",
    "filter_cat": "Category",
    "cat_all": "All categories",
    "filter_country": "Country / edition",
    "country_all": "All countries",
    "results_one": "site listed",
    "results_many": "sites listed",
    "reset": "Reset",
    "slogan": "Smile, you’re being tracked.",
    "see_more": "Show more",
    "see_more_rest": "Show more ({n} remaining)",
    "card_since": "Utiq since",
    "card_go": "Visit site",
    "card_visit": "Open",
    "no_results": "No site matches your search.",
    "downloads": "Download the list",
    "dl_json": "JSON",
    "dl_csv": "CSV",
    "api_link": "API access (JSON)",
    "non_exhaustive": "Non-exhaustive list, subject to change.",
    "disclaimer": (
        "This is an independent project. It is not affiliated with Utiq SA/NV, its founding operators, "
        "or any of the brands mentioned. Information is provided for informational purposes only."
    ),
    "footer_by": "Built by",
    "footer_legal": "Legal notice",
    "back_home": "← Back to home",
    "meta_desc": (
        "Utiq Tracker lists the websites and platforms, in France and worldwide, that use Utiq, the telecom "
        "operators’ advertising tracker. Full-text search, filters, JSON/CSV export."
    ),
    "faq_title": "Utiq FAQ",
    "faq_intro": "Everything about Utiq: what it is, how it tracks you, how to opt out.",
    "about_title": "About Utiq",
    "method_title": "Methodology",
    "api_title": "Data access (JSON API)",
},
}

# ---------------------------------------------------------------------------
# FAQ — liste d'items (question, réponse HTML). Le 1er = désinscription.
# ---------------------------------------------------------------------------
FAQ = {
"fr": [
    ("Comment me désinscrire d’Utiq ?",
     f"<p>Le moyen le plus direct est le <strong>Consent Hub officiel d’Utiq</strong> : "
     f"<a href=\"{CONSENT_HUB}\" target=\"_blank\" rel=\"noopener\">consenthub.utiq.com</a>. "
     "Cliquez sur « Manage Utiq consents » puis « Withdraw Utiq consents » et choisissez "
     "<strong>« Remove all Utiq consents »</strong>. Vos consentements sont alors supprimés et la technologie "
     "cesse d’être active. Utiq indique que les données associées sont effacées de sa plateforme "
     "<strong>sous 24 heures maximum</strong>, tant que vous ne redonnez pas de consentement entre-temps.</p>"
     "<p>Vous pouvez aussi retirer le consentement site par site via le lien « Manage Utiq » présent en pied "
     "de page des sites participants (le retrait ne vaut alors que pour ce site).</p>"),
    ("Comment me prémunir d’Utiq ?",
     "<ul>"
     "<li><strong>Refusez la bannière.</strong> Quand un site demande le consentement Utiq, choisissez "
     "« Refuser » / « Reject ». Sans consentement, la technologie reste inactive.</li>"
     "<li><strong>Bloquez les domaines Utiq</strong> au niveau DNS ou du navigateur. Le pistage repose sur des "
     "domaines techniques (<code>*.utiq-aws.net</code>, <code>*.utiq.com</code>, sous-domaines <code>utiq.&lt;site&gt;</code>). "
     "Des blocklists prêtes à l’emploi sont téléchargeables ci-dessous.</li>"
     "<li><strong>Utilisez un DNS filtrant</strong> (AdGuard Home, NextDNS, Pi-hole) ou un bloqueur de contenu "
     "(uBlock Origin) avec ces listes.</li>"
     "<li><strong>Sur mobile</strong>, l’identifiant dérive de votre connexion opérateur : passer par un VPN ou "
     "le Wi-Fi d’un réseau non participant limite le rattachement réseau, mais ne remplace pas le retrait de "
     "consentement.</li>"
     "</ul>"
     "<p class=\"faq-dl\"><strong>Blocklists Utiq à télécharger :</strong> "
     "<a href=\"/blocklists/utiq-standard-hosts.txt\">hosts</a> · "
     "<a href=\"/blocklists/utiq-standard-domains.txt\">domaines</a> · "
     "<a href=\"/blocklists/utiq-standard-adblock.txt\">AdGuard / uBlock</a> · "
     "<a href=\"/blocklists/utiq-standard-unbound.conf\">Unbound</a> · "
     "<a href=\"/blocklists/utiq-standard-rpz.txt\">RPZ</a> "
     "(<a href=\"/blocklists/\">versions « strict » et index</a>).</p>"),
    ("Qu’est-ce qu’Utiq, concrètement ?",
     "<p>Utiq est une société (issue d’une coentreprise de Deutsche Telekom, Orange, Telefónica et Vodafone, "
     "lancée en 2023) qui propose une technologie d’identification publicitaire fondée sur le réseau des "
     "opérateurs. Plutôt que de déposer un cookie dans votre navigateur, elle s’appuie sur un "
     "<strong>« signal réseau »</strong> fourni par votre opérateur pour générer des identifiants pseudonymes "
     "(martechpass, adtechpass) que les marques et régies utilisent pour le ciblage et la mesure publicitaire.</p>"),
    ("Comment Utiq fonctionne-t-il techniquement ?",
     "<p>Quand vous acceptez sur un site participant, le SDK Utiq fait un appel sécurisé à votre opérateur, qui "
     "renvoie un <em>network signal</em> correspondant à votre connexion. Ce signal est mappé à un identifiant "
     "stable et aléatoire (le <em>consentpass</em>), d’où sont dérivés les identifiants exposés aux annonceurs. "
     "Ces signaux fonctionnent <strong>cross-navigateur et cross-appareil</strong> sur la même connexion, ce qui "
     "permet un ré-identification à grande échelle.</p>"),
    ("Quels opérateurs et quels pays sont concernés ?",
     "<p>Les opérateurs fondateurs sont Deutsche Telekom, Orange, Telefónica et Vodafone, rejoints par d’autres. "
     "Le déploiement est surtout européen (Allemagne, France, Espagne, Royaume-Uni, Italie, Autriche…). La "
     "répartition des sites recensés ici reflète ce périmètre.</p>"),
    ("Comment ce site détecte-t-il les sites utilisant Utiq ?",
     "<p>Le référencement croise plusieurs signaux publics : enregistrements DNS pointant vers l’infrastructure "
     "Utiq (<code>*.utiq-aws.net</code>), certificats TLS émis pour des sous-domaines <code>utiq.&lt;site&gt;</code> "
     "(journaux Certificate Transparency), et vérification que le <em>loader</em> Utiq répond bien sur le domaine. "
     "La date « Utiq depuis » est <strong>estimée</strong> (première trace publique connue) et le pays est une "
     "estimation d’édition de marché, pas un siège juridique.</p>"),
    ("La liste est-elle exhaustive ?",
     "<p><strong>Non.</strong> C’est un instantané, non exhaustif et susceptible d’évoluer. Des sites peuvent "
     "adopter ou retirer Utiq à tout moment. La liste est fournie à titre informatif.</p>"),
    ("Puis-je réutiliser les données ?",
     "<p>Oui. La liste est exportable en <a href=\"/data/utiq-sites.json\">JSON</a> et "
     "<a href=\"/data/utiq-sites.csv\">CSV</a>, et un accès API stable est documenté sur la "
     "<a href=\"/api/\">page API</a> (avec CORS, pour un usage externe).</p>"),
],
"en": [
    ("How do I opt out of Utiq?",
     f"<p>The most direct way is Utiq’s official <strong>Consent Hub</strong>: "
     f"<a href=\"{CONSENT_HUB}\" target=\"_blank\" rel=\"noopener\">consenthub.utiq.com</a>. "
     "Click “Manage Utiq consents”, then “Withdraw Utiq consents” and choose "
     "<strong>“Remove all Utiq consents”</strong>. Your consents are deleted and the technology stops being "
     "active. Utiq states that the associated data is erased from its platform <strong>within 24 hours</strong>, "
     "as long as you don’t grant new consent in the meantime.</p>"
     "<p>You can also withdraw consent site by site via the “Manage Utiq” link in the footer of participating "
     "websites (this only applies to that site).</p>"),
    ("How can I protect myself from Utiq?",
     "<ul>"
     "<li><strong>Reject the banner.</strong> When a site asks for Utiq consent, choose “Reject”. Without "
     "consent, the technology stays inactive.</li>"
     "<li><strong>Block Utiq domains</strong> at the DNS or browser level. Tracking relies on technical domains "
     "(<code>*.utiq-aws.net</code>, <code>*.utiq.com</code>, <code>utiq.&lt;site&gt;</code> subdomains). "
     "Ready-made blocklists are downloadable below.</li>"
     "<li><strong>Use a filtering DNS</strong> (AdGuard Home, NextDNS, Pi-hole) or a content blocker (uBlock "
     "Origin) with these lists.</li>"
     "<li><strong>On mobile</strong>, the identifier derives from your carrier connection: using a VPN or a "
     "non-participating network limits the network binding, but does not replace withdrawing consent.</li>"
     "</ul>"
     "<p class=\"faq-dl\"><strong>Utiq blocklists to download:</strong> "
     "<a href=\"/blocklists/utiq-standard-hosts.txt\">hosts</a> · "
     "<a href=\"/blocklists/utiq-standard-domains.txt\">domains</a> · "
     "<a href=\"/blocklists/utiq-standard-adblock.txt\">AdGuard / uBlock</a> · "
     "<a href=\"/blocklists/utiq-standard-unbound.conf\">Unbound</a> · "
     "<a href=\"/blocklists/utiq-standard-rpz.txt\">RPZ</a> "
     "(<a href=\"/blocklists/\">“strict” versions and index</a>).</p>"),
    ("What exactly is Utiq?",
     "<p>Utiq is a company (spun out of a joint venture between Deutsche Telekom, Orange, Telefónica and "
     "Vodafone, launched in 2023) offering an advertising identification technology based on operator networks. "
     "Rather than dropping a cookie in your browser, it relies on a <strong>“network signal”</strong> provided by "
     "your carrier to generate pseudonymous identifiers (martechpass, adtechpass) used by brands and ad networks "
     "for targeting and measurement.</p>"),
    ("How does Utiq work technically?",
     "<p>When you accept on a participating site, the Utiq SDK makes a secure call to your operator, which "
     "returns a <em>network signal</em> matching your connection. That signal is mapped to a stable random "
     "identifier (the <em>consentpass</em>), from which the identifiers exposed to advertisers are derived. These "
     "signals work <strong>cross-browser and cross-device</strong> over the same connection, enabling "
     "re-identification at scale.</p>"),
    ("Which operators and countries are involved?",
     "<p>The founding operators are Deutsche Telekom, Orange, Telefónica and Vodafone, joined by others. "
     "Deployment is mostly European (Germany, France, Spain, United Kingdom, Italy, Austria…). The distribution "
     "of the sites listed here reflects that scope.</p>"),
    ("How does this site detect websites using Utiq?",
     "<p>The index cross-references several public signals: DNS records pointing to Utiq infrastructure "
     "(<code>*.utiq-aws.net</code>), TLS certificates issued for <code>utiq.&lt;site&gt;</code> subdomains "
     "(Certificate Transparency logs), and a check that the Utiq <em>loader</em> actually responds on the domain. "
     "The “Utiq since” date is <strong>estimated</strong> (earliest known public trace) and the country is an "
     "estimate of the market edition, not a legal headquarters.</p>"),
    ("Is the list exhaustive?",
     "<p><strong>No.</strong> It is a snapshot, non-exhaustive and subject to change. Sites may adopt or drop "
     "Utiq at any time. The list is provided for informational purposes.</p>"),
    ("Can I reuse the data?",
     "<p>Yes. The list is exportable as <a href=\"/data/utiq-sites.json\">JSON</a> and "
     "<a href=\"/data/utiq-sites.csv\">CSV</a>, and a stable API access is documented on the "
     "<a href=\"/api/\">API page</a> (with CORS, for external use).</p>"),
],
}
