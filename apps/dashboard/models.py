from django.db import models


class EvenementSetSetal(models.Model):
    """Journée citoyenne de nettoyage (Set-Setal) annoncée aux citoyens."""

    titre = models.CharField(max_length=150)
    lieu = models.CharField(max_length=150)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Événement Set-Setal"
        verbose_name_plural = "Événements Set-Setal"
        ordering = ["date"]

    def __str__(self):
        return f"{self.titre} ({self.date:%d/%m/%Y})"
