"""
Migration BE-011 : Remplace Preuve.url (CharField) par Preuve.image (ImageField).

Le champ `url` CharField est retiré et remplacé par `image` ImageField
qui gère l'upload physique des fichiers dans MEDIA_ROOT/preuves/.
"""
from django.db import migrations, models
import apps.incidents.models


class Migration(migrations.Migration):

    dependencies = [
        ("incidents", "0001_initial"),
    ]

    operations = [
        # Supprimer l'ancien champ url (CharField)
        migrations.RemoveField(
            model_name="preuve",
            name="url",
        ),
        # Ajouter le nouveau champ image (ImageField)
        migrations.AddField(
            model_name="preuve",
            name="image",
            field=models.ImageField(
                default="",
                help_text="Image JPG/PNG/WebP, taille max 5 MB",
                upload_to=apps.incidents.models.preuve_upload_path,
            ),
            preserve_default=False,
        ),
    ]
