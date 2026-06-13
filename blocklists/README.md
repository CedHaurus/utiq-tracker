# Listes de blocage Utiq

Ces listes bloquent les points d'accès Utiq, pas les sites éditeurs eux-mêmes.

## Niveau recommandé

**Standard** bloque uniquement les sous-domaines Utiq confirmés des 542 sites
actifs recensés, par exemple `utiq.example.com`. C'est le meilleur compromis
pour les utilisateurs ordinaires.

**Strict** ajoute les alias des opérateurs, les domaines techniques connus et
`utiq-aws.net`. Ce niveau protège davantage, mais peut empêcher l'accès au
portail Utiq de gestion ou de retrait du consentement.

## Formats

| Suffixe | Usage |
|---|---|
| `-adblock.txt` | uBlock Origin, AdGuard et bloqueurs compatibles |
| `-domains.txt` | Pi-hole, AdGuard Home et autres filtres DNS |
| `-hosts.txt` | Fichier hosts local |
| `-unbound.conf` | Inclusion directe dans la section `server:` d'Unbound |
| `-rpz.txt` | Résolveurs compatibles Response Policy Zone |

## Installation

### uBlock Origin

Ouvrir **Tableau de bord → Listes de filtres → Importer**, puis ajouter l'URL
publique du fichier `utiq-standard-adblock.txt`.

### AdGuard Home ou Pi-hole

Ajouter l'URL publique de `utiq-standard-domains.txt` comme liste DNS
personnalisée, puis actualiser les listes.

### Unbound

Inclure `utiq-standard-unbound.conf` depuis la configuration principale, puis
vérifier et recharger :

```sh
unbound-checkconf
systemctl reload unbound
```

## Dépannage

En cas de dysfonctionnement, autoriser uniquement le hostname concerné, par
exemple `utiq.example.com`, ou désactiver temporairement la liste standard.
Il ne faut pas autoriser globalement `utiq-aws.net`.

Les fichiers sont régénérés par :

```sh
./.venv/bin/python generate_blocklists.py
```
