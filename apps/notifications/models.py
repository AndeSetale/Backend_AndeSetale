from django.conf import settings
from django.db import models


class Notification(models.Model):
    """Notification envoyée à un utilisateur."""

    class TypeNotification(models.TextChoices):
        PUSH = "PUSH", "Push"
        EMAIL = "EMAIL", "Email"
        SMS = "SMS", "SMS"

    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=10, choices=TypeNotification.choices)
    contenu = models.TextField()
    lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-date_envoi"]

    def __str__(self):
        return f"[{self.get_type_display()}] {self.utilisateur} — lu={self.lu}"
