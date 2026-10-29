import os
import json
import logging
import urllib.request
import urllib.error
from django.conf import settings
from .models import Incident, AnalyseIA

logger = logging.getLogger(__name__)

# URL configurable du Microservice IA FastAPI
AI_SERVICE_URL = getattr(settings, "AI_SERVICE_URL", "http://localhost:8001/analyze-image")
# Le service IA enchaîne Hugging Face (10s max) puis OpenRouter (12s max) : 15s ne suffisait pas
AI_SERVICE_TIMEOUT = getattr(settings, "AI_SERVICE_TIMEOUT", 30)


def déclencher_analyse_ia(incident: Incident, preuve_image) -> AnalyseIA | None:
    """
    Transmet l'image de la preuve au Microservice IA FastAPI (http://localhost:8001/analyze-image).
    Enregistre le résultat retourné dans le modèle AnalyseIA et met à jour le type
    et le niveau d'urgence de l'Incident dans la base de données Django.
    """
    if not preuve_image:
        logger.warning(f"[IA Integration] Aucune image disponible pour l'incident #{incident.id}")
        return None

    try:
        logger.info(f"[IA Integration] Envoi de l'image de l'incident #{incident.id} vers {AI_SERVICE_URL}...")

        # Lecture du contenu binaire de l'image
        if hasattr(preuve_image, "path") and os.path.exists(preuve_image.path):
            with open(preuve_image.path, "rb") as f:
                file_content = f.read()
            filename = os.path.basename(preuve_image.name)
        else:
            preuve_image.open()
            file_content = preuve_image.read()
            filename = os.path.basename(preuve_image.name)

        # Construction d'un body multipart/form-data propre avec urllib
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        body_parts = []
        body_parts.append(f"--{boundary}\r\n".encode("utf-8"))
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8")
        )
        body_parts.append(b"Content-Type: image/jpeg\r\n\r\n")
        body_parts.append(file_content)
        body_parts.append(b"\r\n")
        body_parts.append(f"--{boundary}--\r\n".encode("utf-8"))

        body_data = b"".join(body_parts)

        req = urllib.request.Request(
            AI_SERVICE_URL,
            data=body_data,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body_data)),
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=AI_SERVICE_TIMEOUT) as response:
            if response.status == 200:
                resp_text = response.read().decode("utf-8")
                data = json.loads(resp_text)

                type_detecte = data.get("type_detecte", incident.type)
                score_confiance = float(data.get("score_confiance", 0.0))
                niveau_urgence_detecte = data.get("niveau_urgence_detecte", incident.niveau_urgence)
                description_generee = data.get("description_generee", "")
                recommandations = data.get("recommandations", "")

                # Sauvegarde ou mise à jour du modèle AnalyseIA
                analyse, created = AnalyseIA.objects.update_or_create(
                    incident=incident,
                    defaults={
                        "type_detecte": type_detecte,
                        "score_confiance": score_confiance,
                        "niveau_urgence_detecte": niveau_urgence_detecte,
                        "description_generee": description_generee,
                        "recommandations": recommandations,
                    },
                )

                # Si la confiance est suffisante (>= 0.6), ajuster automatiquement le type et l'urgence de l'incident
                if score_confiance >= 0.6:
                    if type_detecte in dict(Incident.TypeIncident.choices):
                        incident.type = type_detecte
                    if niveau_urgence_detecte in dict(Incident.NiveauUrgence.choices):
                        incident.niveau_urgence = niveau_urgence_detecte
                    incident.save(update_fields=["type", "niveau_urgence"])

                logger.info(
                    f"[IA Integration] Analyse IA enregistrée avec succès pour l'incident #{incident.id} "
                    f"(Type: {type_detecte}, Urgence: {niveau_urgence_detecte})"
                )
                return analyse

    except Exception as e:
        logger.warning(f"[IA Integration] Impossible de joindre le service IA FastAPI: {e}")

    return None
