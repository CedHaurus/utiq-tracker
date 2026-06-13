#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur statique multilingue d'Utiq Tracker à partir de data/source.json.

Le français est servi à la racine, les autres langues sous /<lang>/.
Le contenu de chaque langue est dans build/i18n/<lang>.json (voir content.py).
"""
import json, csv, os, re, shutil, html, hashlib, unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests

from maps import CAT_KEY, CAT_FALLBACK, COUNTRY_META, COUNTRY_FALLBACK
from content import SOCIAL, CONSENT_HUB, LANG_NAMES, LANG_LOCALE, load_content

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD  = os.path.join(ROOT, "build")
STATIC = os.path.join(BUILD, "static")
PUB    = os.path.join(ROOT, "public")
CACHE  = os.path.join(BUILD, "favicons_cache")
SRC    = os.path.join(ROOT, "data", "source.json")
BLOCK  = os.path.join(ROOT, "blocklists")
SITE   = "https://utiq-tracker.online"

CONTENT = load_content()
LANGS = list(CONTENT.keys())            # langues effectivement disponibles (JSON présent)

GEN_AT = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
YEAR   = datetime.now(timezone.utc).year

# Slugs de page (mêmes noms de fichiers dans toutes les langues)
PAGE_SLUG = {"list": "/", "faq": "/faq.html", "about": "/about.html",
             "legal": "/legal.html", "api": "/api/"}
PAGES = ["list", "faq", "about", "legal", "api"]

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
MONO_COLORS = ["#e8590c", "#1b1a17", "#0b7285", "#5f3dc4", "#a61e4d", "#2b8a3e", "#9c6644", "#1864ab"]


def _asset_ver():
    h = hashlib.md5()
    for f in ("style.css", "app.js"):
        h.update(open(os.path.join(STATIC, f), "rb").read())
    return h.hexdigest()[:8]
ASSET_VER = _asset_ver()
OG_VER = "1"


def base(lang):
    return "" if lang == "fr" else "/" + lang


def page_url(page, lang):
    return base(lang) + PAGE_SLUG[page]


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


def subst(text, lang, n_total=None, n_fr=None):
    """Remplace les placeholders de liens/comptes dans un contenu HTML traduit.

    Les contenus i18n utilisent {faq} {about} {api} {legal} {consent} {site}
    {blocklists} {data_json} {data_csv} {n} {fr} pour rester corrects par langue.
    """
    if not text:
        return text
    repl = {
        "{faq}": page_url("faq", lang),
        "{about}": page_url("about", lang),
        "{api}": page_url("api", lang),
        "{legal}": page_url("legal", lang),
        "{home}": page_url("list", lang),
        "{consent}": CONSENT_HUB,
        "{site}": SOCIAL["site"],
        "{blocklists}": "/blocklists/",
        "{data_json}": "/data/utiq-sites.json",
        "{data_csv}": "/data/utiq-sites.csv",
    }
    if n_total is not None:
        repl["{n}"] = str(n_total)
    if n_fr is not None:
        repl["{fr}"] = str(n_fr)
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


# ---------------------------------------------------------------------------
# 1. Normalisation des données (langue-neutre : clés + codes + drapeaux)
# ---------------------------------------------------------------------------
def load_records():
    data = json.load(open(SRC, encoding="utf-8"))
    recs = []
    for d in data["detections"]:
        domain = d["domain"]
        name = (d.get("site_name") or domain).strip()
        url = d.get("final_url") or f"https://{domain}/"
        desc = (d.get("description") or "").strip()
        cat_key = CAT_KEY.get(d.get("category") or "", CAT_FALLBACK)
        code, flag = COUNTRY_META.get(d.get("country") or "", COUNTRY_FALLBACK)
        recs.append({
            "domain": domain, "name": name, "url": url,
            "description": desc, "desc_card": truncate(desc),
            "cat_key": cat_key, "country_code": code, "flag": flag,
            "region": "fr" if code == "FR" else "world",
            "since": d.get("estimated_date") or "",
            "confirmed": bool(d.get("loader_confirmed")),
            "search": strip(f"{name} {domain} {desc}"),
        })
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
# 3. Briques HTML communes
# ---------------------------------------------------------------------------
def head(t, title, desc, page, lang, og=None, extra=""):
    if og is None:
        og = "/assets/og.png" if lang == "fr" else f"/assets/og-{lang}.png"
    canonical = SITE + page_url(page, lang)
    alts = "".join(
        f'<link rel="alternate" hreflang="{l}" href="{SITE}{page_url(page, l)}">\n'
        for l in LANGS)
    alts += f'<link rel="alternate" hreflang="x-default" href="{SITE}{page_url(page, "fr")}">\n'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
{alts}<meta property="og:type" content="website">
<meta property="og:site_name" content="Utiq Tracker">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}{og}?v={OG_VER}">
<meta property="og:locale" content="{LANG_LOCALE.get(lang, 'en_GB')}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{SITE}{og}?v={OG_VER}">
<meta name="theme-color" content="#e8590c">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="stylesheet" href="/assets/style.css?v={ASSET_VER}">
{extra}</head>
<body>"""


def lang_menu(active, lang):
    items = "".join(
        f'<a href="{page_url(active, l)}" data-lang="{l}"'
        f'{" aria-current=\"true\"" if l == lang else ""}>{LANG_NAMES[l]}</a>'
        for l in LANGS)
    return (f'<details class="langmenu"><summary>🌐 <span>{lang.upper()}</span></summary>'
            f'<div class="langmenu-list">{items}</div></details>')


def header(t, lang, active):
    u = t["ui"]
    b = base(lang)
    def link(href, label, key, cta=False):
        cls = ' class="cta"' if cta else (' aria-current="page"' if key == active else "")
        ext = ' target="_blank" rel="noopener"' if href.startswith("http") else ""
        return f'<a href="{href}"{cls}{ext}>{label}</a>'
    nav = "".join([
        link(page_url("list", lang), u["nav_list"], "list"),
        link(page_url("faq", lang), u["nav_faq"], "faq"),
        link(page_url("about", lang), u["nav_about"], "about"),
        link(CONSENT_HUB, u["nav_optout"], "optout", cta=True),
    ])
    return f"""<header class="site-header"><div class="wrap hbar">
<a class="brand" href="{b}/"><span class="logo-mark"><span>U</span></span>
<span class="brand-name">Utiq <b>Tracker</b></span></a>
<nav class="nav">{nav}{lang_menu(active, lang)}</nav></div></header>"""


def footer(t, lang):
    u = t["ui"]
    x_svg = '<svg viewBox="0 0 24 24"><path d="M18.9 1.6h3.5l-7.6 8.7 9 11.9h-7L11.7 15l-6.3 7.2H1.9l8.1-9.3L1.3 1.6h7.1l4.7 6.2 5.8-6.2zm-1.2 18.7h1.9L7.1 3.6H5z"/></svg>'
    gh_svg = '<svg viewBox="0 0 24 24"><path d="M12 .5C5.4.5 0 5.9 0 12.6c0 5.3 3.4 9.8 8.2 11.4.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1.1-.8.1-.8.1-.8 1.2.1 1.9 1.3 1.9 1.3 1.1 1.9 2.9 1.4 3.6 1 .1-.8.4-1.4.8-1.7-2.7-.3-5.5-1.4-5.5-6 0-1.3.5-2.4 1.3-3.2-.1-.3-.6-1.6.1-3.3 0 0 1-.3 3.3 1.2a11.5 11.5 0 016 0C17.3 4.7 18.3 5 18.3 5c.7 1.7.2 3 .1 3.3.8.8 1.3 1.9 1.3 3.2 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.8-1.6 8.2-6.1 8.2-11.4C24 5.9 18.6.5 12 .5z"/></svg>'
    return f"""<footer class="site-footer">
<div class="wrap foot">
<div class="links">
<a href="{page_url('legal', lang)}">{u['footer_legal']}</a>
<span>·</span>
<span>{u['footer_by']} <a href="{SOCIAL['site']}" target="_blank" rel="noopener">Christophe Boutry</a></span>
</div>
<div class="social">
<a href="{SOCIAL['x']}" target="_blank" rel="noopener" aria-label="X">{x_svg}</a>
<a href="{SOCIAL['github']}" target="_blank" rel="noopener" aria-label="GitHub">{gh_svg}</a>
</div>
<p class="disc"><span class="ne">{html.escape(u['non_exhaustive'])}</span>{html.escape(u['disclaimer'])}
&nbsp;© {YEAR} Christophe Boutry.</p>
</div></footer>
<script src="/assets/app.js?v={ASSET_VER}" defer></script>
</body></html>"""


def card_html(r, t, hidden=False):
    u = t["ui"]
    if r["_fav"]:
        ico = f'<img loading="lazy" width="38" height="38" src="/assets/favicons/{safe(r["domain"])}.png" alt="">'
    else:
        color = MONO_COLORS[int(hashlib.md5(r["domain"].encode()).hexdigest(), 16) % len(MONO_COLORS)]
        ico = f'<span class="mono" style="background:{color}">{html.escape(r["name"][:1].upper() or "?")}</span>'
    cat = t["categories"].get(r["cat_key"], r["cat_key"])
    country = t["countries"].get(r["country_code"], r["country_code"])
    since = f'<span class="tag since">{u["card_since"]} {r["since"][:4]}</span>' if r["since"] else ""
    desc = f'<p class="card-desc">{html.escape(r["desc_card"])}</p>' if r["desc_card"] else ""
    hid = " hidden" if hidden else ""
    return f"""<article class="card has-go"{hid} data-search="{html.escape(r['search'])}" data-region="{r['region']}" data-cat="{r['cat_key']}" data-country="{r['country_code']}">
<div class="card-ico">{ico}</div>
<div class="card-body">
<h3 class="card-title" title="{html.escape(r['name'])}">{html.escape(r['name'])}</h3>
<a class="card-url" href="{html.escape(r['url'])}" target="_blank" rel="noopener noreferrer nofollow">{html.escape(r['domain'])}</a>
{desc}
<div class="card-meta"><span class="tag flag" title="{html.escape(country)}">{r['flag']}</span><span class="tag cat">{html.escape(cat)}</span>{since}</div>
</div>
<a class="card-go" href="{html.escape(r['url'])}" target="_blank" rel="noopener noreferrer nofollow" aria-label="{html.escape(u['card_go'])}: {html.escape(r['name'])}">→</a>
</article>"""


# ---------------------------------------------------------------------------
# 4. Pages
# ---------------------------------------------------------------------------
def render_index(t, lang, recs, country_opts, cat_opts, redirect_js):
    u = t["ui"]
    b = base(lang)
    title = f"Utiq Tracker — {t['tagline']}"
    redirect = redirect_js if lang == "fr" else ""
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": "Utiq Tracker", "url": SITE,
             "inLanguage": lang, "description": t["meta_desc"],
             "potentialAction": {"@type": "SearchAction",
                                 "target": SITE + b + "/?q={search_term_string}",
                                 "query-input": "required name=search_term_string"}},
            {"@type": "Dataset", "name": "Utiq Tracker",
             "description": t["meta_desc"], "url": SITE + page_url("list", lang),
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
    seg = (f'<button data-scope="all" aria-pressed="true">{u["scope_all"]}</button>'
           f'<button data-scope="fr">🇫🇷 {u["scope_fr"]}</button>'
           f'<button data-scope="world">🌍 {u["scope_world"]}</button>')
    out = head(t, title, t["meta_desc"], "list", lang, extra=redirect + ld_s)
    out += header(t, lang, "list")
    out += f"""<main>
<section class="hero"><div class="wrap">
<h1 class="hero-title">Utiq <span>Tracker</span></h1>
<p class="tagline">{html.escape(t['tagline'])} <span class="slogan-inline">{html.escape(t['slogan'])}</span></p>
<div class="intro">{t['intro_html']} <a href="{page_url('about', lang)}">{html.escape(u['learn_more'])} →</a></div>
</div></section>

<section class="toolbar"><div class="wrap tb">
<div class="tb-top">
<label class="search"><span>🔎</span><input id="q" type="search" placeholder="{html.escape(u['search_ph'])}" aria-label="{html.escape(u['search_ph'])}"></label>
<div class="dl-group"><span class="lbl">{u['downloads']} :</span>
<a class="btn" href="/data/utiq-sites.json" download>⬇ {u['dl_json']}</a>
<a class="btn" href="/data/utiq-sites.csv" download>⬇ {u['dl_csv']}</a>
<a class="btn orange" href="{page_url('api', lang)}">⚡ {u['api_link']}</a>
</div>
</div>
<div class="tb-filters">
<div class="segmented" role="group" aria-label="{html.escape(u['filter_scope'])}">{seg}</div>
<select id="f-cat" aria-label="{html.escape(u['filter_cat'])}">{cat_opts}</select>
<select id="f-country" aria-label="{html.escape(u['filter_country'])}">{country_opts}</select>
<button class="btn ghost" id="reset">↺ {u['reset']}</button>
</div>
<div class="tb-count"><span class="count"><b id="count-n">{len(recs)}</b> <span id="count-l">{u['results_many']}</span></span></div>
</div></section>

<section class="wrap"><div class="grid" id="grid">
{cards}
</div>
<div class="empty" id="empty">{html.escape(u['no_results'])}</div>
<div class="more-wrap" id="more-wrap"><button class="btn orange" id="more" data-tpl="{html.escape(u['see_more_rest'])}">{u['see_more']}</button></div>
</section>
</main>"""
    out += footer(t, lang)
    return out


def render_faq(t, lang):
    u = t["ui"]
    items = t["faq"]
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", " ", a)}}
                         for q, a in items]}
    ld_s = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    qa = "\n".join(
        f'<details class="qa"{" open" if i == 0 else ""}><summary>{html.escape(q)}</summary><div class="a">{subst(a, lang)}</div></details>'
        for i, (q, a) in enumerate(items))
    out = head(t, f"{u['faq_title']} — Utiq Tracker", u["faq_intro"], "faq", lang, extra=ld_s)
    out += header(t, lang, "faq")
    out += f"""<main><section class="page wrap">
<h1 class="pix">{html.escape(u['faq_title'])}</h1>
<p class="lead">{html.escape(u['faq_intro'])}</p>
{qa}
</section></main>"""
    out += footer(t, lang)
    return out


def render_about(t, lang, n_total, n_fr):
    u = t["ui"]
    body = subst(t["about_html"], lang, n_total, n_fr)
    out = head(t, f"{u['about_title']} — Utiq Tracker", t["meta_desc"], "about", lang)
    out += header(t, lang, "about")
    out += f"""<main><section class="page wrap prose">
<h1 class="pix">{html.escape(u['about_title'])}</h1>
{body}
<p><a href="{page_url('list', lang)}">{html.escape(u['back_home'])}</a></p>
</section></main>"""
    out += footer(t, lang)
    return out


def render_api(t, lang, n_total):
    u = t["ui"]
    a = t["api"]
    ex = "https://utiq-tracker.online/api/v1/sites.json"
    intro_html = subst(a["intro_html"], lang)
    notes = subst(a["notes_html"], lang, n_total)
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
    out = head(t, f"{u['api_title']} — Utiq Tracker", t["meta_desc"], "api", lang)
    out += header(t, lang, "api")
    out += f"""<main><section class="page wrap prose">
<h1 class="pix">{html.escape(u['api_title'])}</h1>
<p class="lead">{intro_html}</p>
<h3 class="pix">{html.escape(a['endpoint_label'])}</h3>
<p><a class="btn orange" href="/api/v1/sites.json">⚡ /api/v1/sites.json</a>
&nbsp;<a class="btn" href="/data/utiq-sites.csv" download>⬇ CSV</a></p>
{notes}
<div class="codeblock"><pre>{curl}</pre></div>
<h3 class="pix">{html.escape(a['fields_label'])}</h3>
{flist}
<p><a href="{page_url('list', lang)}">{html.escape(u['back_home'])}</a></p>
</section></main>
<style>.apitbl{{border-collapse:collapse;width:100%;font-size:13.5px}}.apitbl td{{border:2px solid var(--ink);padding:6px 10px}}.apitbl td:first-child{{white-space:nowrap;width:1%;background:var(--cream)}}</style>"""
    out += footer(t, lang)
    return out


def render_legal(t, lang):
    u = t["ui"]
    title = t["legal"]["title"]
    out = head(t, f"{title} — Utiq Tracker", title + " — Utiq Tracker", "legal", lang)
    out += header(t, lang, "legal")
    out += f"""<main><section class="page wrap prose">
<h1 class="pix">{html.escape(title)}</h1>
{subst(t['legal']['html'], lang)}
<p><a href="{page_url('list', lang)}">{html.escape(u['back_home'])}</a></p>
</section></main>"""
    out += footer(t, lang)
    return out


# ---------------------------------------------------------------------------
# 5. Données publiques (JSON / CSV / API)
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
    with open(os.path.join(PUB, "data", "utiq-sites.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["domain", "name", "url", "description", "category", "country", "scope", "utiq_since", "loader_confirmed"])
        for s in sites:
            w.writerow([s["domain"], s["name"], s["url"], s["description"], s["category"],
                        s["country"], s["scope"], s["utiq_since"] or "", s["loader_confirmed"]])


# ---------------------------------------------------------------------------
# 6. Assets (favicon SVG, OG images par langue, robots, sitemap)
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
        cream, ink, orange, orange_d = "#f3ead4", "#1b1a17", "#e8590c", "#c2470a"
        FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
        FI = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-BoldOblique.ttf"
        def fb(sz):
            try: return ImageFont.truetype(FB, sz)
            except Exception: return ImageFont.load_default()
        def fi(sz):
            try: return ImageFont.truetype(FI, sz)
            except Exception: return ImageFont.load_default()
        def fit(draw, text, font_maker, start, mx):
            sz = start
            while sz > 16 and draw.textlength(text, font=font_maker(sz)) > mx:
                sz -= 1
            return font_maker(sz)
        def render(path, l1, l2, slogan, stat):
            img = Image.new("RGB", (W, H), cream)
            d = ImageDraw.Draw(img)
            for yy in range(26, H, 11):
                for xx in range(26, W, 11):
                    d.point((xx, yy), fill="#e6dabd")
            d.rectangle([0, 0, W, 12], fill=orange)
            M = 72
            mx = W - 2 * M
            d.rounded_rectangle([M, 70, M + 96, 166], radius=12, fill=orange, outline=ink, width=5)
            d.text((M + 48, 118), "U", font=fb(62), fill="#ffffff", anchor="mm")
            tf = fb(70)
            d.text((M + 122, 80), "UTIQ", font=tf, fill=ink)
            d.text((M + 122 + d.textlength("UTIQ ", font=tf), 80), "TRACKER", font=tf, fill=orange)
            f1 = fit(d, l1, fb, 32, mx)
            f2 = fit(d, l2, fb, 32, mx)
            d.text((M, 248), l1, font=f1, fill=ink)
            d.text((M, 292), l2, font=f2, fill=ink)
            d.text((M, 366), slogan, font=fit(d, slogan, fi, 40, mx), fill=orange_d)
            d.line([M, 498, W - M, 498], fill=ink, width=3)
            nf = fb(27)
            d.text((M, 524), stat, font=fit(d, stat, fb, 27, mx - 320), fill=ink)
            ut = "utiq-tracker.online"
            d.text((W - M - d.textlength(ut, font=nf), 524), ut, font=nf, fill=orange_d)
            img.save(path)
        ap = lambda n: os.path.join(PUB, "assets", n)
        for lang in LANGS:
            og = CONTENT[lang]["og"]
            stat = og["stat"].replace("{n}", str(n_total)).replace("{fr}", str(n_fr))
            name = "og.png" if lang == "fr" else f"og-{lang}.png"
            render(ap(name), og["l1"], og["l2"], og["slogan"], stat)
        ic = Image.new("RGB", (180, 180), orange)
        ImageDraw.Draw(ic).text((90, 96), "U", font=fb(120), fill="#ffffff", anchor="mm")
        ic.save(ap("icon-180.png"))
        print(f"  OG images générées ({len(LANGS)} langues)")
    except Exception as e:
        print("  OG image: skip (", e, ")")


def write_seo():
    open(os.path.join(PUB, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)
    items = ""
    for page in PAGES:
        for lang in LANGS:
            loc = SITE + page_url(page, lang)
            alts = "".join(
                f'<xhtml:link rel="alternate" hreflang="{l}" href="{SITE}{page_url(page, l)}"/>'
                for l in LANGS)
            alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{page_url(page, "fr")}"/>'
            items += (f'<url><loc>{loc}</loc>{alts}<lastmod>{GEN_AT[:10]}</lastmod>'
                      f'<changefreq>weekly</changefreq></url>\n')
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + items + '</urlset>\n')
    open(os.path.join(PUB, "sitemap.xml"), "w", encoding="utf-8").write(sm)


# ---------------------------------------------------------------------------
# 7. Sélecteurs (catégories / pays présents, libellés localisés)
# ---------------------------------------------------------------------------
def build_selects(recs, t):
    u = t["ui"]
    seen = {}
    for r in recs:
        seen.setdefault(r["cat_key"], t["categories"].get(r["cat_key"], r["cat_key"]))
    cats = sorted(seen.items(), key=lambda kv: strip(kv[1]))
    cat_opts = f'<option value="all">{u["cat_all"]}</option>' + "".join(
        f'<option value="{k}">{html.escape(v)}</option>' for k, v in cats)
    cc = {}
    for r in recs:
        cc.setdefault(r["country_code"], [r["flag"], t["countries"].get(r["country_code"], r["country_code"]), 0])
        cc[r["country_code"]][2] += 1
    countries = sorted(cc.items(), key=lambda kv: -kv[1][2])
    country_opts = f'<option value="all">{u["country_all"]}</option>' + "".join(
        f'<option value="{code}">{flag} {html.escape(name)} ({n})</option>'
        for code, (flag, name, n) in countries)
    return cat_opts, country_opts


# ---------------------------------------------------------------------------
# 8. Orchestration
# ---------------------------------------------------------------------------
def main():
    print(f"· langues disponibles : {', '.join(LANGS)}")
    print("· chargement des données")
    recs = load_records()
    n_total = len(recs)
    n_fr = sum(1 for r in recs if r["region"] == "fr")
    print(f"  {n_total} sites ({n_fr} France / {n_total - n_fr} monde)")

    print("· favicons")
    have = fetch_all_favicons(recs)
    for r in recs:
        r["_fav"] = have.get(r["domain"], False)

    # reset public/ sans supprimer le dossier (inode stable pour le bind-mount Docker)
    os.makedirs(PUB, exist_ok=True)
    for entry in os.listdir(PUB):
        q = os.path.join(PUB, entry)
        shutil.rmtree(q) if os.path.isdir(q) else os.remove(q)
    os.makedirs(os.path.join(PUB, "assets", "favicons"), exist_ok=True)
    os.makedirs(os.path.join(PUB, "blocklists"), exist_ok=True)

    print("· assets")
    shutil.copy(os.path.join(STATIC, "style.css"), os.path.join(PUB, "assets", "style.css"))
    shutil.copy(os.path.join(STATIC, "app.js"), os.path.join(PUB, "assets", "app.js"))
    for r in recs:
        if r["_fav"]:
            shutil.copy(os.path.join(CACHE, safe(r["domain"]) + ".png"),
                        os.path.join(PUB, "assets", "favicons", safe(r["domain"]) + ".png"))
    for f in os.listdir(BLOCK):
        shutil.copy(os.path.join(BLOCK, f), os.path.join(PUB, "blocklists", f))

    print("· données publiques + assets SEO")
    write_data(recs)
    write_favicon_svg()
    write_og(n_total, n_fr)
    global OG_VER
    try:
        OG_VER = hashlib.md5(open(os.path.join(PUB, "assets", "og.png"), "rb").read()).hexdigest()[:8]
    except Exception:
        pass
    write_seo()

    # script de redirection auto (langue navigateur) injecté sur la racine FR
    js_langs = json.dumps(LANGS)
    redirect_js = ("<script>(function(){try{var L=" + js_langs + ";"
                   "var p=localStorage.getItem('utiq-lang');"
                   "var n=(navigator.language||'').slice(0,2).toLowerCase();"
                   "var t=(p&&L.indexOf(p)>=0)?p:(L.indexOf(n)>=0?n:'fr');"
                   "if(t!=='fr'&&location.pathname==='/')location.replace('/'+t+'/');"
                   "}catch(e){}})();</script>")

    print("· rendu HTML")
    for lang in LANGS:
        t = CONTENT[lang]
        sub = "" if lang == "fr" else lang
        outdir = PUB if not sub else os.path.join(PUB, sub)
        os.makedirs(os.path.join(outdir, "api"), exist_ok=True)
        cat_opts, country_opts = build_selects(recs, t)
        write = lambda name, content: open(os.path.join(outdir, name), "w", encoding="utf-8").write(content)
        write("index.html", render_index(t, lang, recs, country_opts, cat_opts, redirect_js))
        write("faq.html", render_faq(t, lang))
        write("about.html", render_about(t, lang, n_total, n_fr))
        write("legal.html", render_legal(t, lang))
        open(os.path.join(outdir, "api", "index.html"), "w", encoding="utf-8").write(render_api(t, lang, n_total))

    # 404 (langue racine = fr si dispo, sinon première langue)
    t404 = CONTENT.get("fr") or CONTENT[LANGS[0]]
    l404 = "fr" if "fr" in CONTENT else LANGS[0]
    u404 = t404["ui"]
    p404 = head(t404, "404 — Utiq Tracker", "Page introuvable.", "list", l404)
    p404 += header(t404, l404, "list")
    p404 += ('<main><section class="page wrap" style="text-align:center;padding:80px 0">'
             '<h2 class="pix" style="font-size:48px;color:#e8590c">404</h2>'
             f'<p class="lead">{html.escape(u404["no_results"])}</p>'
             f'<p><a class="btn orange" href="/">{html.escape(u404["back_home"])}</a></p></section></main>')
    p404 += footer(t404, l404)
    open(os.path.join(PUB, "404.html"), "w", encoding="utf-8").write(p404)

    print(f"✓ build terminé → {PUB}")


if __name__ == "__main__":
    main()
