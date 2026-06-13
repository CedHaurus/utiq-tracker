#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur statique d'Utiq Tracker (FR + EN) à partir de data/source.json."""
import json, csv, os, re, shutil, html, hashlib, unicodedata, io
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests

from maps import CATEGORIES, COUNTRIES, COUNTRY_FALLBACK
from content import UI, FAQ, SOCIAL, CONSENT_HUB

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD  = os.path.join(ROOT, "build")
STATIC = os.path.join(BUILD, "static")
PUB    = os.path.join(ROOT, "public")
CACHE  = os.path.join(BUILD, "favicons_cache")
SRC    = os.path.join(ROOT, "data", "source.json")
BLOCK  = os.path.join(ROOT, "blocklists")
SITE   = "https://utiq-tracker.online"
PAGE_URLS = {
    "list":  ("/", "/en/"),
    "faq":   ("/faq.html", "/en/faq.html"),
    "about": ("/a-propos.html", "/en/about.html"),
    "legal": ("/mentions-legales.html", "/en/legal-notice.html"),
    "api":   ("/api/", "/en/api/"),
}
GEN_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
YEAR   = datetime.now(timezone.utc).year

def _asset_ver():
    h = hashlib.md5()
    for f in ("style.css", "app.js"):
        h.update(open(os.path.join(STATIC, f), "rb").read())
    return h.hexdigest()[:8]
ASSET_VER = _asset_ver()

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
MONO_COLORS = ["#e8590c", "#1b1a17", "#0b7285", "#5f3dc4", "#a61e4d", "#2b8a3e", "#9c6644", "#1864ab"]


def strip(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def safe(domain):
    return re.sub(r"[^a-z0-9._-]", "_", domain.lower())


def truncate(s, n=165):
    s = (s or "").strip()
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(" ", 1)[0].rstrip(" ,;.:")
    return cut + "…"


# ---------------------------------------------------------------------------
# 1. Normalisation
# ---------------------------------------------------------------------------
def load_records():
    data = json.load(open(SRC, encoding="utf-8"))
    recs = []
    for d in data["detections"]:
        domain = d["domain"]
        name = (d.get("site_name") or domain).strip()
        url = d.get("final_url") or f"https://{domain}/"
        desc = (d.get("description") or "").strip()
        cat_fr = d.get("category") or "Généraliste / autre"
        ckey, cen = CATEGORIES.get(cat_fr, ("general", "General / other"))
        cfr = d.get("country") or "International / indéterminé"
        code, flag, cnEN = COUNTRIES.get(cfr, COUNTRY_FALLBACK)
        region = "fr" if cfr == "France" else "world"
        since = d.get("estimated_date") or ""
        recs.append({
            "domain": domain, "name": name, "url": url,
            "description": desc, "desc_card": truncate(desc),
            "category_fr": cat_fr, "category_en": cen, "cat_key": ckey,
            "country_fr": cfr, "country_en": cnEN, "country_code": code, "flag": flag,
            "region": region, "since": since,
            "confirmed": bool(d.get("loader_confirmed")),
            "search": strip(f"{name} {domain} {desc}"),
        })
    # France d'abord, puis tri alphabétique par nom
    recs.sort(key=lambda r: (r["region"] != "fr", strip(r["name"])))
    return recs


# ---------------------------------------------------------------------------
# 2. Favicons (build-time, self-hostées, fallback monogramme)
# ---------------------------------------------------------------------------
def fetch_favicon(domain):
    dst = os.path.join(CACHE, safe(domain) + ".png")
    if os.path.exists(dst):
        return domain, os.path.getsize(dst) > 70
    ok = False
    for u in (f"https://icons.duckduckgo.com/ip3/{domain}.ico",
              f"https://www.google.com/s2/favicons?domain={domain}&sz=64"):
        try:
            r = requests.get(u, headers=UA, timeout=10)
            if r.status_code == 200 and len(r.content) > 70 and "image" in r.headers.get("content-type", ""):
                open(dst, "wb").write(r.content)
                ok = True
                break
        except Exception:
            continue
    return domain, ok


def fetch_all_favicons(recs):
    os.makedirs(CACHE, exist_ok=True)
    have = {}
    with ThreadPoolExecutor(max_workers=16) as ex:
        for domain, ok in ex.map(lambda r: fetch_favicon(r["domain"]), recs):
            have[domain] = ok
    print(f"  favicons: {sum(have.values())}/{len(have)} récupérées")
    return have


# ---------------------------------------------------------------------------
# 3. Rendu HTML
# ---------------------------------------------------------------------------
def head(t, title, desc, page, lang, og="/assets/og.png", extra=""):
    fr_url, en_url = PAGE_URLS[page]
    alt_fr = SITE + fr_url
    alt_en = SITE + en_url
    canonical = SITE + (fr_url if lang == "fr" else en_url)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="fr" href="{alt_fr}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="alternate" hreflang="x-default" href="{alt_fr}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Utiq Tracker">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}{og}">
<meta property="og:locale" content="{'fr_FR' if lang=='fr' else 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{SITE}{og}">
<meta name="theme-color" content="#e8590c">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="stylesheet" href="/assets/style.css?v={ASSET_VER}">
{extra}</head>
<body>"""


def header(t, lang, active):
    base = "" if lang == "fr" else "/en"
    fr_url, en_url = PAGE_URLS[active]
    other_path = en_url if lang == "fr" else fr_url
    def link(href, label, key, cta=False):
        cls = ' class="cta"' if cta else (' aria-current="page"' if key == active else "")
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        return f'<a href="{href}"{cls}{ext}>{label}</a>'
    nav = "".join([
        link(base + "/", t["nav_list"], "list"),
        link(base + "/faq.html", t["nav_faq"], "faq"),
        link(base + "/a-propos.html" if lang == "fr" else base + "/about.html", t["nav_about"], "about"),
        link(CONSENT_HUB, t["nav_optout"], "optout", cta=True),
    ])
    return f"""<header class="site-header"><div class="wrap hbar">
<a class="brand" href="{base}/"><span class="logo-mark"><span>U</span></span>
<span class="brand-name">Utiq <b>Tracker</b></span></a>
<nav class="nav">{nav}
<button class="lang-btn" id="lang-toggle" data-target="{('en' if lang=='fr' else 'fr')}"
 onclick="location.href='{other_path}'" title="{html.escape(t['lang_switch_label'])}">{t['lang_switch']}</button>
</nav></div></header>"""


def footer(t, lang):
    x_svg = '<svg viewBox="0 0 24 24"><path d="M18.9 1.6h3.5l-7.6 8.7 9 11.9h-7L11.7 15l-6.3 7.2H1.9l8.1-9.3L1.3 1.6h7.1l4.7 6.2 5.8-6.2zm-1.2 18.7h1.9L7.1 3.6H5z"/></svg>'
    gh_svg = '<svg viewBox="0 0 24 24"><path d="M12 .5C5.4.5 0 5.9 0 12.6c0 5.3 3.4 9.8 8.2 11.4.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1.1-.8.1-.8.1-.8 1.2.1 1.9 1.3 1.9 1.3 1.1 1.9 2.9 1.4 3.6 1 .1-.8.4-1.4.8-1.7-2.7-.3-5.5-1.4-5.5-6 0-1.3.5-2.4 1.3-3.2-.1-.3-.6-1.6.1-3.3 0 0 1-.3 3.3 1.2a11.5 11.5 0 016 0C17.3 4.7 18.3 5 18.3 5c.7 1.7.2 3 .1 3.3.8.8 1.3 1.9 1.3 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.8-1.6 8.2-6.1 8.2-11.4C24 5.9 18.6.5 12 .5z"/></svg>'
    return f"""<footer class="site-footer">
<div class="wrap foot">
<div class="links">
<a href="{('/mentions-legales.html' if lang=='fr' else '/legal-notice.html')}">{t['footer_legal']}</a>
<span>·</span>
<span>{t['footer_by']} <a href="{SOCIAL['site']}" target="_blank" rel="noopener">Christophe Boutry</a></span>
</div>
<div class="social">
<a href="{SOCIAL['x']}" target="_blank" rel="noopener" aria-label="X">{x_svg}</a>
<a href="{SOCIAL['github']}" target="_blank" rel="noopener" aria-label="GitHub">{gh_svg}</a>
</div>
<p class="disc"><span class="ne">{html.escape(t['non_exhaustive'])}</span>{html.escape(t['disclaimer'])}
&nbsp;© {YEAR} Christophe Boutry.</p>
</div></footer>
<script src="/assets/app.js?v={ASSET_VER}" defer></script>
</body></html>"""


def card_html(r, t, hidden=False):
    if r["_fav"]:
        ico = f'<img loading="lazy" width="38" height="38" src="/assets/favicons/{safe(r["domain"])}.png" alt="">'
    else:
        color = MONO_COLORS[int(hashlib.md5(r["domain"].encode()).hexdigest(), 16) % len(MONO_COLORS)]
        ico = f'<span class="mono" style="background:{color}">{html.escape(r["name"][:1].upper() or "?")}</span>'
    cat = r["category_fr"] if t["lang"] == "fr" else r["category_en"]
    since = f'<span class="tag since">{t["card_since"]} {r["since"][:4]}</span>' if r["since"] else ""
    desc = f'<p class="card-desc">{html.escape(r["desc_card"])}</p>' if r["desc_card"] else ""
    hid = " hidden" if hidden else ""
    return f"""<article class="card has-go"{hid} data-search="{html.escape(r['search'])}" data-region="{r['region']}" data-cat="{r['cat_key']}" data-country="{r['country_code']}">
<div class="card-ico">{ico}</div>
<div class="card-body">
<h3 class="card-title" title="{html.escape(r['name'])}">{html.escape(r['name'])}</h3>
<a class="card-url" href="{html.escape(r['url'])}" target="_blank" rel="noopener noreferrer nofollow">{html.escape(r['domain'])}</a>
{desc}
<div class="card-meta"><span class="tag flag" title="{html.escape(r['country_fr'] if t['lang']=='fr' else r['country_en'])}">{r['flag']}</span><span class="tag cat">{html.escape(cat)}</span>{since}</div>
</div>
<a class="card-go" href="{html.escape(r['url'])}" target="_blank" rel="noopener noreferrer nofollow" aria-label="{html.escape(t['card_go'])}: {html.escape(r['name'])}">→</a>
</article>"""


def render_index(t, recs, counts, country_opts, cat_opts, lang):
    path = "/" if lang == "fr" else "/en/"
    base = "" if lang == "fr" else "/en"
    title = f"Utiq Tracker — {t['tagline']}"
    redirect = ""
    if lang == "fr":
        redirect = ("<script>(function(){try{var p=localStorage.getItem('utiq-lang');"
                    "if(p==='en'||(!p&&!/^fr\\b/i.test(navigator.language||'')))"
                    "location.replace('/en/');}catch(e){}})();</script>")
    # JSON-LD
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": "Utiq Tracker", "url": SITE,
             "inLanguage": lang, "description": t["meta_desc"],
             "potentialAction": {"@type": "SearchAction",
                                 "target": SITE + base + "/?q={search_term_string}",
                                 "query-input": "required name=search_term_string"}},
            {"@type": "Dataset", "name": "Sites utilisant Utiq" if lang == "fr" else "Websites using Utiq",
             "description": t["meta_desc"], "url": SITE + base + "/",
             "license": "https://creativecommons.org/licenses/by/4.0/",
             "creator": {"@type": "Person", "name": "Christophe Boutry", "url": SOCIAL["site"]},
             "dateModified": GEN_AT[:10],
             "distribution": [
                 {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": SITE + "/data/utiq-sites.json"},
                 {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": SITE + "/data/utiq-sites.csv"},
             ]},
        ],
    }
    ld_s = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'

    cards = "\n".join(card_html(r, t, hidden=(i >= 30)) for i, r in enumerate(recs))
    seg = (f'<button data-scope="all" aria-pressed="true">{t["scope_all"]}</button>'
           f'<button data-scope="fr">🇫🇷 {t["scope_fr"]}</button>'
           f'<button data-scope="world">🌍 {t["scope_world"]}</button>')
    out = head(t, title, t["meta_desc"], "list", lang, extra=redirect + ld_s)
    out += header(t, lang, "list")
    out += f"""<main>
<section class="hero"><div class="wrap">
<h1 class="hero-title">Utiq <span>Tracker</span></h1>
<p class="tagline">{html.escape(t['tagline'])} <span class="slogan-inline">{html.escape(t['slogan'])}</span></p>
<div class="intro">{t['intro_html']} <a href="{base}/a-propos.html" >{'En savoir plus' if lang=='fr' else 'Learn more'} →</a></div>
</div></section>

<section class="toolbar"><div class="wrap tb">
<div class="tb-top">
<label class="search"><span>🔎</span><input id="q" type="search" placeholder="{html.escape(t['search_ph'])}" aria-label="{html.escape(t['search_ph'])}"></label>
<div class="dl-group"><span class="lbl">{t['downloads']} :</span>
<a class="btn" href="/data/utiq-sites.json" download>⬇ {t['dl_json']}</a>
<a class="btn" href="/data/utiq-sites.csv" download>⬇ {t['dl_csv']}</a>
<a class="btn orange" href="{base}/api/">⚡ {t['api_link']}</a>
</div>
</div>
<div class="tb-filters">
<div class="segmented" role="group" aria-label="{html.escape(t['filter_scope'])}">{seg}</div>
<select id="f-cat" aria-label="{html.escape(t['filter_cat'])}">{cat_opts}</select>
<select id="f-country" aria-label="{html.escape(t['filter_country'])}">{country_opts}</select>
<button class="btn ghost" id="reset">↺ {t['reset']}</button>
</div>
<div class="tb-count"><span class="count"><b id="count-n">{len(recs)}</b> <span id="count-l">{t['results_many']}</span></span></div>
</div></section>

<section class="wrap"><div class="grid" id="grid">
{cards}
</div>
<div class="empty" id="empty">{html.escape(t['no_results'])}</div>
<div class="more-wrap" id="more-wrap"><button class="btn orange" id="more" data-tpl="{html.escape(t['see_more_rest'])}">{t['see_more']}</button></div>
</section>
</main>"""
    out += footer(t, lang)
    return out


def render_faq(t, lang):
    path = ("/faq.html" if lang == "fr" else "/en/faq.html")
    items = FAQ[lang]
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", " ", a)}}
                         for q, a in items]}
    ld_s = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    qa = "\n".join(
        f'<details class="qa"{" open" if i == 0 else ""}><summary>{html.escape(q)}</summary><div class="a">{a}</div></details>'
        for i, (q, a) in enumerate(items))
    out = head(t, f"{t['faq_title']} — Utiq Tracker", t["faq_intro"], "faq", lang, extra=ld_s)
    out += header(t, lang, "faq")
    out += f"""<main><section class="page wrap">
<h1 class="pix">{t['faq_title'].replace('Utiq','<b>Utiq</b>')}</h1>
<p class="lead">{html.escape(t['faq_intro'])}</p>
{qa}
</section></main>"""
    out += footer(t, lang)
    return out


def render_about(t, lang, n_total, n_fr):
    path = ("/a-propos.html" if lang == "fr" else "/en/about.html")
    if lang == "fr":
        body = f"""
<h3 class="pix">Qu’est-ce qu’Utiq&nbsp;?</h3>
<p>{t['intro_html']}</p>
<p>Lancé en 2023, Utiq se présente comme un service de consentement « authentique » au pistage
publicitaire opéré par les télécoms. En pratique, votre opérateur devient le maillon qui relie votre
identité d’abonné à votre navigation, là où les régies publicitaires perdaient en visibilité avec la
fin des cookies tiers.</p>
<h3 class="pix">Pourquoi c’est un problème&nbsp;?</h3>
<p>Le pistage opère <strong>au niveau du réseau</strong>, donc indépendamment du navigateur ou de
l’appareil, et survit au nettoyage des cookies ou à la navigation privée. Il s’appuie sur le
consentement, mais celui-ci est souvent demandé dans des bandeaux ambigus, parfois sous forme de
« consentir ou payer ».</p>
<h3 class="pix">Méthodologie de ce référencement</h3>
<p>La liste croise des signaux publics&nbsp;: enregistrements DNS pointant vers l’infrastructure Utiq
(<code>*.utiq-aws.net</code>), certificats TLS pour des sous-domaines <code>utiq.&lt;site&gt;</code>
(journaux Certificate Transparency), et vérification que le <em>loader</em> Utiq répond sur le domaine.
À ce jour, <strong>{n_total} sites</strong> sont recensés, dont <strong>{n_fr} en France</strong>. La date
« Utiq depuis » est estimée à partir de la première trace publique connue.</p>
<p><strong>Liste non exhaustive et susceptible d’évoluer.</strong> Une erreur&nbsp;? Un site à signaler&nbsp;?
Contactez <a href="{SOCIAL['site']}" target="_blank" rel="noopener">Christophe Boutry</a>.</p>
<h3 class="pix">Se désinscrire / se protéger</h3>
<p>Voir la <a href="/faq.html">FAQ</a>&nbsp;: désinscription via le
<a href="{CONSENT_HUB}" target="_blank" rel="noopener">Consent Hub Utiq</a> et blocklists DNS à télécharger.</p>
"""
    else:
        body = f"""
<h3 class="pix">What is Utiq?</h3>
<p>{t['intro_html']}</p>
<p>Launched in 2023, Utiq presents itself as an “authentic” consent service for telecom-operated
advertising tracking. In practice, your carrier becomes the link between your subscriber identity and
your browsing, exactly where ad networks were losing visibility with the end of third-party cookies.</p>
<h3 class="pix">Why is it a problem?</h3>
<p>Tracking happens <strong>at the network level</strong>, independent of the browser or device, and
survives clearing cookies or private browsing. It relies on consent, but that consent is often requested
through ambiguous banners, sometimes as “consent or pay”.</p>
<h3 class="pix">Methodology</h3>
<p>The index cross-references public signals: DNS records pointing to Utiq infrastructure
(<code>*.utiq-aws.net</code>), TLS certificates for <code>utiq.&lt;site&gt;</code> subdomains
(Certificate Transparency logs), and a check that the Utiq <em>loader</em> responds on the domain. To
date, <strong>{n_total} sites</strong> are listed, including <strong>{n_fr} in France</strong>. The
“Utiq since” date is estimated from the earliest known public trace.</p>
<p><strong>Non-exhaustive list, subject to change.</strong> Found an error? A site to report? Contact
<a href="{SOCIAL['site']}" target="_blank" rel="noopener">Christophe Boutry</a>.</p>
<h3 class="pix">Opt out / protect yourself</h3>
<p>See the <a href="/en/faq.html">FAQ</a>: opt out via the
<a href="{CONSENT_HUB}" target="_blank" rel="noopener">Utiq Consent Hub</a> and downloadable DNS blocklists.</p>
"""
    out = head(t, f"{t['about_title']} — Utiq Tracker", t["meta_desc"], "about", lang)
    out += header(t, lang, "about")
    out += f"""<main><section class="page wrap prose">
<h1 class="pix">{t['about_title'].replace('Utiq','<b>Utiq</b>')}</h1>
{body}
<p><a href="{'/' if lang=='fr' else '/en/'}">{t['back_home']}</a></p>
</section></main>"""
    out += footer(t, lang)
    return out


def render_api(t, lang, n_total):
    path = ("/api/" if lang == "fr" else "/en/api/")
    ex = "https://utiq-tracker.online/api/v1/sites.json"
    if lang == "fr":
        intro = ("Les données d’Utiq Tracker sont librement réutilisables (licence "
                 "<a href=\"https://creativecommons.org/licenses/by/4.0/deed.fr\" target=\"_blank\" rel=\"noopener\">CC BY 4.0</a>, "
                 "merci de créditer « Utiq Tracker »). L’endpoint ci-dessous est stable, en lecture seule, "
                 "servi avec l’en-tête <code>Access-Control-Allow-Origin: *</code> (CORS) pour un usage direct "
                 "depuis le navigateur.")
        fields = "Champs"
        notes = (f"<p>Le jeu de données contient <strong>{n_total} entrées</strong>. Réponse&nbsp;: un objet "
                 "<code>meta</code> (génération, total, source, licence) + un tableau <code>sites</code>. "
                 "Mise à jour ponctuelle. <strong>Liste non exhaustive.</strong></p>")
        endp = "Endpoint stable"
    else:
        intro = ("Utiq Tracker data is freely reusable (license "
                 "<a href=\"https://creativecommons.org/licenses/by/4.0/\" target=\"_blank\" rel=\"noopener\">CC BY 4.0</a>, "
                 "please credit “Utiq Tracker”). The endpoint below is stable, read-only, and served with the "
                 "<code>Access-Control-Allow-Origin: *</code> header (CORS) for direct use from the browser.")
        fields = "Fields"
        notes = (f"<p>The dataset holds <strong>{n_total} entries</strong>. Response: a <code>meta</code> object "
                 "(generation, total, source, license) + a <code>sites</code> array. Updated occasionally. "
                 "<strong>Non-exhaustive list.</strong></p>")
        endp = "Stable endpoint"
    flist = """<table class="apitbl">
<tr><td><code>domain</code></td><td>FQDN</td></tr>
<tr><td><code>name</code></td><td>Site name / title</td></tr>
<tr><td><code>url</code></td><td>Canonical URL</td></tr>
<tr><td><code>description</code></td><td>Short description (native language)</td></tr>
<tr><td><code>category</code></td><td>Category key (general, news, sport, …)</td></tr>
<tr><td><code>country</code></td><td>ISO code (FR, DE, ES, GB, INT, …)</td></tr>
<tr><td><code>scope</code></td><td><code>fr</code> or <code>world</code></td></tr>
<tr><td><code>utiq_since</code></td><td>Estimated first-seen date (YYYY-MM-DD)</td></tr>
<tr><td><code>loader_confirmed</code></td><td>Utiq loader responded (bool)</td></tr>
</table>"""
    curl = (f'<span class="k">$</span> curl -s {ex}\n'
            f'<span class="k">$</span> curl -s {ex} | jq \'.sites[] | select(.scope=="fr")\'')
    out = head(t, f"{t['api_title']} — Utiq Tracker", t["meta_desc"], "api", lang)
    out += header(t, lang, "api")
    out += f"""<main><section class="page wrap prose">
<h1 class="pix">{t['api_title'].replace('JSON','<b>JSON</b>')}</h1>
<p class="lead">{intro}</p>
<h3 class="pix">{endp}</h3>
<p><a class="btn orange" href="/api/v1/sites.json">⚡ /api/v1/sites.json</a>
&nbsp;<a class="btn" href="/data/utiq-sites.csv" download>⬇ CSV</a></p>
{notes}
<div class="codeblock"><pre>{curl}</pre></div>
<h3 class="pix">{fields}</h3>
{flist}
<p><a href="{'/' if lang=='fr' else '/en/'}">{t['back_home']}</a></p>
</section></main>
<style>.apitbl{{border-collapse:collapse;width:100%;font-size:13.5px}}.apitbl td{{border:2px solid var(--ink);padding:6px 10px}}.apitbl td:first-child{{white-space:nowrap;width:1%;background:var(--cream)}}</style>"""
    out += footer(t, lang)
    return out


def render_legal(t, lang):
    path = ("/mentions-legales.html" if lang == "fr" else "/en/legal-notice.html")
    if lang == "fr":
        title = "Mentions légales"
        body = """
<h3 class="pix">Éditeur du site</h3>
<p>Le site <strong>utiq-tracker.online</strong> est édité par <strong>Christophe Boutry</strong>,
domicilié à Paris (75012), France. Contact&nbsp;: via <a href="https://christopheboutry.com" target="_blank" rel="noopener">christopheboutry.com</a>.</p>
<h3 class="pix">Directeur de la publication</h3>
<p>Christophe Boutry.</p>
<h3 class="pix">Hébergement</h3>
<p>Le site est hébergé sur un serveur dédié OVH&nbsp;SAS, 2 rue Kellermann, 59100 Roubaix, France
(<a href="https://www.ovhcloud.com" target="_blank" rel="noopener">ovhcloud.com</a>).</p>
<h3 class="pix">Objet et indépendance</h3>
<p>Utiq Tracker est un projet indépendant, à vocation informative, qui recense des sites web utilisant la
technologie Utiq à partir de signaux techniques publics. <strong>Ce site n’a aucun lien avec Utiq SA/NV,
ses opérateurs fondateurs (Deutsche Telekom, Orange, Telefónica, Vodafone) ni aucune des marques citées.</strong>
Les marques et noms cités appartiennent à leurs propriétaires respectifs. La liste est non exhaustive et
susceptible d’évoluer&nbsp;; elle est fournie sans garantie d’exactitude.</p>
<h3 class="pix">Propriété intellectuelle</h3>
<p>La structure du site, ses textes originaux et son code sont la propriété de l’éditeur. Les données du
référencement sont mises à disposition sous licence <a href="https://creativecommons.org/licenses/by/4.0/deed.fr" target="_blank" rel="noopener">CC BY 4.0</a>.</p>
<h3 class="pix">Données personnelles &amp; cookies</h3>
<p>Ce site ne dépose <strong>aucun cookie de pistage</strong> et ne collecte aucune donnée personnelle
identifiable. Aucun traceur tiers n’est chargé&nbsp;; les favicons sont hébergés localement et aucune police web externe n’est chargée (typographie système).
Le traitement éventuel de données est régi par le RGPD (règlement UE 2016/679).</p>
<h3 class="pix">Signalement</h3>
<p>Pour signaler une erreur ou demander un retrait, contactez l’éditeur via
<a href="https://christopheboutry.com" target="_blank" rel="noopener">christopheboutry.com</a>.</p>
"""
    else:
        title = "Legal notice"
        body = """
<h3 class="pix">Publisher</h3>
<p>The site <strong>utiq-tracker.online</strong> is published by <strong>Christophe Boutry</strong>,
based in Paris (75012), France. Contact: via <a href="https://christopheboutry.com" target="_blank" rel="noopener">christopheboutry.com</a>.</p>
<h3 class="pix">Publication director</h3>
<p>Christophe Boutry.</p>
<h3 class="pix">Hosting</h3>
<p>The site is hosted on a dedicated OVH SAS server, 2 rue Kellermann, 59100 Roubaix, France
(<a href="https://www.ovhcloud.com" target="_blank" rel="noopener">ovhcloud.com</a>).</p>
<h3 class="pix">Purpose and independence</h3>
<p>Utiq Tracker is an independent, informational project that lists websites using the Utiq technology
based on public technical signals. <strong>This site is not affiliated with Utiq SA/NV, its founding
operators (Deutsche Telekom, Orange, Telefónica, Vodafone), or any of the brands mentioned.</strong>
Trademarks and names belong to their respective owners. The list is non-exhaustive, subject to change,
and provided without warranty of accuracy.</p>
<h3 class="pix">Intellectual property</h3>
<p>The site structure, original texts and code belong to the publisher. The index data is made available
under the <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a> license.</p>
<h3 class="pix">Personal data &amp; cookies</h3>
<p>This site sets <strong>no tracking cookies</strong> and collects no identifiable personal data. No
third-party tracker is loaded; favicons are self-hosted and no external web font is loaded (system typography). Any data processing is governed by the
GDPR (EU regulation 2016/679).</p>
<h3 class="pix">Reporting</h3>
<p>To report an error or request removal, contact the publisher via
<a href="https://christopheboutry.com" target="_blank" rel="noopener">christopheboutry.com</a>.</p>
"""
    out = head(t, f"{title} — Utiq Tracker", title + " — Utiq Tracker", "legal", lang)
    out += header(t, lang, "legal")
    out += f"""<main><section class="page wrap prose">
<h1 class="pix">{title}</h1>
{body}
<p><a href="{'/' if lang=='fr' else '/en/'}">{t['back_home']}</a></p>
</section></main>"""
    out += footer(t, lang)
    return out


# ---------------------------------------------------------------------------
# 4. Données publiques (JSON / CSV / API)
# ---------------------------------------------------------------------------
def public_record(r):
    return {
        "domain": r["domain"], "name": r["name"], "url": r["url"],
        "description": r["description"], "category": r["cat_key"],
        "country": r["country_code"], "scope": r["region"],
        "utiq_since": r["since"] or None, "loader_confirmed": r["confirmed"],
    }


def write_data(recs):
    os.makedirs(os.path.join(PUB, "data"), exist_ok=True)
    os.makedirs(os.path.join(PUB, "api", "v1"), exist_ok=True)
    sites = [public_record(r) for r in recs]
    meta = {
        "name": "Utiq Tracker", "source": SITE,
        "description": "Websites and platforms using Utiq (telco advertising tracker). Non-exhaustive.",
        "generated_at": GEN_AT, "count": len(sites),
        "count_france": sum(1 for r in recs if r["region"] == "fr"),
        "non_exhaustive": True, "license": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": "Utiq Tracker — christopheboutry.com",
    }
    payload = {"meta": meta, "sites": sites}
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    open(os.path.join(PUB, "data", "utiq-sites.json"), "w", encoding="utf-8").write(blob)
    open(os.path.join(PUB, "api", "v1", "sites.json"), "w", encoding="utf-8").write(blob)
    # CSV
    with open(os.path.join(PUB, "data", "utiq-sites.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "name", "url", "description", "category", "country", "scope", "utiq_since", "loader_confirmed"])
        for s in sites:
            w.writerow([s["domain"], s["name"], s["url"], s["description"], s["category"],
                        s["country"], s["scope"], s["utiq_since"] or "", s["loader_confirmed"]])
    return meta


# ---------------------------------------------------------------------------
# 5. Assets divers (favicon SVG, OG image, robots, sitemap)
# ---------------------------------------------------------------------------
def write_favicon_svg():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="10" fill="#e8590c"/>'
           '<rect x="6" y="6" width="52" height="52" rx="7" fill="none" stroke="#1b1a17" stroke-width="4"/>'
           '<text x="32" y="44" font-family="monospace" font-size="34" font-weight="700" '
           'text-anchor="middle" fill="#fff">U</text></svg>')
    open(os.path.join(PUB, "assets", "favicon.svg"), "w", encoding="utf-8").write(svg)


def write_og(n_total, n_fr):
    try:
        from PIL import Image, ImageDraw, ImageFont
        W, H = 1200, 630
        img = Image.new("RGB", (W, H), "#f3ead4")
        d = ImageDraw.Draw(img)
        for y in range(0, H, 8):
            for x in range(0, W, 8):
                d.point((x, y), fill="#e7dcc0")
        ttf = os.path.join(BUILD, "silkscreen.ttf")
        if not os.path.exists(ttf):
            try:
                r = requests.get("https://github.com/google/fonts/raw/main/ofl/silkscreen/Silkscreen-Bold.ttf",
                                 headers=UA, timeout=20)
                if r.status_code == 200:
                    open(ttf, "wb").write(r.content)
            except Exception:
                pass
        def font(sz):
            try:
                return ImageFont.truetype(ttf, sz)
            except Exception:
                return ImageFont.load_default()
        d.rectangle([0, 0, W, 14], fill="#e8590c")
        d.rectangle([60, 70, 150, 160], fill="#e8590c", outline="#1b1a17", width=6)
        d.text((84, 92), "U", font=font(56), fill="#ffffff")
        d.text((175, 78), "UTIQ", font=font(64), fill="#1b1a17")
        d.text((175, 150), "TRACKER", font=font(64), fill="#e8590c")
        d.text((62, 250), "Sites & plateformes", font=font(34), fill="#1b1a17")
        d.text((62, 300), "qui utilisent Utiq", font=font(34), fill="#1b1a17")
        d.rectangle([62, 380, 742, 470], fill="#1b1a17")
        d.text((84, 408), f"{n_total} SITES  /  {n_fr} EN FRANCE", font=font(24), fill="#f3ead4")
        d.text((62, 560), "utiq-tracker.online", font=font(28), fill="#c2470a")
        img.save(os.path.join(PUB, "assets", "og.png"))
        img.resize((180, 180)).save(os.path.join(PUB, "assets", "icon-180.png"))
        print("  OG image générée")
    except Exception as e:
        print("  OG image: skip (", e, ")")


def write_seo():
    open(os.path.join(PUB, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)
    urls = ["/", "/faq.html", "/a-propos.html", "/mentions-legales.html", "/api/",
            "/en/", "/en/faq.html", "/en/about.html", "/en/legal-notice.html", "/en/api/"]
    items = ""
    for u in urls:
        items += (f'<url><loc>{SITE}{u}</loc><lastmod>{GEN_AT[:10]}</lastmod>'
                  f'<changefreq>weekly</changefreq></url>\n')
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + items + '</urlset>\n')
    open(os.path.join(PUB, "sitemap.xml"), "w", encoding="utf-8").write(sm)


# ---------------------------------------------------------------------------
# 6. Orchestration
# ---------------------------------------------------------------------------
def build_selects(recs, t):
    # catégories présentes triées par label localisé
    seen = {}
    for r in recs:
        seen.setdefault(r["cat_key"], (r["category_fr"] if t["lang"] == "fr" else r["category_en"]))
    cats = sorted(seen.items(), key=lambda kv: strip(kv[1]))
    cat_opts = f'<option value="all">{t["cat_all"]}</option>' + "".join(
        f'<option value="{k}">{html.escape(v)}</option>' for k, v in cats)
    # pays présents avec compte + drapeau
    cc = {}
    for r in recs:
        cc.setdefault(r["country_code"], [r["flag"], (r["country_fr"] if t["lang"] == "fr" else r["country_en"]), 0])
        cc[r["country_code"]][2] += 1
    countries = sorted(cc.items(), key=lambda kv: -kv[1][2])
    country_opts = f'<option value="all">{t["country_all"]}</option>' + "".join(
        f'<option value="{code}">{flag} {html.escape(name)} ({n})</option>'
        for code, (flag, name, n) in countries)
    return cat_opts, country_opts


def main():
    print("· chargement des données")
    recs = load_records()
    n_total = len(recs)
    n_fr = sum(1 for r in recs if r["region"] == "fr")
    print(f"  {n_total} sites ({n_fr} France / {n_total - n_fr} monde)")

    print("· favicons")
    have = fetch_all_favicons(recs)
    for r in recs:
        r["_fav"] = have.get(r["domain"], False)

    # reset public/ : on vide le contenu sans supprimer le dossier lui-même,
    # pour préserver l'inode du bind-mount Docker (sinon le conteneur nginx sert
    # un dossier fantôme tant qu'on ne le redémarre pas).
    os.makedirs(PUB, exist_ok=True)
    for entry in os.listdir(PUB):
        q = os.path.join(PUB, entry)
        shutil.rmtree(q) if os.path.isdir(q) else os.remove(q)
    os.makedirs(os.path.join(PUB, "assets", "favicons"), exist_ok=True)
    os.makedirs(os.path.join(PUB, "en"), exist_ok=True)
    os.makedirs(os.path.join(PUB, "blocklists"), exist_ok=True)

    print("· assets")
    shutil.copy(os.path.join(STATIC, "style.css"), os.path.join(PUB, "assets", "style.css"))
    shutil.copy(os.path.join(STATIC, "app.js"), os.path.join(PUB, "assets", "app.js"))
    for r in recs:
        if r["_fav"]:
            shutil.copy(os.path.join(CACHE, safe(r["domain"]) + ".png"),
                        os.path.join(PUB, "assets", "favicons", safe(r["domain"]) + ".png"))
    # blocklists
    for f in os.listdir(BLOCK):
        shutil.copy(os.path.join(BLOCK, f), os.path.join(PUB, "blocklists", f))

    print("· données publiques (JSON/CSV/API)")
    write_data(recs)
    write_favicon_svg()
    write_og(n_total, n_fr)
    write_seo()

    print("· rendu HTML")
    for lang in ("fr", "en"):
        t = UI[lang]
        cat_opts, country_opts = build_selects(recs, t)
        idx = render_index(t, recs, None, country_opts, cat_opts, lang)
        sub = "" if lang == "fr" else "en"
        def w(name, content):
            p = os.path.join(PUB, sub, name) if sub else os.path.join(PUB, name)
            open(p, "w", encoding="utf-8").write(content)
        w("index.html", idx)
        w("faq.html", render_faq(t, lang))
        w("about.html" if lang == "en" else "a-propos.html", render_about(t, lang, n_total, n_fr))
        w("legal-notice.html" if lang == "en" else "mentions-legales.html", render_legal(t, lang))
        os.makedirs(os.path.join(PUB, sub, "api") if sub else os.path.join(PUB, "api"), exist_ok=True)
        api_p = os.path.join(PUB, sub, "api", "index.html") if sub else os.path.join(PUB, "api", "index.html")
        open(api_p, "w", encoding="utf-8").write(render_api(t, lang, n_total))

    # page 404 (FR, autonome)
    t = UI["fr"]
    p404 = head(t, "404 — Utiq Tracker", "Page introuvable.", "list", "fr")
    p404 += header(t, "fr", "list")
    p404 += ('<main><section class="page wrap" style="text-align:center;padding:80px 0">'
             '<h2 class="pix" style="font-size:48px;color:#e8590c">404</h2>'
             '<p class="lead">Cette page n’existe pas (ou plus).</p>'
             '<p><a class="btn orange" href="/">← Retour à l’accueil</a></p></section></main>')
    p404 += footer(t, "fr")
    open(os.path.join(PUB, "404.html"), "w", encoding="utf-8").write(p404)

    print(f"✓ build terminé → {PUB}")


if __name__ == "__main__":
    main()
