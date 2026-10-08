"""Assignment demo dataset. Replace with the client-approved authoritative dataset."""

AREA_DATASET_VERSION = "demo-us-metro-v1"
AREAS = {
    "sf-bay": {"label": "San Francisco Bay Area", "center": (37.7749, -122.4194), "radius_km": 90},
    "la-metro": {"label": "Los Angeles Metro", "center": (34.0522, -118.2437), "radius_km": 75},
    "nyc-metro": {"label": "New York City Metro", "center": (40.7128, -74.0060), "radius_km": 70},
}


def area_contains(area_id: str, latitude: float, longitude: float) -> bool:
    """Approximate demo boundaries use a circle around each metro center."""
    area = AREAS.get(area_id)
    if not area:
        return False
    from app.services.geo import distance_km

    return distance_km(latitude, longitude, *area["center"]) <= area["radius_km"]
