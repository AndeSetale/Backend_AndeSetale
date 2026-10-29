from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "type", "lu", "date_envoi")
    list_filter = ("type", "lu")
    search_fields = ("utilisateur__username", "contenu")
    readonly_fields = ("date_envoi",)
