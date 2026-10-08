import pytest

from app.core.areas import AREAS
from app.services.coverage import evaluate_coverage, validate_area_ids
from app.services.geo import distance_km


def test_radius_boundary_is_inclusive():
    assert distance_km(0, 0, 0, 1) == pytest.approx(111.195, abs=0.02)
    result = evaluate_coverage(
        {"mode": "RADIUS", "location": {"latitude": 0, "longitude": 0}, "radius_km": distance_km(0, 0, 0, 1)},
        0,
        1,
    )
    assert result.eligible is True


def test_radius_outside_is_ineligible():
    result = evaluate_coverage(
        {"mode": "RADIUS", "location": {"latitude": 37.7749, "longitude": -122.4194}, "radius_km": 10},
        34.0522,
        -118.2437,
    )
    assert result.eligible is False
    assert result.reason == "outside_radius"


def test_area_dataset_accepts_known_ids_and_rejects_unknown_ids():
    validate_area_ids(["sf-bay"])
    assert "sf-bay" in AREAS
    with pytest.raises(ValueError, match="Unknown area IDs"):
        validate_area_ids(["not-a-real-area"])


def test_area_eligibility_uses_selected_areas():
    coverage = {"mode": "AREAS", "area_ids": ["sf-bay"]}
    assert evaluate_coverage(coverage, 37.7749, -122.4194).eligible is True
    assert evaluate_coverage(coverage, 34.0522, -118.2437).eligible is False
