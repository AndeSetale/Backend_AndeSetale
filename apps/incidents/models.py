import uuid

from django.conf import settings
from django.db import models


class Incident(models.Model):
    """Signalement d'un incident urbain par un citoyen."""

    class TypeIncident(models.TextChoices):
        DECHETS = "DECHETS", "Déchets"
        CANAUX = "CANAUX", "Canaux"
        VOIRIE = "VOIRIE", "Voirie"
        ECLAIRAGE_PUBLIC = "ECLAIRAGE_PUBLIC", "Éclairage public"
        ARBRE = "ARBRE", "Arbre"
        FUITE_EAU = "FUITE_EAU", "Fuite d'eau"

    class StatutIncident(models.TextChoices):
        NOUVEAU = "NOUVEAU", "Nouveau"
        EN_COURS = "EN_COURS", "En cours"
        RESOLU = "RESOLU", "Résolu"

    class NiveauUrgence(models.TextChoices):
        CRITIQUE = "CRITIQUE", "Critique"
        ELEVE = "ELEVE", "Élevé"
        MODERE = "MODERE", "Modéré"
        ROUTINE = "ROUTINE", "Routine"

    reference = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=30, choices=TypeIncident.choices)
    description = models.TextField()
    statut = models.CharField(
        max_length=20,
        choices=StatutIncident.choices,
        default=StatutIncident.NOUVEAU,
    )
    niveau_urgence = models.CharField(
        max_length=20,
        choices=NiveauUrgence.choices,
        default=NiveauUrgence.ROUTINE,
    )
    quartier = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_estimation_heures = models.IntegerField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)

    # Relations
    signale_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="incidents_signales",
    )
    assigne_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents_assignes",
    )

    class Meta:
        verbose_name = "Incident"
        verbose_name_plural = "Incidents"
        ordering = ["-date_creation"]

    def save(self, *args, **kwargs):
        # Génère automatiquement une référence unique à la première sauvegarde.
        # Format : INC-XXXXXXXX  (8 caractères hex tirés d'un UUID4)
        if not self.reference:
            self.reference = f"INC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.reference}] {self.get_type_display()} — {self.get_statut_display()}"


class Preuve(models.Model):
    """Photo ou document attaché à un incident."""

    class TypePreuve(models.TextChoices):
        PHOTO_INITIALE = "PHOTO_INITIALE", "Photo initiale"
        PHOTO_AVANT = "PHOTO_AVANT", "Photo avant"
        PHOTO_APRES = "PHOTO_APRES", "Photo après"

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="preuves",
    )
    type = models.CharField(max_length=20, choices=TypePreuve.choices)
    image = models.ImageField(upload_to="preuves/%Y/%m/", blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Preuve"
        verbose_name_plural = "Preuves"
        ordering = ["date_ajout"]

    def __str__(self):
        return f"{self.get_type_display()} — Incident #{self.incident_id}"


class AnalyseIA(models.Model):
    """Analyse automatique d'un incident par IA."""

    class NiveauUrgence(models.TextChoices):
        CRITIQUE = "CRITIQUE", "Critique"
        ELEVE = "ELEVE", "Élevé"
        MODERE = "MODERE", "Modéré"
        ROUTINE = "ROUTINE", "Routine"

    incident = models.OneToOneField(
        Incident,
        on_delete=models.CASCADE,
        related_name="analyse_ia",
    )
    type_detecte = models.CharField(
        max_length=30,
        choices=Incident.TypeIncident.choices,
        blank=True,
        null=True,
    )
    score_confiance = models.FloatField(default=0.0)
    niveau_urgence_detecte = models.CharField(
        max_length=20,
        choices=NiveauUrgence.choices,
        blank=True,
        null=True,
    )
    description_generee = models.TextField(blank=True, null=True)
    recommandations = models.TextField(blank=True, null=True)
    date_analyse = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Analyse IA"
        verbose_name_plural = "Analyses IA"

    def __str__(self):
        return f"AnalyseIA — Incident #{self.incident_id} (confiance: {self.score_confiance:.0%})"


class JournalActivite(models.Model):
    """Trace de toute action effectuée sur le système."""

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="journal_activites",
    )
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activité"
        ordering = ["-date_action"]

    def __str__(self):
        return f"{self.utilisateur} — {self.action} ({self.date_action:%Y-%m-%d %H:%M})"
