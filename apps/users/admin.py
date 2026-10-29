from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import OTP, Administrateur, Agent, Citoyen, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Informations supplémentaires", {
            "fields": ("role", "telephone", "quartier", "photo_profil", "email_verifie"),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Informations supplémentaires", {
            "fields": ("role", "telephone", "quartier"),
        }),
    )


@admin.register(Citoyen)
class CitoyenAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "nombre_signalements", "nombre_resolus")
    search_fields = ("utilisateur__username", "utilisateur__email")


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "matricule", "departement", "specialisation", "disponible", "score_satisfaction")
    list_filter = ("specialisation", "disponible")
    search_fields = ("utilisateur__username", "matricule")


@admin.register(Administrateur)
class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "niveau_acces")
    search_fields = ("utilisateur__username",)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "code", "date_expiration", "verifie")
    list_filter = ("verifie",)
    search_fields = ("utilisateur__username",)
