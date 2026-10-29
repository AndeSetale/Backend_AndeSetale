"""
Workflow métier reliant incidents, interventions et notifications.

Cycle complet :
  1. Le citoyen signale un incident                 → Incident NOUVEAU
  2. L'admin assigne un agent (assigner_incident)   → Incident EN_COURS + Intervention EN_ATTENTE
  3. L'agent démarre l'intervention                 → Intervention EN_COURS
  4. L'agent envoie son rapport (terminer_intervention)
                                                    → Intervention TERMINEE + Incident RESOLU

Ces fonctions sont appelées depuis les vues incidents ET interventions afin que
les deux côtés (dashboard admin et application agent) restent toujours synchronisés.
"""

from django.db import transaction
from django.utils import timezone

from apps.incidents.models import Incident
from apps.notifications.models import Notification

from .models import Intervention


def notifier(utilisateur, contenu: str) -> None:
    """Crée une notification in-app (PUSH) si le destinataire existe."""
    if utilisateur is not None:
        Notification.objects.create(
            utilisateur=utilisateur,
            type=Notification.TypeNotification.PUSH,
            contenu=contenu,
        )


@transaction.atomic
def assigner_incident(incident: Incident, agent) -> Intervention:
    """
    Assigne un agent à un incident.

    Réutilise l'intervention ouverte de l'incident (réassignation) ou en crée une
    nouvelle, puis passe l'incident EN_COURS.
    """
    intervention = (
        incident.interventions
        .exclude(statut=Intervention.Statut.TERMINEE)
        .first()
    )
    if intervention is None:
        intervention = Intervention.objects.create(incident=incident, agent=agent)
    elif intervention.agent_id != agent.id:
        intervention.agent = agent
        intervention.date_assignation = timezone.now()
        intervention.save(update_fields=["agent", "date_assignation"])

    incident.assigne_a = agent
    if incident.statut == Incident.StatutIncident.NOUVEAU:
        incident.statut = Incident.StatutIncident.EN_COURS
    incident.save(update_fields=["assigne_a", "statut"])

    notifier(
        agent,
        f"Nouvelle intervention {intervention.numero_suivi} : "
        f"{incident.get_type_display()} — {incident.adresse or incident.quartier or 'Dakar Plateau'}.",
    )
    notifier(
        incident.signale_par,
        f"Votre signalement {incident.reference} a été pris en charge par un agent.",
    )
    return intervention


@transaction.atomic
def terminer_intervention(intervention: Intervention) -> Intervention:
    """Clôture l'intervention et marque l'incident associé comme résolu."""
    maintenant = timezone.now()

    if intervention.statut != Intervention.Statut.TERMINEE:
        intervention.statut = Intervention.Statut.TERMINEE
        intervention.date_debut = intervention.date_debut or maintenant
        intervention.date_fin = maintenant
        intervention.save(update_fields=["statut", "date_debut", "date_fin"])

    resoudre_incident(intervention.incident)
    return intervention


def resoudre_incident(incident: Incident) -> None:
    """Passe l'incident RESOLU (une seule fois) et prévient le citoyen."""
    if incident.statut == Incident.StatutIncident.RESOLU and incident.date_resolution:
        return
    incident.statut = Incident.StatutIncident.RESOLU
    incident.date_resolution = incident.date_resolution or timezone.now()
    incident.save(update_fields=["statut", "date_resolution"])
    notifier(
        incident.signale_par,
        f"Bonne nouvelle : votre signalement {incident.reference} a été résolu. Merci pour votre vigilance !",
    )
