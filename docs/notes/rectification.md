# Corrections prioritaires — à appliquer avant de continuer

Tous ces fichiers ont été **testés bout en bout** (register → login → me →
signalement anonyme → vérification OTP → `/my/`) sur une base SQLite de test,
et la suite de tests existante (23 tests) passe intégralement après application.

## Où copier chaque fichier

| Fichier ici | Destination dans ton projet |
|---|---|
| `1_apps_incidents_serializers.py` | `apps/incidents/serializers.py` (remplace tout) |
| `2_apps_users_otp_utils.py` | `apps/users/otp_utils.py` (**nouveau fichier**) |
| `3_apps_users_serializers.py` | `apps/users/serializers.py` (remplace tout) |
| `4_apps_users_views.py` | `apps/users/views.py` (remplace tout) |
| `5_apps_users_urls.py` | `apps/users/urls.py` (remplace tout) |
| `6_apps_incidents_views.py` | `apps/incidents/views.py` (remplace tout) |
| `7_apps_incidents_urls.py` | `apps/incidents/urls.py` (remplace tout) |
| `8_apps_users_tests.py` | `apps/users/tests.py` (remplace tout — corrige le login dans les tests) |

## Ce que ça corrige

1. **Bug de duplication** dans `incidents/serializers.py` → `analyse_ia` réapparaît dans les réponses.
2. **OTP** : `POST /api/auth/verify-email/` et `POST /api/auth/resend-otp/` créés (durée 1min, cooldown 60s).
3. **Inscription alignée sur la maquette** : `nom_complet`, `email_ou_telephone`, `quartier`, `password`, `accepte_conditions`, `recevoir_alertes` — plus besoin d'envoyer `username`/`first_name`/`last_name`/`password2`/`role`.
4. **Connexion par email ou téléphone** via un champ unique `identifiant` (au lieu de `username`).
5. **Signalement sans connexion** : `POST /api/incidents/` accepte désormais les requêtes anonymes (`signale_par` reste `null` si non connecté).
6. **`GET /api/incidents/my/`** : liste les signalements du citoyen connecté.

## Après avoir copié les fichiers

```bash
uv run python manage.py migrate      # aucune nouvelle migration nécessaire, mais vérifie
uv run python manage.py test apps.users   # doit afficher 23 passed
uv run python manage.py runserver
```

## ⚠️ Un détail à vérifier toi-même

Dans `otp_utils.py`, l'envoi d'email utilise `django.core.mail.send_mail`, qui
s'appuie sur ta config `MAILERS` déjà en place (`console.EmailBackend` en dev
→ le code OTP s'affichera dans les logs du serveur, pas de vrai email envoyé
tant que tu es en local).

## Non inclus ici (priorité moyenne, pour la suite)

Détail/update d'incident, endpoint analyse IA, CRUD agents, rapport
d'intervention, filtres/pagination — voir `etat_avancement_backend.md`
partagé précédemment, section "🟠 Priorité moyenne".
