# Utiq Tracker

An open index of websites and platforms, in France and around the world, that use [Utiq](https://utiq.com).

Live site: https://utiq-tracker.online

Utiq is an advertising tracking technology built by four large European telecom operators (Deutsche Telekom, Orange, Telefónica, Vodafone). Instead of a browser cookie, it identifies people at the network level: your mobile or fixed connection, tied to your phone number or line, is turned into an advertising identifier that follows you across sites, browsers and devices. It is sometimes called the telco super-cookie.

This project lists the sites where Utiq has been detected, explains how it works, and points to the official opt-out. The list is non-exhaustive and changes over time. Anyone can help keep it up to date (see [Contributing](#contributing)).

## Features

- Bilingual static site (French at `/`, English at `/en/`), browser language is auto-detected on first visit
- Full-text search plus filters by scope (France / World), category and country
- One card per site: favicon, name, domain, short description, country flag, estimated first-seen date
- Self-hosted favicons and no external web fonts, so no third-party request is made from a visitor's browser
- FAQ covering what Utiq is, how to opt out through the official Consent Hub, and how to block it (DNS blocklists included)
- Open data: JSON and CSV export, plus a stable JSON API with CORS enabled
- SEO ready: per-page metadata, Open Graph image, JSON-LD (WebSite, Dataset, FAQPage), sitemap and hreflang

## Data and API

The dataset is available three ways:

- JSON download: https://utiq-tracker.online/data/utiq-sites.json
- CSV download: https://utiq-tracker.online/data/utiq-sites.csv
- Stable API endpoint (CORS, read-only): https://utiq-tracker.online/api/v1/sites.json

The API response is an object with a `meta` block and a `sites` array. Each site:

| Field | Description |
|-------|-------------|
| `domain` | Fully qualified domain |
| `name` | Site name or title |
| `url` | Canonical URL |
| `description` | Short description, in the site's own language |
| `category` | Category key (`general`, `news`, `sport`, `tech`, ...) |
| `country` | ISO code (`FR`, `DE`, `ES`, `GB`, `INT`, ...) |
| `scope` | `fr` or `world` |
| `utiq_since` | Estimated first-seen date (`YYYY-MM-DD`) |
| `loader_confirmed` | Whether the Utiq loader responded on the domain |

The data is published under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Please credit "Utiq Tracker".

## How detection works

A site is listed when several public signals line up:

- a DNS record pointing to Utiq infrastructure (`*.utiq-aws.net`)
- a TLS certificate issued for a `utiq.<domain>` subdomain, visible in Certificate Transparency logs
- a check that the Utiq loader actually answers on the domain

The `utiq_since` date is an estimate based on the earliest known public trace (first certificate or first archived copy of the loader). The country is an estimate of the market edition, not a legal headquarters.

## Project layout

```
build/
  build.py        static site generator
  maps.py         category, country and flag tables
  content.py      bilingual UI strings, intro, FAQ, legal text
  static/         style.css, app.js
data/
  source.json     the dataset that drives the build
blocklists/       ready-made DNS/host/adblock lists for blocking Utiq
docker/
  nginx.conf      nginx config used to serve the site
deploy/
  utiq-tracker.caddy   example Caddy vhost (reverse proxy)
compose.yaml      nginx container serving public/
```

The `public/` directory is generated and is not tracked in git.

## Build and run

Requirements: Python 3.10+.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r build/requirements.txt
python build/build.py
```

This reads `data/source.json`, downloads favicons (cached under `build/favicons_cache/`), renders the French and English pages, writes the JSON/CSV/API files and the sitemap, and puts everything in `public/`.

Serve it with any static web server. With Docker:

```bash
docker compose up -d   # serves public/ with nginx on the "edge" network
```

The `edge` network is external in `compose.yaml` because the site sits behind a shared reverse proxy. Drop that and bind a port if you just want to run it standalone.

## Contributing

The list is meant to grow. If you know a site that uses Utiq, or you spot a mistake, please open an issue or a pull request. See [CONTRIBUTING.md](CONTRIBUTING.md) for the entry format and a quick way to verify a site.

## License

Code under the MIT license, dataset under CC BY 4.0. See [LICENSE](LICENSE).

## Disclaimer

This is an independent project. It is not affiliated with Utiq SA/NV, its founding operators, or any of the brands listed. Trademarks belong to their respective owners. The list is provided for informational purposes and without warranty of accuracy.
