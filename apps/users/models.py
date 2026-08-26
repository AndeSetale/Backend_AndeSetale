from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class UtilisateurManager(UserManager):

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self._create_user(
            username,
            email,
            password,
            **extra_fields
        )


class Utilisateur(AbstractUser):
    """Modèle utilisateur abstrait commun à tous les rôles."""

    class Role(models.TextChoices):
        CITOYEN = "citoyen", "Citoyen"
        AGENT = "agent", "Agent"
        ADMIN = "admin", "Administrateur"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CITOYEN,
    )
    telephone = models.CharField(max_length=20, blank=True, null=True)
    quartier = models.CharField(max_length=100, blank=True, null=True)
    photo_profil = models.ImageField(
        upload_to="profils/", blank=True, null=True
    )
    email_verifie = models.BooleanField(default=False)
    objects = UtilisateurManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


class Citoyen(models.Model):
    """Profil étendu pour les citoyens."""

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="profil_citoyen",
        limit_choices_to={"role": Utilisateur.Role.CITOYEN},
    )
    nombre_signalements = models.IntegerField(default=0)
    nombre_resolus = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Citoyen"
        verbose_name_plural = "Citoyens"

    def __str__(self):
        return str(self.utilisateur)


class Agent(models.Model):
    """Profil étendu pour les agents de terrain."""

    class TypeIncident(models.TextChoices):
        DECHETS = "DECHETS", "Déchets"
        CANAUX = "CANAUX", "Canaux"
        VOIRIE = "VOIRIE", "Voirie"
        ECLAIRAGE_PUBLIC = "ECLAIRAGE_PUBLIC", "Éclairage public"
        ARBRE = "ARBRE", "Arbre"
        FUITE_EAU = "FUITE_EAU", "Fuite d'eau"

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="profil_agent",
        limit_choices_to={"role": Utilisateur.Role.AGENT},
    )
    matricule = models.CharField(max_length=50, unique=True)
    departement = models.CharField(max_length=100, blank=True, null=True)
    specialisation = models.CharField(
        max_length=30,
        choices=TypeIncident.choices,
        blank=True,
        null=True,
    )
    disponible = models.BooleanField(default=True)
    score_satisfaction = models.FloatField(default=0.0)
    taux_completion = models.FloatField(default=0.0)
    ponctualite = models.FloatField(default=0.0)
    taches_resolues_semaine = models.IntegerField(default=0)
    objectif_hebdo = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Agent"
        verbose_name_plural = "Agents"

    def __str__(self):
        return f"{self.utilisateur} — {self.matricule}"


class Administrateur(models.Model):
    """Profil étendu pour les administrateurs."""

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="profil_admin",
        limit_choices_to={"role": Utilisateur.Role.ADMIN},
    )
    niveau_acces = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Administrateur"
        verbose_name_plural = "Administrateurs"

    def __str__(self):
        return str(self.utilisateur)


class OTP(models.Model):
    """Code OTP pour la vérification (email / SMS)."""

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="otps",
    )
    code = models.CharField(max_length=10)
    date_expiration = models.DateTimeField()
    verifie = models.BooleanField(default=False)

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        ordering = ["-date_expiration"]

    def __str__(self):
        return f"OTP({self.utilisateur}, verifie={self.verifie})"
