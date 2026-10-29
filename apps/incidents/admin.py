from django.contrib import admin

from .models import AnalyseIA, Incident, JournalActivite, Preuve


class PreuveInline(admin.TabularInline):
    model = Preuve
    extra = 0
    readonly_fields = ("date_ajout",)


class AnalyseIAInline(admin.StackedInline):
    model = AnalyseIA
    extra = 0
    readonly_fields = ("date_analyse",)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "type", "statut", "niveau_urgence",
        "quartier", "signale_par", "assigne_a", "date_creation",
    )
    list_filter = ("statut", "type", "niveau_urgence")
    search_fields = ("reference", "description", "quartier", "adresse")
    readonly_fields = ("date_creation",)
    inlines = [PreuveInline, AnalyseIAInline]


@admin.register(Preuve)
class PreuveAdmin(admin.ModelAdmin):
    list_display = ("incident", "type", "date_ajout")
    list_filter = ("type",)
    readonly_fields = ("date_ajout",)


@admin.register(AnalyseIA)
class AnalyseIAAdmin(admin.ModelAdmin):
    list_display = ("incident", "type_detecte", "score_confiance", "niveau_urgence_detecte", "date_analyse")
    readonly_fields = ("date_analyse",)


@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "action", "date_action")
    search_fields = ("utilisateur__username", "action")
    readonly_fields = ("date_action",)
