from django.contrib import admin

from .models import Intervention, Rapport


class RapportInline(admin.StackedInline):
    model = Rapport
    extra = 0
    readonly_fields = ("date_envoi",)


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ("numero_suivi", "incident", "agent", "statut", "date_debut", "date_fin")
    list_filter = ("statut",)
    search_fields = ("numero_suivi", "incident__reference", "agent__username")
    readonly_fields = ("date_debut",)
    inlines = [RapportInline]


@admin.register(Rapport)
class RapportAdmin(admin.ModelAdmin):
    list_display = ("intervention", "statut", "date_envoi")
    readonly_fields = ("date_envoi",)
