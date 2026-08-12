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

Binetou doit démarrer le serveur en exposant toutes les interfaces réseau :

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

---

## 3. Configurer Angular

### 3.1 — Fichier d'environnement

Dans `src/environments/environment.ts` :

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://192.168.1.111:8000/api'
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

### 3.3 — Ajouter HttpClientModule

Dans `app.module.ts` (ou `app.config.ts` pour standalone) :

```typescript
import { HttpClientModule } from '@angular/common/http';

// Dans imports: [HttpClientModule]
```

---

## 4. Authentification JWT

Tous les endpoints (sauf login et register) nécessitent un token JWT dans le header :

```
Authorization: Bearer <access_token>
```

### 4.1 — Inscription

```
POST /api/auth/register/
Content-Type: application/json
```

**Body :**
```json
{
  "username": "jean_dupont",
  "email": "jean@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "password": "MotDePasse123!",
  "password2": "MotDePasse123!",
  "role": "CITOYEN",
  "telephone": "771234567",
  "quartier": "Plateau"
}
```

Valeurs possibles pour `role` : `CITOYEN`, `AGENT`, `ADMIN`

**Réponse 201 :**
```json
{
  "message": "Inscription réussie.",
  "user": {
    "id": 1,
    "username": "jean_dupont",
    "email": "jean@example.com",
    "role": "CITOYEN",
    ...
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
  "username": "jean_dupont",
  "password": "MotDePasse123!"
}
```

**Réponse 200 :**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": 1,
    "username": "jean_dupont",
    "email": "jean@example.com",
    "role": "CITOYEN",
    "first_name": "Jean",
    "last_name": "Dupont"
  }
}
```

> **À stocker** : `access` dans `localStorage.setItem('access_token', ...)` et `refresh` dans `localStorage.setItem('refresh_token', ...)`

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
  "username": "jean_dupont",
  "email": "jean@example.com",
  "first_name": "Jean",
  "last_name": "Dupont",
  "role": "CITOYEN",
  "telephone": "771234567",
  "quartier": "Plateau",
  "photo_profil": null,
  "email_verifie": false,
  "date_joined": "2026-08-12T10:00:00Z"
}
```

---

## 5. Incidents

### 5.1 — Liste des incidents

```
GET /api/incidents/
Authorization: Bearer <access_token>
```

**Réponse 200 :**
```json
[
  {
    "id": 1,
    "reference": "INC-00001",
    "type": "DECHET",
    "description": "Tas d'ordures devant l'école",
    "statut": "SIGNALE",
    "niveau_urgence": "MOYEN",
    "quartier": "Médina",
    "adresse": "Rue 12",
    "latitude": 14.6928,
    "longitude": -17.4467,
    "date_creation": "2026-08-12T09:00:00Z",
    "date_estimation_heures": 24,
    "commentaire": "",
    "signale_par": 1,
    "assigne_a": null,
    "preuves": [
      {
        "id": 1,
        "type": "PHOTO_INITIALE",
        "image_url": "http://192.168.1.111:8000/media/preuves/photo.jpg",
        "date_ajout": "2026-08-12T09:00:00Z"
      }
    ],
    "analyse_ia": null
  }
]
```

---

### 5.2 — Créer un incident (sans image)

```
POST /api/incidents/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Body :**
```json
{
  "type": "DECHET",
  "description": "Tas d'ordures devant l'école",
  "niveau_urgence": "MOYEN",
  "quartier": "Médina",
  "adresse": "Rue 12",
  "latitude": 14.6928,
  "longitude": -17.4467,
  "date_estimation_heures": 24,
  "commentaire": ""
}
```

Valeurs `type` : `DECHET`, `INONDATION`, `DEGRADATION`, `AUTRE`  
Valeurs `niveau_urgence` : `FAIBLE`, `MOYEN`, `ELEVE`, `CRITIQUE`

---

### 5.3 — Créer un incident (avec image)

```
POST /api/incidents/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Body (FormData) :**
```
type          = DECHET
description   = Tas d'ordures devant l'école
niveau_urgence = MOYEN
quartier      = Médina
adresse       = Rue 12
latitude      = 14.6928
longitude     = -17.4467
image         = [fichier image, max 5 MB, JPEG/PNG/WebP]
```

**Exemple Angular :**
```typescript
createIncidentWithImage(data: any, imageFile: File) {
  const formData = new FormData();
  Object.keys(data).forEach(key => formData.append(key, data[key]));
  formData.append('image', imageFile);

  return this.http.post(`${this.base}/api/incidents/`, formData, {
    headers: new HttpHeaders({ Authorization: `Bearer ${localStorage.getItem('access_token')}` })
    // Ne PAS définir Content-Type manuellement — Angular le gère automatiquement en multipart
  });
}
```

---

### 5.4 — Uploader une photo de preuve (incident existant)

```
POST /api/incidents/preuves/upload/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Body (FormData) :**
```
incident_id = 1
type        = PHOTO_AVANT    (PHOTO_INITIALE | PHOTO_AVANT | PHOTO_APRES)
image       = [fichier image, obligatoire, max 5 MB, JPEG/PNG/WebP]
```

**Réponse 201 :**
```json
{
  "id": 2,
  "type": "PHOTO_AVANT",
  "image_url": "http://192.168.1.111:8000/media/preuves/photo_avant.jpg",
  "date_ajout": "2026-08-12T11:00:00Z"
}
```

---

## 6. Interventions

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
    "numero_suivi": "INT-00001",
    "incident": 1,
    "agent": 2,
    "statut": "EN_COURS",
    "date_debut": "2026-08-12T08:00:00Z",
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
  "statut": "PLANIFIEE",
  "date_debut": "2026-08-13T08:00:00Z",
  "date_fin": null
}
```

Valeurs `statut` : `PLANIFIEE`, `EN_COURS`, `TERMINEE`, `ANNULEE`

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
  "date_fin": "2026-08-13T14:00:00Z"
}
```

---

## 7. Notifications

### 7.1 — Mes notifications

```
GET /api/notifications/
Authorization: Bearer <access_token>
```

**Réponse 200 :**
```json
[
  {
    "id": 1,
    "titre": "Incident mis à jour",
    "message": "Votre incident INC-00001 est maintenant EN_COURS.",
    "lu": false,
    "date_envoi": "2026-08-12T10:30:00Z"
  }
]
```

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

---

## 9. Codes d'erreur courants

| Code | Signification |
|------|--------------|
| `401` | Token manquant ou expiré → relancer `/api/auth/token/refresh/` |
| `400` | Données invalides → voir le champ `detail` ou les champs en erreur |
| `403` | Accès interdit (mauvais rôle) |
| `404` | Ressource introuvable |

---

## 10. Intercepteur Angular pour le token (recommandé)

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

Avec l'intercepteur en place, plus besoin d'ajouter le header manuellement dans chaque appel.
