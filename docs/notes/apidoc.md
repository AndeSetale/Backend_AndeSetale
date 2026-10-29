# Andë Sétal — Documentation API pour le Frontend Angular

## 1. Prérequis réseau

Le backend tourne sur la machine de Binetou.  
Assure-toi d'être **sur le même réseau WiFi/LAN**.

| Info | Valeur |
|------|--------|
| IP du backend | `192.168.1.111` |
| Port | `8000` |
| Base URL API | `http://192.168.1.111:8000/api` |
| Swagger interactif | `http://192.168.1.111:8000/api/docs/` |

> **Conseil :** Ouvre le Swagger dans ton navigateur — tu peux tester tous les endpoints directement depuis l'interface.

---

## 2. Lancer le backend (côté Binetou)

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

---

## 3. Configurer Angular

### 3.1 — Fichier d'environnement

```typescript
// src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://192.168.1.123:8000/api'
};
```

### 3.2 — Service HTTP de base

```typescript
// src/app/core/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  get<T>(path: string) {
    return this.http.get<T>(`${this.base}${path}`, { headers: this.authHeaders() });
  }

  post<T>(path: string, body: any) {
    return this.http.post<T>(`${this.base}${path}`, body, { headers: this.authHeaders() });
  }

  patch<T>(path: string, body: any) {
    return this.http.patch<T>(`${this.base}${path}`, body, { headers: this.authHeaders() });
  }
}
```

### 3.3 — Intercepteur JWT (recommandé)

Avec cet intercepteur, plus besoin d'ajouter le header manuellement dans chaque appel :

```typescript
// src/app/core/interceptors/auth.interceptor.ts
import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = localStorage.getItem('access_token');
    if (token) {
      const cloned = req.clone({
        setHeaders: { Authorization: `Bearer ${token}` }
      });
      return next.handle(cloned);
    }
    return next.handle(req);
  }
}
```

Enregistrer dans `app.module.ts` :
```typescript
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { AuthInterceptor } from './core/interceptors/auth.interceptor';

providers: [
  { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
]
```

---

## 4. Authentification JWT

Tous les endpoints protégés nécessitent le header :
```
Authorization: Bearer <access_token>
```

### 4.1 — Inscription

```
POST /api/auth/register/
Content-Type: application/json
```

**Body — contrat exact attendu :**
```json
{
  "nom_complet": "Jean Dupont",
  "email_ou_telephone": "jean@example.com",
  "quartier": "Plateau",
  "password": "MotDePasse123!",
  "accepte_conditions": true,
  "recevoir_alertes": true
}
```

> `email_ou_telephone` accepte une adresse email **ou** un numéro de téléphone.  
> Le champ `quartier` est optionnel.  
> Le rôle est toujours `citoyen` à l'inscription publique — les agents/admins sont créés par un administrateur.

**Réponse 201 :**
```json
{
  "message": "Inscription réussie. Vérifiez votre email pour activer votre compte.",
  "user": {
    "id": 1,
    "username": "jean",
    "email": "jean@example.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "role": "citoyen",
    "telephone": null,
    "quartier": "Plateau",
    "photo_profil": null,
    "email_verifie": false,
    "date_joined": "2026-08-14T10:00:00Z"
  }
}
```

---

### 4.2 — Connexion

```
POST /api/auth/login/
Content-Type: application/json
```

**Body :**
```json
{
  "identifiant": "jean@example.com",
  "password": "MotDePasse123!"
}
```

> `identifiant` = email ou numéro de téléphone (pas de champ `username`).

**Réponse 200 :**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": 1,
    "username": "jean",
    "email": "jean@example.com",
    "role": "citoyen",
    "first_name": "Jean",
    "last_name": "Dupont"
  }
}
```

> Stocker `access` et `refresh` dans `localStorage`.  
> Le token `access` expire après **60 minutes**, le `refresh` après **7 jours**.

---

### 4.3 — Rafraîchir le token

```
POST /api/auth/token/refresh/
Content-Type: application/json
```

**Body :**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Réponse 200 :**
```json
{
  "access": "<nouveau_access_token>"
}
```

---

### 4.4 — Profil utilisateur connecté

```
GET /api/auth/me/
Authorization: Bearer <access_token>
```

**Réponse 200 :**
```json
{
  "id": 1,
  "username": "jean",
  "email": "jean@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "role": "citoyen",
  "telephone": null,
  "quartier": "Plateau",
  "photo_profil": null,
  "email_verifie": false,
  "date_joined": "2026-08-14T10:00:00Z"
}
```

---

### 4.5 — Vérifier l'email (OTP)

```
POST /api/auth/verify-email/
Content-Type: application/json
```

**Body :**
```json
{
  "email": "jean@example.com",
  "code": "123456"
}
```

**Réponse 200 :**
```json
{
  "detail": "Email vérifié avec succès.",
  "email_verifie": true
}
```

---

### 4.6 — Renvoyer un code OTP

```
POST /api/auth/resend-otp/
Content-Type: application/json
```

**Body :**
```json
{
  "email": "jean@example.com"
}
```

**Réponse 200 :**
```json
{
  "detail": "Nouveau code envoyé.",
  "expires_in": 600
}
```

> Si le cooldown de 60 s n'est pas écoulé, retourne `429` avec `retry_after` (secondes restantes).

---

## 5. Incidents

### Valeurs des champs énumérés

| Champ | Valeurs acceptées |
|---|---|
| `type` | `DECHETS` · `CANAUX` · `VOIRIE` · `ECLAIRAGE_PUBLIC` · `ARBRE` · `FUITE_EAU` |
| `statut` | `NOUVEAU` · `EN_COURS` · `RESOLU` |
| `niveau_urgence` | `CRITIQUE` · `ELEVE` · `MODERE` · `ROUTINE` |

### 5.1 — Liste des incidents

```
GET /api/incidents/
Authorization: Bearer <access_token>
```

**Filtres disponibles (query params) :**

| Paramètre | Exemple |
|---|---|
| `statut` | `?statut=EN_COURS` |
| `type` | `?type=DECHETS` |
| `niveau_urgence` | `?niveau_urgence=CRITIQUE` |
| `quartier` | `?quartier=Médina` |
| `search` | `?search=ordures` (description, référence, adresse) |
| `ordering` | `?ordering=-date_creation` |
| `page` | `?page=2` (20 items par page) |

**Réponse 200 (paginée) :**
```json
{
  "count": 42,
  "next": "http://192.168.1.111:8000/api/incidents/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "reference": "INC-3A7F2B1C",
      "type": "DECHETS",
      "description": "Tas d'ordures devant l'école",
      "statut": "NOUVEAU",
      "niveau_urgence": "MODERE",
      "quartier": "Médina",
      "adresse": "Rue 12",
      "latitude": 14.6928,
      "longitude": -17.4467,
      "date_creation": "2026-08-14T09:00:00Z",
      "date_estimation_heures": 24,
      "commentaire": null,
      "signale_par": 1,
      "assigne_a": null,
      "preuves": [
        {
          "id": 1,
          "type": "PHOTO_INITIALE",
          "image_url": "http://192.168.1.111:8000/media/preuves/incident_1/photo.jpg",
          "date_ajout": "2026-08-14T09:00:00Z"
        }
      ],
      "analyse_ia": null
    }
  ]
}
```

---

### 5.2 — Créer un incident (sans image)

```
POST /api/incidents/
Content-Type: application/json
```

> Cet endpoint est **public** (pas d'authentification requise).  
> Si l'utilisateur est connecté, `signale_par` est renseigné automatiquement.

**Body :**
```json
{
  "type": "DECHETS",
  "description": "Tas d'ordures devant l'école",
  "niveau_urgence": "MODERE",
  "quartier": "Médina",
  "adresse": "Rue 12",
  "latitude": 14.6928,
  "longitude": -17.4467,
  "date_estimation_heures": 24,
  "commentaire": ""
}
```

**Réponse 201 :** objet `Incident` complet (même format que le détail).

---

### 5.3 — Créer un incident avec image

```
POST /api/incidents/
Content-Type: multipart/form-data
```

**FormData :**
```
type              = DECHETS
description       = Tas d'ordures devant l'école
niveau_urgence    = MODERE
quartier          = Médina
adresse           = Rue 12
latitude          = 14.6928
longitude         = -17.4467
image             = [fichier, max 5 MB, JPEG/PNG/WebP]
```

Si fournie, l'image crée automatiquement une `Preuve` de type `PHOTO_INITIALE`.

**Exemple Angular :**
```typescript
createIncident(data: any, imageFile?: File) {
  const formData = new FormData();
  Object.keys(data).forEach(key => formData.append(key, data[key]));
  if (imageFile) formData.append('image', imageFile);

  // Ne PAS définir Content-Type — Angular le gère automatiquement en multipart
  return this.http.post(`${this.base}/incidents/`, formData);
}
```

---

### 5.4 — Détail d'un incident

```
GET /api/incidents/{id}/
Authorization: Bearer <access_token>
```

**Réponse 200 :** objet `Incident` complet avec `preuves` et `analyse_ia`.

---

### 5.5 — Mettre à jour un incident (Agent / Admin)

```
PATCH /api/incidents/{id}/
Authorization: Bearer <access_token>   (rôle agent ou admin requis)
Content-Type: application/json
```

**Body (tous les champs sont optionnels) :**
```json
{
  "statut": "EN_COURS",
  "niveau_urgence": "CRITIQUE",
  "assigne_a": 3,
  "commentaire": "Équipe dépêchée sur place.",
  "date_estimation_heures": 12
}
```

---

### 5.6 — Mes incidents

```
GET /api/incidents/my/
Authorization: Bearer <access_token>
```

Retourne uniquement les incidents signalés par l'utilisateur connecté.

---

### 5.7 — Uploader une photo de preuve

```
POST /api/incidents/preuves/upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**FormData :**
```
incident_id = 1
type        = PHOTO_AVANT    (PHOTO_INITIALE | PHOTO_AVANT | PHOTO_APRES)
image       = [fichier, obligatoire, max 5 MB, JPEG/PNG/WebP]
```

**Réponse 201 :**
```json
{
  "id": 2,
  "type": "PHOTO_AVANT",
  "image_url": "http://192.168.1.111:8000/media/preuves/incident_1/photo_avant.jpg",
  "date_ajout": "2026-08-14T11:00:00Z"
}
```

---

### 5.8 — Soumettre une analyse IA

Endpoint réservé au service IA du coéquipier.

```
POST /api/incidents/{id}/analyse/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body :**
```json
{
  "type_detecte": "DECHETS",
  "score_confiance": 0.93,
  "niveau_urgence_detecte": "MODERE",
  "description_generee": "Accumulation de déchets ménagers.",
  "recommandations": "Intervention sous 24h."
}
```

> `score_confiance` doit être entre `0.0` et `1.0`.  
> Si une analyse existe déjà pour cet incident, elle est mise à jour.

---

## 6. Interventions

### Valeurs du champ `statut`

| Valeur | Signification |
|---|---|
| `EN_ATTENTE` | En attente d'affectation |
| `EN_COURS` | Intervention en cours |
| `TERMINEE` | Intervention clôturée |

### 6.1 — Liste des interventions

```
GET /api/interventions/
Authorization: Bearer <access_token>
```

**Réponse 200 :**
```json
[
  {
    "id": 1,
    "numero_suivi": "INT-4C2A8F1E",
    "incident": 1,
    "agent": 2,
    "statut": "EN_COURS",
    "date_debut": "2026-08-14T08:00:00Z",
    "date_fin": null,
    "rapport": null
  }
]
```

---

### 6.2 — Détail d'une intervention

```
GET /api/interventions/{id}/
Authorization: Bearer <access_token>
```

**Réponse 200 :** objet `Intervention` complet avec `rapport` si disponible.

```json
{
  "id": 1,
  "numero_suivi": "INT-4C2A8F1E",
  "incident": 1,
  "agent": 2,
  "statut": "TERMINEE",
  "date_debut": "2026-08-14T08:00:00Z",
  "date_fin": "2026-08-14T14:30:00Z",
  "rapport": {
    "id": 1,
    "contenu_pdf": null,
    "taille_fichier_mo": null,
    "statut": "VALIDE",
    "date_envoi": "2026-08-14T14:35:00Z"
  }
}
```

---

### 6.3 — Créer une intervention

```
POST /api/interventions/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body :**
```json
{
  "incident": 1,
  "agent": 2,
  "statut": "EN_ATTENTE",
  "date_debut": "2026-08-15T08:00:00Z",
  "date_fin": null
}
```

> `numero_suivi` est généré automatiquement (`INT-XXXXXXXX`).

**Réponse 201 :** objet `Intervention` complet.

---

### 6.4 — Mettre à jour une intervention

```
PATCH /api/interventions/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body (tous les champs sont optionnels) :**
```json
{
  "statut": "TERMINEE",
  "date_fin": "2026-08-15T14:00:00Z",
  "agent": 3
}
```

---

## 7. Notifications

### 7.1 — Mes notifications

```
GET /api/notifications/
Authorization: Bearer <access_token>
```

**Réponse 200 (non-lues en premier) :**
```json
[
  {
    "id": 1,
    "type": "EMAIL",
    "contenu": "Votre incident INC-3A7F2B1C est maintenant EN_COURS.",
    "lu": false,
    "date_envoi": "2026-08-14T10:30:00Z"
  },
  {
    "id": 2,
    "type": "PUSH",
    "contenu": "Un agent a été assigné à votre signalement.",
    "lu": true,
    "date_envoi": "2026-08-13T08:00:00Z"
  }
]
```

> Valeurs de `type` : `PUSH` · `EMAIL` · `SMS`

---

### 7.2 — Nombre de notifications non lues

```
GET /api/notifications/unread-count/
Authorization: Bearer <access_token>
```

**Réponse 200 :**
```json
{
  "unread_count": 3
}
```

---

### 7.3 — Marquer des notifications comme lues

```
POST /api/notifications/mark-read/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body :**
```json
{
  "ids": [1, 2, 3]
}
```

> Seules les notifications appartenant à l'utilisateur connecté et actuellement non lues sont mises à jour.

**Réponse 200 :**
```json
{
  "marked_read": 3
}
```

---

## 8. Dashboard

### 8.1 — Statistiques globales

```
GET /api/dashboard/stats/
Authorization: Bearer <access_token>
```

**Réponse 200 :**
```json
{
  "signalements": {
    "total": 142,
    "en_cours": 38,
    "resolus": 91,
    "urgents": 17
  },
  "incidents_par_statut": [
    { "statut": "EN_COURS", "count": 38 },
    { "statut": "NOUVEAU",  "count": 13 },
    { "statut": "RESOLU",   "count": 91 }
  ],
  "agents_disponibles": 6
}
```

> `urgents` = incidents avec `niveau_urgence` = `CRITIQUE` ou `ELEVE`.

---

## 9. Codes d'erreur

| Code | Signification | Action Angular |
|---|---|---|
| `200` | Succès | — |
| `201` | Ressource créée | — |
| `400` | Données invalides | Afficher les messages d'erreur par champ |
| `401` | Token manquant ou expiré | Appeler `/api/auth/token/refresh/` puis réessayer |
| `403` | Accès interdit (mauvais rôle) | Rediriger vers page d'accueil |
| `404` | Ressource introuvable | Afficher message d'erreur |
| `429` | Trop de requêtes (OTP) | Afficher `retry_after` secondes restantes |

**Format d'erreur 400 :**
```json
{
  "email_ou_telephone": ["Cette adresse email est déjà utilisée."],
  "password": ["Ce mot de passe est trop courant."]
}
```

**Format d'erreur 401/403 :**
```json
{
  "detail": "Les informations d'authentification n'ont pas été fournies."
}
```


# Gestion des agents

## Présentation

Le module `users` permet aux administrateurs de gérer les agents de la plateforme.

Un agent est composé de deux éléments :

- un compte `Utilisateur`
- un profil `Agent` associé au compte utilisateur par une relation OneToOne.

La création d'un agent crée donc automatiquement :

1. un utilisateur avec le rôle `AGENT`
2. un profil `Agent` associé

L'accès aux endpoints de gestion des agents est réservé aux utilisateurs authentifiés ayant le rôle `admin`.

---

## Endpoints

### Lister les agents

**GET `/api/agents/`**

Retourne la liste des agents.

Authentification :

- JWT Access Token requis
- rôle `admin` requis

Exemple de réponse :

```json
[
  {
    "id": 3,
    "nom_complet": "Agent Test Trois",
    "email": "agent.test3@andesetal.local",
    "telephone": "770000099",
    "quartier": "Plateau",
    "matricule": "AG-TEST-003",
    "departement": "Proprete",
    "specialisation": "DECHETS",
    "disponible": false,
    "score_satisfaction": 0,
    "taux_completion": 0,
    "ponctualite": 0,
    "taches_resolues_semaine": 0,
    "objectif_hebdo": 0
  }
]