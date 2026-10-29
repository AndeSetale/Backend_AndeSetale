# Andë Sétal — Documentation technique

## 1. Organisation du code

```
AndeSetale/
├── AndeSetal_Frontend/       # Angular 22 — dashboard admin, app citoyen (/mobile), app agent (/agent)
│   └── src/app/
│       ├── core/             # services API, modèles, guards (rôles), intercepteur JWT
│       ├── features/         # écrans (admin, citoyen, agent, authentification)
│       └── components/       # composants partagés (graphiques, tableaux, modales)
├── Backend_AndeSetale/       # Django 6.1 + DRF — API REST /api/
│   ├── deploy/               # docker-compose.yml : lance les 4 services ensemble
│   ├── docs/                 # livrables du projet et notes d'équipe
│   ├── config/               # settings (base, dev, test, prod) et routage
│   └── apps/
│       ├── users/            # comptes, rôles, OTP, gestion des agents
│       ├── incidents/        # signalements, photos, analyse IA, périmètre géographique
│       ├── interventions/    # interventions, rapports, workflow métier, statistiques
│       ├── notifications/    # notifications in-app
│       └── dashboard/        # statistiques admin/agent, carte, événements Set-Setal
└── ai-ande-settal/           # FastAPI — POST /analyze-image
    └── app/services/         # vision.py (Hugging Face), rag.py (règles de salubrité), llm.py (OpenRouter)
```

## 2. Installation avec Docker (recommandée)

**Prérequis** : Docker Desktop (≈ 15 Go d'espace disque libre pour le premier build).

Les trois dépôts doivent être clonés **dans le même dossier** :

```bash
mkdir AndeSetale && cd AndeSetale
git clone https://github.com/AndeSetale/AndeSetal_Frontend.git
git clone https://github.com/AndeSetale/Backend_AndeSetale.git
git clone https://github.com/AndeSetale/ai-ande-settal.git

cd Backend_AndeSetale
docker compose -f deploy/docker-compose.yml up -d --build                          # construit et démarre tout
docker compose -f deploy/docker-compose.yml exec backend python manage.py peupler_demo   # données de démonstration
```

Les commandes `docker compose …` ci-dessous s'entendent avec `-f deploy/docker-compose.yml` depuis `Backend_AndeSetale/`.

| Service | Adresse |
|---|---|
| Application (frontend) | http://localhost:4200 |
| API + documentation Swagger | http://localhost:8000/api/docs/ |
| Administration Django | http://localhost:8000/admin/ |
| Microservice IA (Swagger) | http://localhost:8001/docs |
| MySQL (conteneur) | `localhost:3307` — base `and_setal`, utilisateur `ande_user` / `ande_password` |

Commandes utiles :

```bash
docker compose logs -f backend                     # logs (les codes OTP s'y affichent)
docker compose exec backend python manage.py createsuperuser
docker compose up -d --build                       # après une modification du code
docker compose down                                # arrêt (les données sont conservées)
```

## 3. Installation sans Docker

### Backend (port 8000)

Prérequis : Python 3.12, [uv](https://docs.astral.sh/uv/), MySQL 8.

```bash
cd Backend_AndeSetale
cp .env.example .env            # puis renseigner SECRET_KEY et DB_*
uv sync
uv run python manage.py migrate
uv run python manage.py peupler_demo
uv run python manage.py runserver
```

### Microservice IA (port 8001)

```bash
cd ai-ande-settal
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # clés HF_TOKEN / OPENROUTER_API_KEY optionnelles
uvicorn app.main:app --port 8001
```

### Frontend (port 4200)

Prérequis : Node.js ≥ 24.15 (exigé par Angular 22).

```bash
cd AndeSetal_Frontend
npm ci
npm start
```

L'adresse de l'API se règle dans `src/environments/environment.ts` (`apiUrl`, `mediaUrl`).

## 4. Configuration (variables d'environnement)

**Backend** (`Backend_AndeSetale/.env`)

| Variable | Rôle | Défaut |
|---|---|---|
| `SECRET_KEY` | Clé secrète Django | — (obligatoire) |
| `DEBUG` | Mode développement | `False` |
| `ALLOWED_HOSTS` | Hôtes autorisés | `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Connexion MySQL | `and_setal`, `root`, …, `127.0.0.1`, `3306` |
| `CORS_ALLOWED_ORIGINS` | Origines du frontend | `http://localhost:4200` |
| `AI_SERVICE_URL` | URL du microservice IA | `http://localhost:8001/analyze-image` |
| `AI_SERVICE_TIMEOUT` | Délai max d'analyse (s) | `30` |
| `GEOFENCE_PLATEAU` | Refuser les signalements hors Dakar-Plateau | `True` |

**Microservice IA** (`ai-ande-settal/.env`)

| Variable | Rôle |
|---|---|
| `HF_TOKEN`, `HF_VISION_MODEL` | Classification d'image Hugging Face (optionnel) |
| `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` | Rédaction de la description et des recommandations (optionnel) |

Sans clé, l'IA bascule sur un mode local : la plateforme fonctionne, avec une confiance d'analyse faible (le type saisi par le citoyen est alors conservé).

## 5. Authentification

- `POST /api/auth/login/` avec `{"identifiant": "<email ou téléphone>", "password": "..."}` renvoie un jeton `access` (60 min) et un jeton `refresh` (7 jours).
- Les appels protégés envoient l'en-tête `Authorization: Bearer <access>`.
- Le frontend renouvelle automatiquement le jeton via `POST /api/auth/token/refresh/`.
- En local, les emails (codes OTP) ne sont pas envoyés : ils s'affichent dans les logs du backend.

## 6. API REST — routes

Documentation interactive complète : **http://localhost:8000/api/docs/** (Swagger, générée automatiquement).

Accès : 🌐 public · 🔑 connecté · 👤 citoyen · 🛠 agent · 🛡 admin

### Authentification et profil — `/api/auth/`

| Méthode | Route | Accès | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | 🌐 | Inscription citoyen (`nom_complet`, `email_ou_telephone`, `quartier`, `password`, `accepte_conditions`) ; envoie un code OTP |
| POST | `/api/auth/verify-email/` | 🌐 | Valide le code OTP (`email`, `code`) |
| POST | `/api/auth/resend-otp/` | 🌐 | Renvoie un code (attente 60 s, validité 10 min) |
| POST | `/api/auth/login/` | 🌐 | Connexion, renvoie les jetons et l'utilisateur |
| POST | `/api/auth/token/refresh/` | 🌐 | Nouveau jeton d'accès |
| GET / PATCH | `/api/auth/me/` | 🔑 | Profil de l'utilisateur connecté (le rôle n'est pas modifiable) |

### Incidents — `/api/incidents/`

| Méthode | Route | Accès | Description |
|---|---|---|---|
| POST | `/api/incidents/` | 🌐 | Signalement (multipart : `description`, `type`, `adresse`, `latitude`, `longitude`, `image`) ; déclenche l'analyse IA ; refusé hors Dakar-Plateau |
| GET | `/api/incidents/` | 🔑 | Liste paginée, filtres `?statut=&type=&niveau_urgence=&quartier=`, recherche `?search=`, tri `?ordering=` ; l'identité des autres signaleurs est masquée pour un citoyen |
| GET | `/api/incidents/my/` | 🔑 | Signalements de l'utilisateur connecté |
| GET | `/api/incidents/{id}/` | 🔑 | Détail (photos, analyse IA, agent assigné) |
| PATCH | `/api/incidents/{id}/` | 🛠🛡 | Mise à jour (`statut`, `niveau_urgence`, `commentaire`, `assigne_a`) ; `assigne_a` crée l'intervention de l'agent et notifie ; `statut=RESOLU` clôture |
| POST | `/api/incidents/preuves/upload/` | 🔑 | Ajout d'une photo à un incident existant |
| POST | `/api/incidents/{id}/analyse/` | 🛠🛡 | Enregistrement manuel d'un résultat d'analyse IA |

### Interventions — `/api/interventions/`

| Méthode | Route | Accès | Description |
|---|---|---|---|
| GET | `/api/interventions/` | 🛠🛡 | Toutes (admin) ou les siennes (agent) |
| POST | `/api/interventions/` | 🛡 | Création et assignation (`incident`, `agent`) |
| GET | `/api/interventions/my/` | 🛠 | Interventions de l'agent connecté, avec le détail de l'incident |
| GET | `/api/interventions/{id}/` | 🛠🛡 | Détail |
| PATCH | `/api/interventions/{id}/` | 🛠🛡 | Changement de statut : `EN_ATTENTE → EN_COURS → TERMINEE` (dates renseignées automatiquement ; `TERMINEE` résout l'incident) |
| GET / POST / PATCH | `/api/interventions/{id}/rapport/` | 🛠🛡 | Rapport de clôture (multipart : `photo_avant`, `photo_apres`) ; l'envoi termine l'intervention |

### Agents — `/api/agents/`

| Méthode | Route | Accès | Description |
|---|---|---|---|
| GET | `/api/agents/` | 🛡 | Liste avec indicateurs calculés (taux de complétion, ponctualité, temps moyen) |
| POST | `/api/agents/` | 🛡 | Création d'un agent et de son compte (`nom_complet`, `email`, `password`, `matricule`, …) |
| GET / PATCH / DELETE | `/api/agents/{id}/` | 🛡 | Fiche détaillée (activité de la semaine, répartition par type, activité récente), modification, suppression |
| GET / PATCH | `/api/agents/me/` | 🛠 | Profil de l'agent connecté ; PATCH `disponible` |

### Tableaux de bord — `/api/dashboard/`

| Méthode | Route | Accès | Description |
|---|---|---|---|
| GET | `/api/dashboard/stats/` | 🛡 | Compteurs, répartition par statut et par type, évolution sur 30 jours, classement des agents |
| GET | `/api/dashboard/agent/` | 🛠 | Indicateurs et interventions prioritaires de l'agent connecté |
| GET | `/api/dashboard/incidents-carte/` | 🛠🛡 | Incidents géolocalisés pour la carte |
| GET | `/api/dashboard/evenements/prochain/` | 🌐 | Prochain événement Set-Setal |

### Notifications — `/api/notifications/`

| Méthode | Route | Accès | Description |
|---|---|---|---|
| GET | `/api/notifications/` | 🔑 | Notifications de l'utilisateur (non lues en premier) |
| GET | `/api/notifications/unread-count/` | 🔑 | Nombre de non lues |
| POST | `/api/notifications/mark-read/` | 🔑 | Marque comme lues (`ids`) |

### Microservice IA — port 8001

| Méthode | Route | Description |
|---|---|---|
| POST | `/analyze-image` | Photo (multipart `file`) → `type_detecte`, `score_confiance`, `niveau_urgence_detecte`, `description_generee`, `recommandations`, `regles_contextuelles` |
| GET | `/health` | État du service et modèles utilisés |

Appelé automatiquement par le backend à la création d'un incident avec photo. Si la confiance est ≥ 0,6, le type et l'urgence de l'incident sont ajustés.

## 7. Routes de l'application (frontend)

| Espace | Routes |
|---|---|
| Authentification | `/connexion`, `/inscription`, `/verification`, `/dash/connexion` (admin) |
| Admin (rôle admin) | `/dashboard`, `/dashboard/map`, `/dashboard/map/incidents/:id`, `/dashboard/incidents`, `/dashboard/agents`, `/dashboard/agents/:id` |
| Citoyen | `/mobile`, `/mobile/carte`, `/mobile/scan`, `/mobile/enregistrement`, `/mobile/confirmation`, `/mobile/signalements`, `/mobile/signalements/:id`, `/mobile/profil` |
| Agent (rôle agent) | `/agent`, `/agent/interventions`, `/agent/interventions/:id`, `/agent/incidents/:id`, `/agent/historique/:id`, `/agent/rapport-envoye/:id`, `/agent/carte`, `/agent/profil` |

Après connexion, chaque utilisateur est redirigé vers l'espace de son rôle ; les espaces admin et agent sont protégés par des guards de rôle.

## 8. Tests

```bash
cd Backend_AndeSetale
uv run pytest            # 63 tests (permissions, incidents, workflow complet, dashboard)
```

Les tests utilisent une base SQLite en mémoire et un dossier média temporaire : ils ne touchent pas aux données réelles.

## 9. Problèmes fréquents

| Symptôme | Cause / solution |
|---|---|
| « Ce signalement est en dehors du périmètre couvert » | La position GPS est hors de Dakar-Plateau. Simuler une position (Chrome → F12 → Sensors → 14.6700 / -17.4380) ou mettre `GEOFENCE_PLATEAU=False`. |
| Code OTP non reçu | En local, il s'affiche dans `docker compose logs backend`. |
| Création d'agent refusée | Mot de passe trop simple (≥ 8 caractères, pas uniquement des chiffres, pas un mot de passe courant). |
| `ng serve` refuse de démarrer | Node.js trop ancien : Angular 22 exige Node ≥ 24.15. |
| Docker ne démarre pas / `unexpected EOF` | Espace disque insuffisant sur C:. |
