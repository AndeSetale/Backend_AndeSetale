# Andë Sétal — Reste à faire pour un backend 100 % fonctionnel

**Périmètre :** backend uniquement. IA et frontend exclus (gérés par tes coéquipiers).

**Statut des corrections précédentes : ✅ appliquées et validées** (23/23 tests passent) :
- Bug de duplication dans `incidents/serializers.py` corrigé.
- Endpoints OTP (`verify-email`, `resend-otp`) créés.
- Inscription alignée sur la maquette (`nom_complet`, `email_ou_telephone`, `quartier`, `password`).
- Connexion par email/téléphone via `identifiant`.
- Signalement accessible sans connexion (`signale_par = null` si anonyme).
- `GET /api/incidents/my/` créé.

Ce document couvre **tout ce qu'il reste**, classé par priorité.

---

## 🟠 Priorité haute — fonctionnalités attendues par les maquettes

### 1. Détail d'un incident — `GET /api/incidents/<id>/`

N'existe pas encore. Nécessaire pour les écrans "Détail incidents" (web admin) et "Details" (mobile agent/citoyen).

**À ajouter dans `apps/incidents/views.py` :**
```python
from rest_framework.generics import get_object_or_404

class IncidentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        incident = get_object_or_404(
            Incident.objects.prefetch_related("preuves"), pk=pk
        )
        serializer = IncidentSerializer(incident, context={"request": request})
        return Response(serializer.data)
```
Route à ajouter dans `apps/incidents/urls.py` :
```python
path("<int:pk>/", IncidentDetailView.as_view(), name="incident-detail"),
```

### 2. Mise à jour d'un incident par un agent/admin — `PATCH /api/incidents/<id>/`

Vu dans la maquette "Gestion de l'intervention" (changer statut, assigner un agent, définir la priorité, ajouter des notes). Le serializer `IncidentUpdateSerializer` existe déjà (ajouté dans la correction précédente) mais n'est branché nulle part.

```python
from .serializers import IncidentUpdateSerializer
from apps.users.permissions import IsAgentOrAdmin

class IncidentDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAgentOrAdmin()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        ...  # comme ci-dessus

    def patch(self, request, pk):
        incident = get_object_or_404(Incident, pk=pk)
        serializer = IncidentUpdateSerializer(
            incident, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            IncidentSerializer(incident, context={"request": request}).data
        )
```

### 3. Endpoint analyse IA — `POST /api/incidents/<id>/analyse/`

Le modèle `AnalyseIA` et son serializer existent déjà, mais **aucune route ne les expose**. Ton coéquipier IA en aura besoin pour poster ses résultats — à créer même si tu ne fais pas l'IA toi-même, sinon il sera bloqué.

```python
from .models import AnalyseIA
from .serializers import AnalyseIASerializer

class AnalyseIAView(APIView):
    # À restreindre à un compte de service dédié en prod (ex : clé API interne),
    # IsAuthenticated est un minimum en attendant.
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        incident = get_object_or_404(Incident, pk=pk)
        serializer = AnalyseIASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analyse, _ = AnalyseIA.objects.update_or_create(
            incident=incident, defaults=serializer.validated_data
        )
        return Response(
            AnalyseIASerializer(analyse).data, status=status.HTTP_201_CREATED
        )
```
Route :
```python
path("<int:pk>/analyse/", AnalyseIAView.as_view(), name="incident-analyse"),
```
⚠️ Vérifie avec ton coéquipier IA le contrat exact des champs attendus (`type_detecte`, `score_confiance`, `niveau_urgence_detecte`, `description_generee`, `recommandations`) avant qu'il commence à coder contre cet endpoint.

### 4. Filtres et pagination — actuellement inopérants

`django_filters` et `DEFAULT_PAGINATION_CLASS` sont déclarés dans `REST_FRAMEWORK` (settings) mais **ne s'appliquent pas**, car tes vues sont des `APIView` classiques — seuls les `generics.ListAPIView` héritent automatiquement des filter/pagination backends.

**Deux options :**
- **Option A (rapide)** : migrer `IncidentListView.get` vers `generics.ListAPIView` + `filterset_fields`.
- **Option B (garder APIView)** : appliquer manuellement les backends.

Option A recommandée :
```python
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

class IncidentListView(generics.ListCreateAPIView):
    queryset = Incident.objects.prefetch_related("preuves").order_by("-date_creation")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["statut", "type", "niveau_urgence", "quartier"]
    search_fields = ["description", "reference", "adresse"]
    ordering_fields = ["date_creation", "niveau_urgence"]

    def get_serializer_class(self):
        return IncidentCreateSerializer if self.request.method == "POST" else IncidentSerializer

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "POST" else [IsAuthenticated()]

    def perform_create(self, serializer):
        signale_par = self.request.user if self.request.user.is_authenticated else None
        serializer.save(signale_par=signale_par)
```
Nécessaire pour la maquette "Carte des incidents" (filtres par type : Tous/Déchets/Canaux/Voirie) et "Gestion des incidents" (recherche, tri).

### 5. Permissions manquantes sur `interventions`

N'importe quel utilisateur connecté (même un citoyen) peut aujourd'hui créer/modifier une intervention. `IsAgentOrAdmin` existe déjà dans `apps/users/permissions.py` mais n'est pas utilisé dans `apps/interventions/views.py`.

```python
from apps.users.permissions import IsAgentOrAdmin

class InterventionListView(APIView):
    permission_classes = [IsAgentOrAdmin]
    ...

class InterventionDetailView(APIView):
    permission_classes = [IsAgentOrAdmin]
    ...
```

### 6. Rapport de clôture d'intervention — endpoint manquant

Le modèle `Rapport` et son serializer existent, mais **aucune vue ne les utilise**. Nécessaire pour l'écran mobile "Envoyer le rapport" (photo avant/après, PDF).

```python
from .models import Rapport
from .serializers import RapportSerializer

class RapportView(APIView):
    permission_classes = [IsAgentOrAdmin]

    def post(self, request, intervention_id):
        intervention = get_object_or_404(Intervention, pk=intervention_id)
        serializer = RapportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rapport = serializer.save(intervention=intervention)
        return Response(RapportSerializer(rapport).data, status=status.HTTP_201_CREATED)

    def patch(self, request, intervention_id):
        rapport = get_object_or_404(Rapport, intervention_id=intervention_id)
        serializer = RapportSerializer(rapport, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
```
Route dans `apps/interventions/urls.py` :
```python
path("<int:intervention_id>/rapport/", RapportView.as_view(), name="intervention-rapport"),
```

### 7. "Mes interventions" pour un agent — `GET /api/interventions/my/`

Pour l'écran mobile "File d'Interventions" (l'agent voit seulement ses missions assignées) :
```python
class MesInterventionsView(APIView):
    permission_classes = [IsAgentOrAdmin]

    def get(self, request):
        interventions = Intervention.objects.filter(agent=request.user).order_by("-date_debut")
        serializer = InterventionSerializer(interventions, many=True)
        return Response(serializer.data)
```

---

## 🟡 Priorité moyenne — pilotage / gestion (interfaces admin)

### 8. Gestion des agents (CRUD complet)

La maquette web "Gestion des agents" montre : liste avec stats, ajout, modification, suppression, fiche détaillée (incidents résolus, temps moyen, ponctualité, activité hebdo, spécialisation). Aujourd'hui, seul l'admin Django permet ça.

**À créer :** `apps/users/views.py` (ou un nouveau fichier `apps/users/agent_views.py`) :
```python
class AgentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    queryset = Utilisateur.objects.filter(role=Utilisateur.Role.AGENT)
    serializer_class = UtilisateurSerializer  # ou un AgentSerializer dédié avec stats

class AgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdmin]
    queryset = Utilisateur.objects.filter(role=Utilisateur.Role.AGENT)
    serializer_class = UtilisateurSerializer
```
Pour la fiche détaillée avec stats (127 incidents, 22h temps moyen, 94% satisfaction), il faudra un serializer/vue custom qui agrège les données `Incident`/`Intervention` liées à cet agent — à spécifier plus précisément selon les calculs exacts attendus (à valider avec la maquette).

### 9. Journal d'activité exposé — `GET /api/incidents/<id>/journal/`

Le modèle `JournalActivite` existe mais n'a aucun endpoint. Utile pour l'écran "Historique du Rapport" côté mobile.
```python
class JournalActiviteView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JournalActiviteSerializer  # à créer, simple ModelSerializer

    def get_queryset(self):
        return JournalActivite.objects.filter(
            incident_id=self.kwargs["pk"]
        ).order_by("-date")
```

### 10. Dashboard — compléter les statistiques manquantes

L'endpoint actuel ne couvre que les compteurs globaux et la répartition par statut. Manquent, d'après les maquettes :
- **Répartition par type** (donut "184" : déchets/canaux/voirie/éclairage).
- **Évolution des incidents sur 30 jours** (graphique en courbe).
- **Performance des agents** (liste triée par nombre d'interventions résolues).

```python
from django.db.models import Count
from django.db.models.functions import TruncDay
from datetime import timedelta
from django.utils import timezone

def repartition_par_type(self):
    return Incident.objects.values("type").annotate(total=Count("id"))

def evolution_30_jours(self):
    depuis = timezone.now() - timedelta(days=30)
    return (
        Incident.objects.filter(date_creation__gte=depuis)
        .annotate(jour=TruncDay("date_creation"))
        .values("jour")
        .annotate(total=Count("id"))
        .order_by("jour")
    )
```
À intégrer dans la réponse de `apps/dashboard/views.py`.

---

## 🟢 Priorité basse — qualité et robustesse

### 11. Tests manquants sur les autres apps

Seule `users` a une vraie suite de tests (23 tests). `incidents`, `interventions`, `notifications`, `dashboard` n'ont que le stub vide généré par Django. À écrire au fur et à mesure que tu ajoutes les endpoints ci-dessus (chaque nouveau endpoint = au moins un test nominal + un test de permission).

### 12. Sécuriser la rotation des refresh tokens

`ROTATE_REFRESH_TOKENS = True` sans `BLACKLIST_AFTER_ROTATION` : un ancien refresh token reste valide après rotation. Pour une vraie invalidation :
```bash
uv add djangorestframework-simplejwt[blacklist]
```
```python
# settings/base.py
INSTALLED_APPS += ["rest_framework_simplejwt.token_blacklist"]
SIMPLE_JWT["BLACKLIST_AFTER_ROTATION"] = True
```
```bash
uv run python manage.py migrate
```

### 13. Documentation API (Swagger/Redoc)

`drf-spectacular` est déjà installé — vérifie que `/api/docs/` (ou l'URL configurée) est bien monté dans `config/urls.py`, et tiens-le à jour au fil des ajouts ci-dessus : c'est ce que tu peux directement partager avec l'équipe Angular pour qu'elle avance sans attendre tes réponses écrites.

---

## Plan d'action suggéré

| Sprint | Contenu | Pourquoi |
|---|---|---|
| **1** | Points 1 à 4 (détail/update incident, endpoint analyse IA, filtres/pagination) | Débloque le frontend web (gestion des incidents) ET ton coéquipier IA |
| **2** | Points 5 à 7 (permissions interventions, rapport, mes interventions) | Débloque l'app mobile agent |
| **3** | Points 8 à 10 (CRUD agents, journal, dashboard complet) | Débloque le tableau de bord admin |
| **4** | Points 11 à 13 (tests, blacklist JWT, doc API) | Qualité avant mise en production |

Une fois les sprints 1 et 2 terminés, ton backend couvre l'intégralité des parcours visibles dans les 3 maquettes (web admin, mobile agent, mobile citoyen) — le sprint 3 est du "nice to have" pour le pilotage, le sprint 4 est de la robustesse.
