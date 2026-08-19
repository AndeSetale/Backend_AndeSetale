import uuid

from django.conf import settings
from django.db import models

from apps.incidents.models import Incident


class Intervention(models.Model):
    """Intervention terrain déclenchée suite à un incident."""

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        EN_COURS = "EN_COURS", "En cours"
        TERMINEE = "TERMINEE", "Terminée"

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="interventions",
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interventions",
    )
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
    )
    date_debut = models.DateTimeField(blank=True, null=True)
    date_fin = models.DateTimeField(blank=True, null=True)
    numero_suivi = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Intervention"
        verbose_name_plural = "Interventions"
        ordering = ["-date_debut"]

    def save(self, *args, **kwargs):
        # Génère automatiquement un numéro de suivi à la première sauvegarde.
        # Format : INT-XXXXXXXX  (8 caractères hex tirés d'un UUID4)
        if not self.numero_suivi:
            self.numero_suivi = f"INT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Intervention {self.numero_suivi} — {self.get_statut_display()}"


class Rapport(models.Model):
    """Rapport photo de clôture d'une intervention."""

    intervention = models.OneToOneField(
        Intervention,
        on_delete=models.CASCADE,
        related_name="rapport",
    )

    photo_avant = models.ImageField(
        upload_to="rapports/avant/",
        null=True,
        blank=True
    )

    photo_apres = models.ImageField(
        upload_to="rapports/apres/",
        null=True,
        blank=True
    )

    date_envoi = models.DateTimeField(
        auto_now_add=True
    )

    statut = models.CharField(
        max_length=50,
        default="ENVOYE"
    )

    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"

    def __str__(self):
        return f"Rapport — Intervention {self.intervention.numero_suivi}"