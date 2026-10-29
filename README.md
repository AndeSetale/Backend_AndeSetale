# Andë Sétal — Backend API

Plateforme de co-gestion de la salubrité urbaine à Dakar.  
Backend REST en Django 6.1 + DRF, base de données MySQL, authentification JWT.

> **Livrables du projet** (présentation, base de données, documentation technique, API) : [`docs/livrables/`](docs/livrables/README.md)  
> **Lancer toute la plateforme avec Docker** : `docker compose -f deploy/docker-compose.yml up -d --build`

---

## Stack technique

| Technologie | Version | Rôle |
|---|---|---|
| Python | 3.12 | Langage |
| Django | 6.1 | Framework web |
| Django REST Framework | 3.18 | API REST |
| djangorestframework-simplejwt | 5.5 | Authentification JWT |
| drf-spectacular | 0.30 | Documentation Swagger |
| MySQL | 8+ | Base de données production |
| SQLite | — | Base de données tests |
| uv | latest | Gestionnaire de paquets / venv |
| django-environ | 0.14 | Variables d'environnement |
| django-cors-headers | 4.9 | CORS |
| django-filter | 26.1 | Filtrage des querysets |
| Pillow | 12.3 | Upload photos |

---

## Structure du projet

```
Backend_AndeSetale/
├── apps/
│   ├── users/              # Utilisateurs, rôles, OTP, permissions
│   │   ├── models.py       # Utilisateur, Citoyen, Agent, Administrateur, OTP
│   │   ├── serializers.py  # RegisterSerializer, CustomTokenObtainPairSerializer, VerifyEmailSerializer
│   │   ├── views.py        # RegisterView, LoginView, MeView, VerifyEmailView, ResendOtpView
│   │   ├── urls.py         # /api/auth/*
│   │   ├── permissions.py  # IsCitoyen, IsAgent, IsAdmin, IsAgentOrAdmin, IsCitoyenOrAdmin, IsOwnerOrAdmin
│   │   ├── otp_utils.py    # Génération et envoi OTP par email
│   │   ├── admin.py        # Interface d'administration
│   │   └── tests.py        # 23 tests de permissions
│   ├── incidents/          # Incidents, preuves, analyse IA, journal
│   │   ├── models.py       # Incident, Preuve (ImageField), AnalyseIA, JournalActivite
│   │   ├── serializers.py  # IncidentSerializer/Create/Update, PreuveUpload, AnalyseIASerializer
│   │   ├── views.py        # IncidentListView, IncidentDetailView, PreuveUploadView, MesIncidentsView, AnalyseIAView
│   │   └── urls.py         # /api/incidents/*
│   ├── interventions/      # Interventions terrain et rapports
│   │   ├── models.py       # Intervention, Rapport
│   │   ├── serializers.py  # InterventionSerializer/Create/Update, RapportSerializer
│   │   ├── views.py        # InterventionListView, InterventionDetailView
│   │   └── urls.py         # /api/interventions/*
│   ├── notifications/      # Notifications PUSH / EMAIL / SMS
│   │   ├── models.py       # Notification
│   │   ├── serializers.py  # NotificationSerializer, NotificationMarkReadSerializer
│   │   ├── views.py        # NotificationListView, NotificationMarkReadView, NotificationUnreadCountView
│   │   └── urls.py         # /api/notifications/*
│   └── dashboard/          # Statistiques agrégées
│       ├── serializers.py  # DashboardStatsSerializer
│       ├── views.py        # DashboardStatsView
│       └── urls.py         # /api/dashboard/*
├── config/
│   ├── settings/
│   │   ├── base.py         # Settings communs (DB, DRF, JWT, CORS, MAILERS…)
│   │   ├── dev.py          # Debug toolbar
│   │   ├── prod.py         # HTTPS, HSTS, SMTP
│   │   └── test.py         # SQLite mémoire, passwords rapides
│   ├── urls.py             # Routes racine + media + debug toolbar
│   ├── api_urls.py         # Préfixe /api/
│   ├── wsgi.py
│   └── asgi.py
├── docs/                   # Livrables, notes d'équipe (docs/notes/) et documentation
├── .env                    # Variables locales (non versionné)
├── .env.example            # Template à copier
├── pyproject.toml          # Dépendances + config pytest
└── uv.lock                 # Lock file uv
```

---

## Installation

### Prérequis
- Python 3.12+
- MySQL 8+ en cours d'exécution
- `uv` installé (`pip install uv` ou voir https://docs.astral.sh/uv/)

### Étapes

```bash
# 1. Cloner le repo
git clone https://github.com/AndeSetale/Backend_AndeSetale.git
cd Backend_AndeSetale

# 2. Installer les dépendances (crée le .venv automatiquement)
uv sync

# 3. Créer le fichier d'environnement
cp .env.example .env
# Remplir les valeurs dans .env (DB_NAME, DB_USER, DB_PASSWORD…)

# 4. Appliquer les migrations
uv run python manage.py migrate

# 5. Créer un superutilisateur (optionnel)
uv run python manage.py createsuperuser

# 6. Lancer le serveur (local uniquement)
uv run python manage.py runserver

# 6b. Lancer le serveur exposé sur le réseau LAN (pour le frontend)
uv run python manage.py runserver 0.0.0.0:8000
```

---

## Variables d'environnement

Copier `.env.example` en `.env` et remplir :

| Variable | Description | Exemple |
|---|---|---|
| `SECRET_KEY` | Clé secrète Django | `une-longue-chaine-aleatoire` |
| `DEBUG` | Mode debug | `True` (dev) / `False` (prod) |
| `ALLOWED_HOSTS` | Hôtes autorisés | `127.0.0.1,localhost,192.168.1.111` |
| `DB_NAME` | Nom de la base MySQL | `ande_setal` |
| `DB_USER` | Utilisateur MySQL | `ande_user` |
| `DB_PASSWORD` | Mot de passe MySQL | `votre_mdp` |
| `DB_HOST` | Hôte MySQL | `127.0.0.1` |
| `DB_PORT` | Port MySQL | `3306` |
| `CORS_ALLOWED_ORIGINS` | Origines frontend autorisées | `http://localhost:4200,http://192.168.1.111:4200` |

> Pour l'accès réseau LAN, ajouter l'IP de ta machine dans `ALLOWED_HOSTS` et l'adresse du frontend dans `CORS_ALLOWED_ORIGINS`.

---

## Accès réseau LAN (développement collaboratif)

Pour que le frontend Angular sur une autre machine puisse appeler l'API :

```bash
# Connaître son IP locale
hostname -I

# Lancer le serveur sur toutes les interfaces
uv run python manage.py runserver 0.0.0.0:8000
```

| Accès | URL |
|---|---|
| Local (ta machine) | `http://localhost:8000` |
| Réseau LAN (autre machine) | `http://<ton-IP-locale>:8000` |
| Swagger (LAN) | `http://<ton-IP-locale>:8000/api/docs/` |

> `0.0.0.0:8000` est l'adresse d'**écoute** — ne pas l'ouvrir dans un navigateur. Utiliser l'IP locale à la place.

---

## Endpoints disponibles

### Authentification

| Méthode | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Inscription citoyen (nom_complet, email_ou_telephone, quartier, password…) |
| POST | `/api/auth/login/` | Public | Connexion via identifiant (email ou téléphone) — retourne access + refresh + user |
| POST | `/api/auth/token/refresh/` | Public | Renouveler l'access token |
| GET | `/api/auth/me/` | Bearer JWT | Profil de l'utilisateur connecté |
| POST | `/api/auth/verify-email/` | Public | Vérifier le code OTP reçu par email |
| POST | `/api/auth/resend-otp/` | Public | Renvoyer un code OTP (cooldown 60 s) |

### Incidents

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/incidents/` | Bearer JWT | Liste tous les incidents (filtrables, paginés) |
| POST | `/api/incidents/` | Public | Créer un incident (JSON ou multipart avec image optionnelle) |
| GET | `/api/incidents/{id}/` | Bearer JWT | Détail complet d'un incident |
| PATCH | `/api/incidents/{id}/` | Agent / Admin | Mise à jour partielle (statut, assignation, urgence…) |
| GET | `/api/incidents/my/` | Bearer JWT | Mes incidents (signalés par l'utilisateur connecté) |
| POST | `/api/incidents/preuves/upload/` | Bearer JWT | Uploader une photo de preuve sur un incident existant |
| POST | `/api/incidents/{id}/analyse/` | Bearer JWT | Soumettre le résultat d'analyse IA |

### Interventions

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/interventions/` | Bearer JWT | Liste toutes les interventions |
| POST | `/api/interventions/` | Bearer JWT | Créer une intervention |
| GET | `/api/interventions/{id}/` | Bearer JWT | Détail d'une intervention |
| PATCH | `/api/interventions/{id}/` | Bearer JWT | Mise à jour partielle (statut, agent, dates) |

### Notifications

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/notifications/` | Bearer JWT | Mes notifications (non-lues en premier) |
| GET | `/api/notifications/unread-count/` | Bearer JWT | Nombre de notifications non lues |
| POST | `/api/notifications/mark-read/` | Bearer JWT | Marquer une liste de notifications comme lues |

### Dashboard

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/dashboard/stats/` | Bearer JWT | Statistiques globales (totaux, répartition par statut, agents disponibles) |

### Documentation

| URL | Description |
|---|---|
| `/api/docs/` | Swagger UI interactif |
| `/api/schema/` | Schéma OpenAPI (JSON/YAML) |
| `/admin/` | Interface d'administration Django |

---

## Modèles de données

### users
| Modèle | Description |
|---|---|
| `Utilisateur` | Modèle auth principal (AbstractUser) — rôle `citoyen` / `agent` / `admin` |
| `Citoyen` | Profil étendu citoyen (nombre_signalements, nombre_resolus) |
| `Agent` | Profil étendu agent (matricule, spécialisation, scores de performance) |
| `Administrateur` | Profil étendu admin (niveau_acces) |
| `OTP` | Code de vérification temporaire (validité 1 min, cooldown 60 s) |

### incidents
| Modèle | Description |
|---|---|
| `Incident` | Signalement avec type, statut, niveau urgence, géolocalisation, référence auto |
| `Preuve` | Photo attachée à un incident — upload `ImageField` (PHOTO_INITIALE / PHOTO_AVANT / PHOTO_APRES) |
| `AnalyseIA` | Résultat d'analyse automatique (type détecté, score confiance, recommandations) |
| `JournalActivite` | Traçabilité de toutes les actions |

### interventions
| Modèle | Description |
|---|---|
| `Intervention` | Intervention terrain (EN_ATTENTE / EN_COURS / TERMINEE) — numéro de suivi auto |
| `Rapport` | Rapport de clôture d'une intervention |

### notifications
| Modèle | Description |
|---|---|
| `Notification` | Notification PUSH / EMAIL / SMS — champ `lu` géré par l'API |

---

## Permissions

| Classe | Accès autorisé |
|---|---|
| `IsCitoyen` | Citoyens authentifiés uniquement |
| `IsAgent` | Agents authentifiés uniquement |
| `IsAdmin` | Administrateurs uniquement |
| `IsAgentOrAdmin` | Agents et Administrateurs |
| `IsCitoyenOrAdmin` | Citoyens et Administrateurs |
| `IsOwnerOrAdmin` | Propriétaire de la ressource ou Administrateur |

Usage dans une view :
```python
from apps.users.permissions import IsAgentOrAdmin

class MaView(generics.ListAPIView):
    permission_classes = [IsAgentOrAdmin]
```

---

## Filtres disponibles sur `/api/incidents/`

| Paramètre | Type | Exemple |
|---|---|---|
| `statut` | query | `?statut=EN_COURS` |
| `type` | query | `?type=DECHETS` |
| `niveau_urgence` | query | `?niveau_urgence=CRITIQUE` |
| `quartier` | query | `?quartier=Médina` |
| `search` | query | `?search=ordures` (description, référence, adresse) |
| `ordering` | query | `?ordering=-date_creation` |
| `page` | query | `?page=2` (pagination, 20 items/page) |

---

## Commandes utiles

### Développement

| Commande | Description |
|---|---|
| `uv sync` | Installer toutes les dépendances |
| `uv run python manage.py runserver` | Lancer le serveur (local) |
| `uv run python manage.py runserver 0.0.0.0:8000` | Lancer exposé sur le réseau LAN |
| `uv run python manage.py shell` | Shell Django interactif |
| `uv run python manage.py createsuperuser` | Créer un superutilisateur admin |
| `uv run python manage.py check` | Vérifier la config Django |

### Base de données

| Commande | Description |
|---|---|
| `uv run python manage.py makemigrations` | Générer les migrations |
| `uv run python manage.py makemigrations <app>` | Migrations d'une app spécifique |
| `uv run python manage.py migrate` | Appliquer les migrations |
| `uv run python manage.py showmigrations` | Voir l'état des migrations |
| `uv run python manage.py sqlmigrate <app> <num>` | Voir le SQL d'une migration |

### Tests

| Commande | Description |
|---|---|
| `uv run pytest` | Lancer tous les tests |
| `uv run pytest apps/users/tests.py` | Tests d'une app spécifique |
| `uv run pytest -v` | Mode verbeux |
| `uv run pytest -x` | Stopper au premier échec |

### Git — workflow branches

| Commande | Description |
|---|---|
| `git checkout -b feature/BE-00X-nom` | Créer une nouvelle branche feature |
| `git checkout develop` | Revenir sur develop |
| `git add <fichiers>` | Stager des fichiers spécifiques |
| `git commit -m "feat(scope): message"` | Committer avec convention |
| `git push -u origin feature/BE-00X-nom` | Pousser une nouvelle branche |
| `git log --oneline -10` | Historique compact |

---

## Convention de commits

```
feat(scope):     ajout d'une fonctionnalité
fix(scope):      correction d'un bug
docs(scope):     mise à jour documentation
refactor(scope): refactorisation sans changement fonctionnel
test(scope):     ajout ou modification de tests
chore(scope):    tâches de maintenance
```

---

## Branches

| Branche | Statut | Description |
|---|---|---|
| `main` | stable | Code en production |
| `develop` | actif | Branche d'intégration principale |
| `feature/BE-001-django-init` | mergée | Initialisation projet + modèles complets |
| `feature/BE-004-auth-jwt` | mergée | Authentification JWT |
| `feature/BE-005-permissions` | mergée | Permissions DRF par rôle |
| `feature/BE-011-upload-photo` | mergée | Upload photos (ImageField, validation 5 MB) |
| `feature/BE-018-dashboard-stats` | mergée | Dashboard stats superviseur |
| `feature/BE-0018-api-dashboard-superviseur` | mergée | API Dashboard superviseur |

---

## Ce qui a été réalisé

### BE-001 — Initialisation du projet ✅
- Structure Django 6.1 avec `uv`
- DRF configuré avec JWT, Swagger, CORS, filtres, pagination
- Settings split : `base.py` / `dev.py` / `prod.py` / `test.py`
- Tous les modèles implémentés, migrations appliquées sur MySQL
- Admins enregistrés avec filtres et inlines

### BE-004 — Authentification JWT ✅
- `POST /api/auth/register/` — inscription citoyen, contrat maquette Angular (nom_complet, email_ou_telephone…)
- `POST /api/auth/login/` — connexion par email ou téléphone, retourne access (60 min) + refresh (7 j) + user
- `POST /api/auth/token/refresh/` — renouvellement token
- `GET /api/auth/me/` — profil utilisateur connecté
- `POST /api/auth/verify-email/` — vérification OTP par email
- `POST /api/auth/resend-otp/` — renvoi OTP avec cooldown 60 s

### BE-005 — Permissions par rôle ✅
- 6 classes de permissions (IsCitoyen, IsAgent, IsAdmin, IsAgentOrAdmin, IsCitoyenOrAdmin, IsOwnerOrAdmin)
- 23 tests unitaires et d'intégration — tous passent
- Settings de test SQLite en mémoire (pas de dépendance MySQL)

### BE-011 — Upload photos ✅
- `Preuve.image` migré de `CharField(url)` vers `ImageField` (upload physique)
- Validation : max 5 MB, formats JPEG/PNG/WebP
- `POST /api/incidents/preuves/upload/` — upload multipart sur incident existant
- `POST /api/incidents/` — image optionnelle incluse à la création (PHOTO_INITIALE auto)
- URLs absolues construites avec `request.build_absolute_uri`

### BE-006 — CRUD Incidents & Interventions ✅
- `GET/POST /api/incidents/` avec filtres (statut, type, urgence, quartier), recherche, pagination
- `GET/PATCH /api/incidents/{id}/` — détail et mise à jour par agent/admin
- `GET /api/incidents/my/` — incidents du citoyen connecté
- `POST /api/incidents/{id}/analyse/` — endpoint pour le service IA (update_or_create)
- CRUD interventions complet avec `InterventionCreateSerializer` / `InterventionUpdateSerializer`
- Numéro de suivi auto généré (`INT-XXXXXXXX`)

### BE-018 — Dashboard superviseur ✅
- `GET /api/dashboard/stats/` — totaux signalements, répartition par statut, agents disponibles
- Agrégats optimisés (4 requêtes groupées)

### Notifications ✅
- `GET /api/notifications/` — liste non-lues en premier
- `GET /api/notifications/unread-count/` — compteur
- `POST /api/notifications/mark-read/` — marquage en lot par IDs

### Corrections ✅
- Fix conflit `EMAIL_BACKEND` vs `MAILERS` (Django 6.1)
- Accès réseau LAN configuré (`ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`)
