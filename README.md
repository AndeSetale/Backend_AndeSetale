# Backend_AndeSetale

# Andë Sétal — Backend

## Stack
Django 5 · DRF · MySQL · JWT (SimpleJWT) · uv

## Setup local
\`\`\`bash
uv sync
cp .env.example .env   # remplir les valeurs
uv run python manage.py migrate
uv run python manage.py runserver
\`\`\`

## Structure
- `config/` — settings (base/dev/prod), urls racine
- `apps/users` — Utilisateur, Citoyen, Agent, Administrateur, OTP
- `apps/incidents` — Incident, AnalyseIA, Preuve
- `apps/interventions` — Intervention, Rapport, JournalActivite
- `apps/notifications` — Notification

## Documentation API
`/api/docs/` (Swagger) une fois le serveur lancé.
```

---

## Récapitulatif des critères d'acceptation BE-001

| Critère | Comment il est couvert |
|---|---|
| Le projet démarre sans erreur | `uv run python manage.py runserver` (étape 11) |
| DRF accessible via `/api/` | `config/api_urls.py` monté sur `/api/` (étape 10) |
| Structure propre et documentée | apps séparées par domaine, settings split, README (étapes 8, 14) |