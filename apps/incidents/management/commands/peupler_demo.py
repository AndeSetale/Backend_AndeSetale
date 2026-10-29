"""
Peuple la base avec un jeu de données de démonstration cohérent.

    python manage.py peupler_demo           # crée les données (idempotent : refuse si déjà présentes)
    python manage.py peupler_demo --reset   # supprime puis recrée les données de démonstration

Tous les comptes créés utilisent le domaine @demo.andesetal.sn et le mot de passe
MOT_DE_PASSE ci-dessous. Les autres comptes de la base ne sont jamais modifiés.

Les incidents suivent le vrai workflow métier (assignation → intervention → rapport →
résolution) afin que dashboards, statistiques agents et notifications soient cohérents.
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from shapely.geometry import Point

from apps.dashboard.models import EvenementSetSetal
from apps.incidents.geo import PLATEAU_SHAPE
from apps.incidents.models import Incident
from apps.interventions.models import Intervention, Rapport
from apps.interventions.workflow import assigner_incident, terminer_intervention
from apps.users.models import Agent, Utilisateur

DOMAINE = "demo.andesetal.sn"
MOT_DE_PASSE = "Demo2026!"
MARQUEUR_EVENEMENT = "(données de démonstration)"

AGENTS = [
    ("Moussa", "Diop", "AG-001", "Assainissement", "DECHETS"),
    ("Aïssatou", "Sow", "AG-002", "Assainissement", "CANAUX"),
    ("Abdoulaye", "Ndiaye", "AG-003", "Voirie", "VOIRIE"),
    ("Fatou", "Faye", "AG-004", "Éclairage public", "ECLAIRAGE_PUBLIC"),
    ("Ibrahima", "Sarr", "AG-005", "Espaces verts", "ARBRE"),
]

CITOYENS = [
    ("Awa", "Diallo"), ("Mamadou", "Ba"), ("Khady", "Gueye"), ("Ousmane", "Fall"),
    ("Mariama", "Cissé"), ("Cheikh", "Mbaye"), ("Ndeye", "Thiam"), ("Babacar", "Seck"),
]

RUES = [
    "Avenue Léopold Sédar Senghor", "Rue Mohamed V", "Avenue Georges Pompidou",
    "Rue Jules Ferry", "Boulevard de la République", "Avenue Hassan II",
    "Rue Félix Faure", "Place de l'Indépendance", "Rue Carnot", "Avenue Lamine Guèye",
    "Marché Kermel", "Rue Vincens", "Avenue Pasteur", "Rue Wagane Diouf", "Corniche Est",
]

DESCRIPTIONS = {
    "DECHETS": [
        "Dépôt sauvage d'ordures ménagères sur le trottoir.",
        "Bacs à ordures débordants depuis plusieurs jours.",
        "Sacs plastiques et gravats abandonnés près du marché.",
    ],
    "CANAUX": [
        "Caniveau bouché par le sable et les déchets, l'eau stagne.",
        "Bouche d'égout obstruée, risque d'inondation à la prochaine pluie.",
    ],
    "VOIRIE": [
        "Nid-de-poule profond au milieu de la chaussée.",
        "Trottoir effondré, dangereux pour les piétons.",
    ],
    "ECLAIRAGE_PUBLIC": [
        "Lampadaire éteint depuis une semaine, rue très sombre la nuit.",
        "Câble électrique apparent au pied d'un candélabre.",
    ],
    "ARBRE": [
        "Grosse branche cassée qui menace de tomber sur la route.",
        "Arbre penché après le vent, gêne la circulation.",
    ],
    "FUITE_EAU": [
        "Fuite d'eau importante sur la canalisation, la rue est inondée.",
        "Eau qui jaillit d'une conduite cassée depuis ce matin.",
    ],
}

URGENCE_PAR_TYPE = {
    "DECHETS": ["ELEVE", "MODERE", "ROUTINE"],
    "CANAUX": ["CRITIQUE", "ELEVE"],
    "VOIRIE": ["ELEVE", "MODERE"],
    "ECLAIRAGE_PUBLIC": ["MODERE", "ROUTINE"],
    "ARBRE": ["CRITIQUE", "MODERE"],
    "FUITE_EAU": ["CRITIQUE", "ELEVE"],
}

EVENEMENTS = [
    ("Set-Setal du Marché Kermel", "Marché Kermel", 9),
    ("Nettoyage de la Corniche Est", "Corniche Est", 23),
]


class Command(BaseCommand):
    help = "Peuple la base avec des données de démonstration (comptes @demo.andesetal.sn)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Supprime puis recrée les données de démonstration.")

    def handle(self, *args, reset=False, **options):
        self.rng = random.Random(2026)  # données identiques à chaque exécution

        if reset:
            self.supprimer()
        elif Utilisateur.objects.filter(email__endswith=f"@{DOMAINE}").exists():
            self.stdout.write(self.style.WARNING(
                "Des données de démonstration existent déjà. Utilisez --reset pour les recréer."
            ))
            return

        with transaction.atomic():
            admin = self.creer_utilisateur("admin", "Superviseur", "Mairie", Utilisateur.Role.ADMIN)
            agents = self.creer_agents()
            citoyens = [
                self.creer_utilisateur(f"{p.lower()}.{n.lower()}", p, n, Utilisateur.Role.CITOYEN)
                for p, n in CITOYENS
            ]
            stats = self.creer_incidents(citoyens, agents)
            self.creer_evenements()

        self.stdout.write(self.style.SUCCESS(
            f"Données créées : 1 admin, {len(agents)} agents, {len(citoyens)} citoyens, "
            f"{sum(stats.values())} incidents ({stats['NOUVEAU']} nouveaux, "
            f"{stats['EN_COURS']} en cours, {stats['RESOLU']} résolus), {len(EVENEMENTS)} événements."
        ))
        self.stdout.write(f"Connexion admin : {admin.email} / {MOT_DE_PASSE}")
        # Agent conseillé pour la démo : celui qui a le plus d'interventions à démarrer
        agent_demo = max(
            agents,
            key=lambda a: Intervention.objects.filter(agent=a, statut=Intervention.Statut.EN_ATTENTE).count(),
        )
        self.stdout.write(f"Connexion agent : {agent_demo.email} / {MOT_DE_PASSE}")
        self.stdout.write(f"Connexion citoyen : {citoyens[0].email} / {MOT_DE_PASSE}")

    # ------------------------------------------------------------------

    def supprimer(self):
        demo = Utilisateur.objects.filter(email__endswith=f"@{DOMAINE}")
        incidents = Incident.objects.filter(signale_par__in=demo)
        nb_incidents = incidents.count()
        incidents.delete()  # cascade : preuves, analyses, interventions, rapports
        nb_comptes = demo.count()
        demo.delete()  # cascade : profils agent, notifications, OTP
        EvenementSetSetal.objects.filter(description__contains=MARQUEUR_EVENEMENT).delete()
        self.stdout.write(f"Supprimé : {nb_comptes} comptes et {nb_incidents} incidents de démonstration.")

    def creer_utilisateur(self, identifiant, prenom, nom, role):
        user = Utilisateur(
            username=f"demo_{identifiant}".replace("ï", "i").replace(" ", "")[:150],
            email=f"{identifiant}@{DOMAINE}".replace("ï", "i"),
            first_name=prenom,
            last_name=nom,
            role=role,
            quartier="Plateau",
            telephone=f"77{self.rng.randint(1000000, 9999999)}",
            email_verifie=True,
        )
        user.set_password(MOT_DE_PASSE)
        user.save()
        return user

    def creer_agents(self):
        agents = []
        for prenom, nom, matricule, departement, specialisation in AGENTS:
            user = self.creer_utilisateur(f"{prenom.lower()}.{nom.lower()}", prenom, nom, Utilisateur.Role.AGENT)
            Agent.objects.create(
                utilisateur=user,
                matricule=matricule,
                departement=departement,
                specialisation=specialisation,
                objectif_hebdo=8,
                disponible=True,
            )
            agents.append(user)
        return agents

    def point_au_plateau(self):
        minx, miny, maxx, maxy = PLATEAU_SHAPE.bounds
        while True:
            lng, lat = self.rng.uniform(minx, maxx), self.rng.uniform(miny, maxy)
            if PLATEAU_SHAPE.contains(Point(lng, lat)):
                return round(lat, 6), round(lng, 6)

    def creer_incidents(self, citoyens, agents):
        maintenant = timezone.now()
        agent_par_type = {
            Agent.objects.get(utilisateur=a).specialisation: a for a in agents
        }
        stats = {"NOUVEAU": 0, "EN_COURS": 0, "RESOLU": 0}

        for n in range(40):
            type_incident = self.rng.choice(list(DESCRIPTIONS))
            lat, lng = self.point_au_plateau()
            cree_le = maintenant - timedelta(days=self.rng.uniform(0, 29), hours=self.rng.uniform(0, 10))

            incident = Incident.objects.create(
                type=type_incident,
                description=self.rng.choice(DESCRIPTIONS[type_incident]),
                niveau_urgence=self.rng.choice(URGENCE_PAR_TYPE[type_incident]),
                quartier="Plateau",
                adresse=self.rng.choice(RUES),
                latitude=lat,
                longitude=lng,
                signale_par=self.rng.choice(citoyens),
            )
            Incident.objects.filter(pk=incident.pk).update(date_creation=cree_le)
            incident.refresh_from_db()

            # Les signalements du jour sont encore à traiter ; les autres se répartissent
            # entre en cours et résolus (y compris cette semaine, pour les indicateurs hebdo)
            age_heures = (maintenant - cree_le).total_seconds() / 3600
            sort = "NOUVEAU" if age_heures < 20 or n % 5 == 0 else ("EN_COURS" if n % 3 == 0 else "RESOLU")

            if sort != "NOUVEAU":
                agent = agent_par_type.get(type_incident) or self.rng.choice(agents)
                intervention = assigner_incident(incident, agent)
                assigne_le = cree_le + timedelta(hours=self.rng.uniform(1, 12))
                Intervention.objects.filter(pk=intervention.pk).update(date_assignation=assigne_le)
                intervention.refresh_from_db()

                if sort == "EN_COURS" and n % 2 == 0:
                    intervention.statut = Intervention.Statut.EN_COURS
                    intervention.date_debut = assigne_le + timedelta(hours=2)
                    intervention.save(update_fields=["statut", "date_debut"])

                if sort == "RESOLU":
                    Rapport.objects.create(intervention=intervention)
                    terminer_intervention(intervention)
                    fini_le = min(assigne_le + timedelta(hours=self.rng.uniform(4, 60)), maintenant)
                    Intervention.objects.filter(pk=intervention.pk).update(
                        date_debut=assigne_le + timedelta(hours=1), date_fin=fini_le
                    )
                    Incident.objects.filter(pk=incident.pk).update(date_resolution=fini_le)

            stats[sort] += 1
        return stats

    def creer_evenements(self):
        for titre, lieu, dans_jours in EVENEMENTS:
            EvenementSetSetal.objects.create(
                titre=titre,
                lieu=lieu,
                date=(timezone.now() + timedelta(days=dans_jours)).replace(hour=8, minute=0, second=0, microsecond=0),
                description=f"Journée citoyenne de nettoyage {MARQUEUR_EVENEMENT}",
            )
