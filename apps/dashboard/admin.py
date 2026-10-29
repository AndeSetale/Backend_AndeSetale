from django.contrib import admin

from .models import EvenementSetSetal


@admin.register(EvenementSetSetal)
class EvenementSetSetalAdmin(admin.ModelAdmin):
    list_display = ("titre", "lieu", "date")
    ordering = ("-date",)
