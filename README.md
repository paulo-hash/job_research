# job_research

Cherche des offres **New York** sur l’[API publique Lever](https://github.com/lever/postings-api) (software engineer, data engineer, ML, etc.) dont la description **mentionne un sponsoring de visa**.

Lever n’a pas de recherche globale : chaque entreprise a son propre board (`https://api.lever.co/v0/postings/{slug}`). Le script interroge la liste de slugs dans `companies.txt`, puis filtre en local.

## Prérequis

- Python 3.11+

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
source .venv/bin/activate
python main.py
```

Par défaut : jobs NYC d’ingénierie avec une **mention positive** de sponsoring (ignore les « we are unable to sponsor »).

```bash
python main.py --visa all                         # tous les jobs NYC d’ingénierie
python main.py --visa none                        # refus explicite de sponsoring
python main.py --companies palantir,spotify       # quelques boards seulement
python main.py --companies-file companies.txt
python main.py --json                             # sortie JSON
python main.py --workers 16
python main.py --refresh                          # ignore le cache
```

Le résumé (nombre de résultats, boards, erreurs) va sur stderr. La liste des jobs va sur stdout.

## Filtres

| Filtre | Règle |
| --- | --- |
| Lieu | New York City, NYC, Brooklyn, Manhattan, Queens, Bronx, Staten Island, Long Island City, `New York, NY`. Pas les autres villes de l’État (`Clifton Park, New York`). |
| Titre | software / data / ML / backend / frontend / fullstack / platform / SRE / research engineer, etc. Exclut sales engineer, recruiting, customer success. |
| Visa `sponsors` | La description dit qu’ils sponsorisent (H-1B, visa sponsorship, we will sponsor…). |
| Visa `none` | La description dit qu’ils ne sponsorisent pas. |
| Visa `all` | Tous les jobs NYC d’ingénierie, avec le statut `sponsors` / `no` / `unmentioned`. |

Le visa est lu dans le titre, la description et les listes de l’offre. Les questions du formulaire de candidature **ne sont pas** exposées par l’API Lever.

## Entreprises

Les slugs sont dans `companies.txt` (un par ligne, `#` pour commenter). C’est le `{slug}` de `https://jobs.lever.co/{slug}`.

Beaucoup d’entreprises (Stripe, Anthropic, Netflix, …) ont quitté Lever : un 404 ou une liste vide est ignoré.

## Cache

Les réponses API sont stockées dans `.cache/lever/` pour éviter de recharger ~2 000 boards à chaque run. Utilise `--refresh` pour tout re-télécharger.

## Limites

- Pas de recherche full-text côté Lever : seuls les boards listés sont scannés.
- La plupart des offres **ne parlent pas** de visa dans la description. Un silence n’est ni un oui ni un non.
- Certaines entreprises ne mettent le visa que dans le formulaire de candidature, invisible ici.
