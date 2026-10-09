"""Canonical shared service-area catalog and demo boundary geometry."""

AREA_DATASET_VERSION = "demo-us-metro-v1"
AREA_BOUNDARY_RULE = "Each metro is a circle around its published center; points exactly on the radius are included."
AREAS = {
    "sf-bay": {
        "label": "San Francisco Bay Area",
        "detail": "San Francisco, Oakland, San Jose",
        "center": (37.7749, -122.4194),
        "radius_km": 90,
    },
    "la-metro": {
        "label": "Los Angeles Metro",
        "detail": "Los Angeles, Long Beach, Anaheim",
        "center": (34.0522, -118.2437),
        "radius_km": 75,
    },
    "nyc-metro": {
        "label": "New York City Metro",
        "detail": "New York, Newark, Jersey City",
        "center": (40.7128, -74.0060),
        "radius_km": 70,
    },
}


def area_contains(area_id: str, latitude: float, longitude: float) -> bool:
    """Approximate demo boundaries use a circle around each metro center."""
    area = AREAS.get(area_id)
    if not area:
        return False
    from app.services.geo import distance_km

    return distance_km(latitude, longitude, *area["center"]) <= area["radius_km"]
