"""
Utilitaires OTP — génération, envoi par email, durée de validité.

Valeurs fixées (à ajuster si besoin, mais garder cohérent avec le frontend) :
- Durée de validité du code : 10 minutes
- Délai minimum avant de pouvoir redemander un code : 60 secondes
"""

import random
from datetime import timedelta

from django.core.mail import send_mail
from django.utils import timezone

from .models import OTP

OTP_VALIDITY_MINUTES = 1
OTP_RESEND_COOLDOWN_SECONDS = 60


def generate_otp_code():
    """Génère un code numérique à 6 chiffres."""
    return f"{random.randint(0, 999999):06d}"


def create_and_send_otp(utilisateur):
    """
    Crée un nouvel OTP pour l'utilisateur et l'envoie par email.

    Retourne le code généré (utile pour les tests / logs en dev,
    ne jamais le retourner dans une réponse API).
    """
    code = generate_otp_code()
    OTP.objects.create(
        utilisateur=utilisateur,
        code=code,
        date_expiration=timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES),
    )

    if utilisateur.email:
        send_mail(
            subject="Andë Sétal — Votre code de vérification",
            message=(
                f"Bonjour {utilisateur.get_full_name() or utilisateur.username},\n\n"
                f"Votre code de vérification est : {code}\n"
                f"Ce code expire dans {OTP_VALIDITY_MINUTES} minutes.\n\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
            ),
            from_email=None,  # utilise DEFAULT_FROM_EMAIL
            recipient_list=[utilisateur.email],
            fail_silently=False,
        )

    return code


def can_resend_otp(utilisateur):
    """
    Vérifie si le délai de cooldown (60s) est écoulé depuis le dernier OTP envoyé.
    Retourne (autorisé: bool, secondes_restantes: int).
    """
    dernier_otp = utilisateur.otps.order_by("-id").first()
    if dernier_otp is None:
        return True, 0

    date_creation_dernier = dernier_otp.date_expiration - timedelta(
        minutes=OTP_VALIDITY_MINUTES
    )
    ecoule = (timezone.now() - date_creation_dernier).total_seconds()
    if ecoule >= OTP_RESEND_COOLDOWN_SECONDS:
        return True, 0
    return False, int(OTP_RESEND_COOLDOWN_SECONDS - ecoule)
