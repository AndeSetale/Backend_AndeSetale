"""
Statistiques calculées à partir des interventions réelles.

Utilisées par la gestion des agents (liste + fiche détaillée), le dashboard
agent et le dashboard admin, afin que tous les écrans affichent les mêmes chiffres.
"""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from apps.incidents.models import Incident

from .models import Intervention

# Délai de résolution attendu (en heures) selon l'urgence de l'incident
SLA_HEURES = {
    Incident.NiveauUrgence.CRITIQUE: 24,
    Incident.NiveauUrgence.ELEVE: 48,
    Incident.NiveauUrgence.MODERE: 72,
    Incident.NiveauUrgence.ROUTINE: 168,
}

JOURS_SEMAINE = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def debut_semaine():
    aujourd_hui = timezone.localdate()
    return aujourd_hui - timedelta(days=aujourd_hui.weekday())


def _debut_reference(intervention):
    return intervention.date_assignation or intervention.incident.date_creation


def stats_agent(utilisateur) -> dict:
    """Indicateurs de performance d'un agent (compte Utilisateur)."""
    interventions = list(
        Intervention.objects.filter(agent=utilisateur).select_related("incident")
    )
    terminees = [i for i in interventions if i.statut == Intervention.Statut.TERMINEE and i.date_fin]
    total = len(interventions)

    dans_les_delais = 0
    durees = []
    for intervention in terminees:
        duree = intervention.date_fin - _debut_reference(intervention)
        durees.append(duree.total_seconds() / 3600)
        sla = SLA_HEURES.get(intervention.incident.niveau_urgence, 168)
        if duree <= timedelta(hours=sla):
            dans_les_delais += 1

    lundi = debut_semaine()
    return {
        "interventions_total": total,
        "interventions_terminees": len(terminees),
        "interventions_en_cours": sum(1 for i in interventions if i.statut == Intervention.Statut.EN_COURS),
        "interventions_en_attente": sum(1 for i in interventions if i.statut == Intervention.Statut.EN_ATTENTE),
        "taux_completion": round(len(terminees) * 100 / total) if total else 0,
        "ponctualite": round(dans_les_delais * 100 / len(terminees)) if terminees else 0,
        "temps_moyen_heures": round(sum(durees) / len(durees), 1) if durees else 0,
        "taches_resolues_semaine": sum(
            1 for i in terminees if timezone.localtime(i.date_fin).date() >= lundi
        ),
    }


def activite_semaine_agent(utilisateur) -> list[dict]:
    """Interventions assignées / résolues par jour pour la semaine en cours."""
    lundi = debut_semaine()
    jours = [lundi + timedelta(days=n) for n in range(7)]
    interventions = Intervention.objects.filter(agent=utilisateur)

    def jour(date):
        return timezone.localtime(date).date() if date else None

    assignees = [jour(i.date_assignation) for i in interventions]
    resolues = [jour(i.date_fin) for i in interventions if i.statut == Intervention.Statut.TERMINEE]
    return [
        {
            "jour": JOURS_SEMAINE[n],
            "assignes": assignees.count(date),
            "resolus": resolues.count(date),
        }
        for n, date in enumerate(jours)
    ]


def repartition_types_agent(utilisateur) -> list[dict]:
    """Nombre d'interventions de l'agent par type d'incident."""
    labels = dict(Incident.TypeIncident.choices)
    lignes = (
        Intervention.objects.filter(agent=utilisateur)
        .values("incident__type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    return [
        {"type": l["incident__type"], "label": labels.get(l["incident__type"], l["incident__type"]), "total": l["total"]}
        for l in lignes
    ]


def activites_recentes_agent(utilisateur, limite=10) -> list[dict]:
    """Dernières interventions de l'agent (tableau « activité récente »)."""
    interventions = (
        Intervention.objects.filter(agent=utilisateur)
        .select_related("incident")
        .order_by("-date_assignation", "-id")[:limite]
    )
    return [
        {
            "intervention_id": i.id,
            "numero_suivi": i.numero_suivi,
            "incident_id": i.incident_id,
            "reference": i.incident.reference,
            "type": i.incident.get_type_display(),
            "quartier": i.incident.quartier or i.incident.adresse or "—",
            "date": i.date_fin or i.date_debut or i.date_assignation,
            "statut": i.statut,
            "statut_display": i.get_statut_display(),
        }
        for i in interventions
    ]
