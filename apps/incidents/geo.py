# apps/incidents/geo.py
import json
from pathlib import Path
from shapely.geometry import shape, Point

GEOJSON_PATH = Path(__file__).resolve().parent / "data" / "plateau_polygon.geojson"


def _charger_polygone():
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        # Réponse brute de Nominatim : une liste de résultats
        geometrie = data[0]["geojson"]
    elif isinstance(data, dict) and "features" in data:
        # FeatureCollection standard
        geometrie = data["features"][0]["geometry"]
    elif isinstance(data, dict) and "geometry" in data:
        # Un objet Feature seul
        geometrie = data["geometry"]
    elif isinstance(data, dict) and "coordinates" in data:
        # Déjà une géométrie brute
        geometrie = data
    else:
        raise ValueError(f"Structure GeoJSON non reconnue dans {GEOJSON_PATH}")

    return shape(geometrie)


PLATEAU_SHAPE = _charger_polygone()


def point_dans_plateau(lat: float, lng: float) -> bool:
    """Vérifie si un point (lat, lng) est dans le périmètre de l'arrondissement Dakar-Plateau."""
    return PLATEAU_SHAPE.contains(Point(lng, lat))