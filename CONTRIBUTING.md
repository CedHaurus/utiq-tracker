# Contributing

Thanks for helping keep the list accurate. The index is non-exhaustive and sites add or drop Utiq all the time, so additions and corrections are welcome.

## Two ways to help

1. Open an issue with the site and what you found (fastest, no setup needed).
2. Open a pull request editing `data/source.json` directly.

## How to verify a site uses Utiq

Before adding a site, check at least one of these public signals:

- DNS: the site exposes a `utiq.<domain>` subdomain that is a CNAME to `*.utiq-aws.net`.

  ```bash
  dig +short CNAME utiq.example.com
  # expect something like frontend.prod.utiq-aws.net
  ```

- Certificate Transparency: a TLS certificate has been issued for `utiq.<domain>`. You can search https://crt.sh for `utiq.example.com`.
- The Utiq consent banner or a "Manage Utiq" link appears on the site.

## Adding an entry

Add an object to the `detections` array in `data/source.json`. Only a few fields are needed, the rest fall back to sensible defaults:

```json
{
  "domain": "example.com",
  "site_name": "Example",
  "final_url": "https://www.example.com/",
  "description": "Short description of the site.",
  "category": "Actualités et médias",
  "country": "France",
  "estimated_date": "2024-01-15",
  "loader_confirmed": true
}
```

Notes:

- `category` and `country` use the French labels listed in `build/maps.py` (for example `Actualités et médias`, `Sport`, `Technologie`, `France`, `Allemagne`, `Espagne`). If unsure, use `Généraliste / autre` and `International / indéterminé`.
- `estimated_date` is the earliest public trace you can find (CT log or archived loader), in `YYYY-MM-DD`. Leave it out if you don't know.
- Keep the array sorted however you like, the build sorts entries on its own (France first, then alphabetical).

## Test your change

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r build/requirements.txt
python build/build.py
```

Open `public/index.html` in a browser and confirm your site shows up and the search finds it. Then commit and open a pull request.

## Style

- Keep descriptions short and factual.
- Do not add a site you cannot back with a public signal.
- One site per entry, no duplicates (the build does not deduplicate for you).
