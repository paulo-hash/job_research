# job_research

Cherche des offres **New York** sur l’[API guest LinkedIn](https://gist.github.com/Diegiwg/51c22fa7ec9d92ed9b5d1f537b9e1107), les filtre (lieu, titre, visa, 24 h), les **score** contre `data/profile.yaml`, puis les stocke dans SQLite.

La recherche se fait à New York (`geoId=102571732`). LinkedIn ne filtre pas le visa côté search : le script lit chaque description (`/jobPosting/{id}`).

## Prérequis

- Python 3.11+

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Docker est optionnel (voir plus bas). `brew install docker` n’installe que le **client** : il faut aussi un daemon ([Colima](https://github.com/abiosoft/colima) ou Docker Desktop).

## Usage

```bash
source .venv/bin/activate
python main.py
```

Par défaut : **dernières 24 h**, jobs NYC d’ingénierie avec une **mention positive** de sponsoring, scorés puis insérés dans `data/jobs.db`.

```bash
python main.py --posted 24h                       # défaut
python main.py --posted week
python main.py --posted any                       # sans filtre de date
python main.py --visa all                         # tous les jobs NYC d’ingénierie
python main.py --visa none                        # refus explicite de sponsoring
python main.py --pages 12                         # pages par mot-clé (10 offres/page)
python main.py --keywords "software engineer,backend engineer"
python main.py --profile data/profile.yaml        # défaut
python main.py --json
python main.py --refresh                          # ignore le cache
```

Le résumé va sur stderr. La liste des jobs (avec score) va sur stdout.

## Profil et score

Édite `data/profile.yaml` (séniorité, années, skills, titres, domaines). Le score est un entier 0–100, **sans LLM** :

| Poids | Critère |
| --- | --- |
| 50 % | Skills du profil trouvés dans le titre + la description |
| 20 % | Titre proche de `titles` |
| 20 % | Séniorité / années (écart de grade, années demandées vs `years`) |
| 10 % | Domaines (`fintech`, `infrastructure`, …) |

Les mots sont matchés tels quels (pas de synonymes). Un job iOS sans Python/SQL reste bas ; un backend senior avec 2 skills du profil tourne autour de 60–70. Un 100 demande les 4 skills, un titre aligné, la bonne séniorité **et** un domaine.

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

## Base SQLite

Les offres scorées vont dans `data/jobs.db` (`JOBS_DB` pour changer le chemin). `id` (LinkedIn job id) est **PRIMARY KEY** : un `INSERT OR IGNORE` n’ajoute la ligne que si l’id n’existe pas encore. Le fichier n’est **pas** versionné.

```bash
python main.py --visa all --pages 2 --keywords "software engineer,backend engineer"
sqlite3 data/jobs.db "SELECT score, company, title, matched_skills FROM jobs ORDER BY score DESC;"
```

## Tests

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

Couvre un match fort / faible, le tri par score, et le `INSERT OR IGNORE` sur un id déjà présent.

## Docker

Le Dockerfile est dans `db/`. Le conteneur crée la table `jobs` au démarrage (`db/entrypoint.sh`), puis lance le scrape.

```bash

docker build -f db/Dockerfile -t job_research .
docker run --rm -v "$(pwd)/data:/app/data" job_research
```

Le volume garde `jobs.db` entre les runs.

## Cache

Les réponses sont dans `.cache/linkedin/`. `--refresh` ignore ce cache et re-télécharge tout. Ni le cache ni `data/jobs.db` ne sont commités.

## Limites

- Environ 10 offres par page ; LinkedIn coupe souvent vers `start=1000`.
- La plupart des offres **ne parlent pas** de visa dans la description. Un silence n’est ni un oui ni un non.
- Le score ne comprend pas les synonymes (ex. « distributed computing » ≠ `distributed systems`).
