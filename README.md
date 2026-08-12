# Andë Sétal — Backend API

Plateforme de co-gestion de la salubrité urbaine à Dakar.  
Backend REST en Django 6.1 + DRF, base de données MySQL, authentification JWT.

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
│   │   ├── serializers.py  # RegisterSerializer, CustomTokenObtainPairSerializer
│   │   ├── views.py        # RegisterView, LoginView, MeView
│   │   ├── urls.py         # /api/auth/*
│   │   ├── permissions.py  # IsCitoyen, IsAgent, IsAdmin, IsOwnerOrAdmin...
│   │   ├── admin.py        # Interface d'administration
│   │   └── tests.py        # 23 tests de permissions
│   ├── incidents/          # Incidents, preuves, analyse IA, journal
│   │   ├── models.py       # Incident, Preuve, AnalyseIA, JournalActivite
│   │   ├── serializers.py  # IncidentSerializer, PreuveUploadSerializer, AnalyseIASerializer
│   │   ├── views.py        # IncidentListView, PreuveUploadView
│   │   └── urls.py         # /api/incidents/*
│   ├── interventions/      # Interventions terrain et rapports
│   │   ├── models.py       # Intervention, Rapport
│   │   ├── serializers.py  # InterventionSerializer, InterventionCreateSerializer
│   │   ├── views.py        # InterventionListView, InterventionDetailView
│   │   └── urls.py         # /api/interventions/*
│   ├── notifications/      # Notifications PUSH / EMAIL / SMS
│   │   ├── models.py       # Notification
│   │   ├── views.py        # NotificationListView, MarkReadView, UnreadCountView
│   │   └── urls.py         # /api/notifications/*
│   └── dashboard/          # Statistiques agrégées
│       ├── views.py        # DashboardStatsView
│       └── urls.py         # /api/dashboard/*
├── config/
│   ├── settings/
│   │   ├── base.py         # Settings communs (DB, DRF, JWT, CORS, MAILERS...)
│   │   ├── dev.py          # Debug toolbar
│   │   ├── prod.py         # HTTPS, HSTS, SMTP via MAILERS
│   │   └── test.py         # SQLite mémoire, passwords rapides
│   ├── urls.py             # Routes racine + debug toolbar
│   ├── api_urls.py         # Préfixe /api/
│   ├── wsgi.py
│   └── asgi.py
├── apidoc.md               # Documentation API pour le frontend Angular
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
# Remplir les valeurs dans .env (DB_NAME, DB_USER, DB_PASSWORD...)

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
| `ALLOWED_HOSTS` | Hôtes autorisés | `127.0.0.1,localhost,192.168.1.111,0.0.0.0` |
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

Voir `apidoc.md` pour la documentation complète dédiée au frontend Angular.

---

## Endpoints disponibles

### Authentification

| Méthode | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Inscription (crée le profil selon le rôle) |
| POST | `/api/auth/login/` | Public | Connexion — retourne access + refresh + user |
| POST | `/api/auth/token/refresh/` | Public | Renouveler l'access token |
| GET | `/api/auth/me/` | Bearer JWT | Profil de l'utilisateur connecté |

### Incidents

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/incidents/` | Bearer JWT | Liste tous les incidents avec leurs preuves |
| POST | `/api/incidents/` | Bearer JWT | Créer un incident (JSON ou multipart avec image) |
| POST | `/api/incidents/preuves/upload/` | Bearer JWT | Uploader une photo de preuve |

### Interventions

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/interventions/` | Bearer JWT | Liste toutes les interventions |
| POST | `/api/interventions/` | Bearer JWT | Créer une intervention |
| GET | `/api/interventions/{id}/` | Bearer JWT | Détail d'une intervention |
| PATCH | `/api/interventions/{id}/` | Bearer JWT | Mise à jour partielle (statut, dates) |

### Notifications

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/notifications/` | Bearer JWT | Mes notifications (non-lues en premier) |
| GET | `/api/notifications/unread-count/` | Bearer JWT | Nombre de notifications non lues |
| POST | `/api/notifications/mark-read/` | Bearer JWT | Marquer des notifications comme lues |

### Dashboard

| Méthode | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/dashboard/stats/` | Bearer JWT | Statistiques globales |

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
| `Utilisateur` | Modèle auth principal (AbstractUser) — rôle CITOYEN / AGENT / ADMIN |
| `Citoyen` | Profil étendu citoyen (nombre_signalements, nombre_resolus) |
| `Agent` | Profil étendu agent (matricule, spécialisation, scores) |
| `Administrateur` | Profil étendu admin (niveau_acces) |
| `OTP` | Code de vérification temporaire |

### incidents
| Modèle | Description |
|---|---|
| `Incident` | Signalement avec type, statut, urgence, géolocalisation |
| `Preuve` | Photo attachée à un incident (PHOTO_INITIALE / PHOTO_AVANT / PHOTO_APRES) |
| `AnalyseIA` | Résultat d'analyse automatique (score confiance, recommandations) |
| `JournalActivite` | Traçabilité de toutes les actions |

### interventions
| Modèle | Description |
|---|---|
| `Intervention` | Intervention terrain (PLANIFIEE / EN_COURS / TERMINEE / ANNULEE) |
| `Rapport` | Rapport de clôture d'une intervention |

### notifications
| Modèle | Description |
|---|---|
| `Notification` | Notification PUSH / EMAIL / SMS |

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
| `git push` | Pousser sur la branche courante |
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

| Branche | Description |
|---|---|
| `main` | Code stable en production |
| `develop` | Branche d'intégration |
| `feature/BE-001-django-init` | Initialisation projet + modèles complets |
| `feature/BE-004-auth-jwt` | Authentification JWT |
| `feature/BE-005-permissions` | Permissions DRF par rôle |

---

## Ce qui a été réalisé

### BE-001 — Initialisation du projet ✅
- Structure Django 6.1 avec `uv` (pas de `requirements.txt`)
- DRF configuré avec JWT, Swagger, CORS, filtres, pagination
- Settings split : `base.py` / `dev.py` / `prod.py` / `test.py`
- Tous les modèles du diagramme de classe implémentés
- Migrations propres appliquées sur MySQL
- Admins enregistrés avec filtres et inlines

### BE-004 — Authentification JWT ✅
- `POST /api/auth/register/` — inscription multi-rôle avec création profil automatique
- `POST /api/auth/login/` — retourne access (60 min) + refresh (7 jours) + infos user
- `POST /api/auth/token/refresh/` — renouvellement du token
- `GET /api/auth/me/` — profil utilisateur connecté
- Serializers de validation (password match, email unique, force du mot de passe)
- Tous les endpoints documentés dans Swagger

### BE-005 — Permissions par rôle ✅
- 6 classes de permissions (IsCitoyen, IsAgent, IsAdmin, IsAgentOrAdmin, IsCitoyenOrAdmin, IsOwnerOrAdmin)
- 23 tests unitaires et d'intégration — tous passent
- Settings de test avec SQLite en mémoire (pas de dépendance MySQL pour les tests)

### BE-006 — Incidents, Interventions, Notifications, Dashboard ✅
- CRUD incidents avec upload photo multipart (max 5 MB, JPEG/PNG/WebP)
- Upload de preuves (PHOTO_INITIALE / PHOTO_AVANT / PHOTO_APRES)
- Contrat AnalyseIA exposé pour le service IA
- CRUD interventions avec mise à jour partielle (PATCH)
- Notifications avec compteur non-lues et marquage en lot
- Endpoint stats dashboard
- Documentation API frontend dans `apidoc.md`

### Corrections ✅
- Fix conflit `EMAIL_BACKEND` vs `MAILERS` (Django 6.1) dans `dev.py` et `prod.py`
- Accès réseau LAN configuré (`ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`)
