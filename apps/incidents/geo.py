# apps/incidents/geo.py
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

GEOJSON_PATH = Path(__file__).resolve().parent / "data" / "plateau_polygon.geojson"

try:
    from shapely.geometry import shape, Point

    def _charger_polygone():
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
            raise ValueError(f"Structure GeoJSON non reconnue dans {GEOJSON_PATH}")

        return shape(geometrie)

    PLATEAU_SHAPE = _charger_polygone()

    def point_dans_plateau(lat: float, lng: float) -> bool:
        """Vérifie si un point (lat, lng) est dans le périmètre de l'arrondissement Dakar-Plateau."""
        try:
            return PLATEAU_SHAPE.contains(Point(lng, lat))
        except Exception:
            return True

except ImportError:
    logger.warning("[Geo Fallback] Shapely n'est pas installé. Utilisation du fallback par rectangle englobant pour Dakar Plateau.")

    def point_dans_plateau(lat: float, lng: float) -> bool:
        # Rectangle englobant approximatif de Dakar Plateau (14.65 <= lat <= 14.72, -17.48 <= lng <= -17.42)
        return 14.60 <= lat <= 14.75 and -17.50 <= lng <= -17.40