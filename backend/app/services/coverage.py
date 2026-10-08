from app.core.areas import AREAS, area_contains
from app.models.service_area import ServiceArea
from app.schemas.service_area import AreasCoverage, EligibilityResponse, RadiusCoverage
from app.services.geo import distance_km


def validate_area_ids(area_ids: list[str]) -> None:
    unknown = sorted(set(area_ids) - AREAS.keys())
    if unknown:
        raise ValueError(f"Unknown area IDs: {', '.join(unknown)}")
    if len(set(area_ids)) != len(area_ids):
        raise ValueError("Area IDs must be unique")


def evaluate_coverage(coverage: dict, latitude: float, longitude: float, area_id: str | None = None) -> EligibilityResponse:
    if coverage["mode"] == "RADIUS":
        location = coverage["location"]
        inside = distance_km(latitude, longitude, location["latitude"], location["longitude"]) <= coverage["radius_km"]
        return EligibilityResponse(eligible=inside, reason="within_radius" if inside else "outside_radius")
    if area_id:
        inside = area_id in coverage["area_ids"] and area_contains(area_id, latitude, longitude)
        return EligibilityResponse(eligible=inside, reason="inside_selected_area" if inside else "outside_selected_areas")
    inside = any(area_contains(candidate, latitude, longitude) for candidate in coverage["area_ids"])
    return EligibilityResponse(eligible=inside, reason="inside_selected_area" if inside else "outside_selected_areas")
