import json
import random
from pathlib import Path

import requests
from shapely.geometry import shape, Point


API_URL = "http://127.0.0.1:8000/api/incidents/"

GEOJSON_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "plateau_polygon.geojson"
)


# --------------------------------------------------
# Chargement du périmètre de Dakar-Plateau
# --------------------------------------------------

def charger_polygone():

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        geometrie = data[0]["geojson"]

    elif isinstance(data, dict) and "features" in data:
        geometrie = data["features"][0]["geometry"]

    elif isinstance(data, dict) and "geometry" in data:
        geometrie = data["geometry"]

    elif isinstance(data, dict) and "coordinates" in data:
        geometrie = data

    else:
        raise ValueError("Format GeoJSON non reconnu.")

    return shape(geometrie)


PLATEAU_SHAPE = charger_polygone()


# --------------------------------------------------
# Données
# --------------------------------------------------

QUARTIERS_LABELS = [
    {
        "nom": "Plateau",
        "rues": [
            "Rue de Thiong",
            "Avenue Léopold Sédar Senghor",
            "Rue Vincens",
            "Place de l'Indépendance",
            "Avenue Georges Pompidou",
            "Rue Félix Faure",
            "Rue Thiers",
            "Boulevard de la République",
            "Avenue Faidherbe",
            "Marché Sandaga",
            "Rue Parchappe",
        ],
    },
]


TYPES = [
    "DECHETS",
    "CANAUX",
    "VOIRIE",
    "ECLAIRAGE_PUBLIC",
    "ARBRE",
    "FUITE_EAU",
]


URGENCES = [
    "CRITIQUE",
    "ELEVE",
    "MODERE",
    "ROUTINE",
]


DESCRIPTIONS = {
    "DECHETS": "Accumulation de déchets ménagers sur la voie publique.",
    "CANAUX": "Canal d'évacuation obstrué, risque d'inondation.",
    "VOIRIE": "Nid-de-poule important gênant la circulation.",
    "ECLAIRAGE_PUBLIC": "Lampadaire hors service depuis plusieurs jours.",
    "ARBRE": "Arbre penché menaçant de tomber sur la chaussée.",
    "FUITE_EAU": "Fuite d'eau importante sur le réseau SDE.",
}


# --------------------------------------------------
# Génération d'un point dans Dakar-Plateau
# --------------------------------------------------

def point_aleatoire_dans_plateau():

    minx, miny, maxx, maxy = PLATEAU_SHAPE.bounds

    while True:

        point = Point(
            random.uniform(minx, maxx),
            random.uniform(miny, maxy)
        )

        if PLATEAU_SHAPE.contains(point):

            # Shapely = x,y = longitude, latitude
            return point.y, point.x


# --------------------------------------------------
# Seed
# --------------------------------------------------

def seed(n=15):

    for i in range(n):

        quartier = random.choice(QUARTIERS_LABELS)
        type_incident = random.choice(TYPES)

        latitude, longitude = point_aleatoire_dans_plateau()

        payload = {
            "type": type_incident,
            "description": DESCRIPTIONS[type_incident],
            "niveau_urgence": random.choice(URGENCES),

            "quartier": quartier["nom"],

            "adresse": (
                f"{random.choice(quartier['rues'])}, "
                f"{quartier['nom']}"
            ),

            "latitude": latitude,
            "longitude": longitude,

            "date_estimation_heures": random.choice([
                24,
                48,
                72
            ]),

            "commentaire": "",
        }

        response = requests.post(
            API_URL,
            json=payload
        )

        try:
            data = response.json()
        except Exception:
            data = response.text

        print(
            f"[{i + 1}/{n}] "
            f"{response.status_code} "
            f"{quartier['nom']} "
            f"{type_incident} "
            f"→ {data.get('reference', data) if isinstance(data, dict) else data}"
        )


if __name__ == "__main__":
    seed(15)