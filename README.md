# job_research

Cherche des offres **New York** sur l’[API guest LinkedIn](https://gist.github.com/Diegiwg/51c22fa7ec9d92ed9b5d1f537b9e1107) (software engineer, data engineer, ML, etc.) dont la description **mentionne un sponsoring de visa**.

La recherche se fait à New York (`geoId=102571732`). LinkedIn ne filtre pas le visa côté search : le script lit chaque description (`/jobPosting/{id}`).

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

Par défaut : **dernières 24 h**, jobs NYC d’ingénierie avec une **mention positive** de sponsoring.

```bash
python main.py --posted 24h                       # défaut
python main.py --posted week
python main.py --posted any                       # sans filtre de date
python main.py --visa all                         # tous les jobs NYC d’ingénierie
python main.py --visa none                        # refus explicite de sponsoring
python main.py --pages 12                         # pages par mot-clé (10 offres/page)
python main.py --keywords "software engineer,data engineer"
python main.py --json
python main.py --refresh                          # ignore le cache
```

Le résumé va sur stderr. La liste des jobs va sur stdout.

## Filtres

| Filtre | Règle |
| --- | --- |
| Lieu | New York City, NYC, Brooklyn, Manhattan, Queens, Bronx, Staten Island, Long Island City, `New York, NY`. Pas Jersey City ni les autres villes de l’État. |
| Titre | software / data / ML / backend / frontend / fullstack / platform / SRE / research engineer, etc. Exclut sales engineer, recruiting, customer success. |
| Visa `sponsors` | La description dit qu’ils sponsorisent (H-1B, visa sponsorship, we will sponsor…). |
| Visa `none` | La description dit qu’ils ne sponsorisent pas. |
| Visa `all` | Tous les jobs NYC d’ingénierie, avec le statut `sponsors` / `no` / `unmentioned`. |
| Date `24h` | Offres des dernières 24 h (défaut, `f_TPR=r86400`). `week` / `month` / `any` aussi. |

## Conception : éviter le 429

L’API guest LinkedIn n’est pas officielle. Trop d’appels trop vite renvoie **429 Too Many Requests** : LinkedIn refuse temporairement l’IP, ce n’est pas un échec de filtre.

Pour limiter ça :

1. **Une requête à la fois.** Les descriptions ne partent plus en parallèle.
2. **Pause de 1,5 s** (`REQUEST_GAP_SECONDS`) entre chaque appel réseau.
3. **Backoff après un 429.** Le script attend `Retry-After` s’il est présent, sinon 15 s, 30 s, 45 s… (5 essais). L’offre est ignorée seulement si LinkedIn refuse encore.
4. **Cache disque** (`.cache/linkedin/`). Une page ou une description déjà réussie n’est pas redemandée. Relance **sans** `--refresh`.

Ctrl+C arrête un run trop long. Réduire `--pages` ou `--keywords` diminue aussi le volume.

## Cache

Les réponses sont dans `.cache/linkedin/`. `--refresh` ignore ce cache et re-télécharge tout.

## Limites

- Environ 10 offres par page ; LinkedIn coupe souvent vers `start=1000`.
- La plupart des offres **ne parlent pas** de visa dans la description. Un silence n’est ni un oui ni un non.
