import pytest

from app.core.areas import AREA_BOUNDARY_RULE, AREA_DATASET_VERSION, AREAS


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def radius_payload(expected_revision=0, *, latitude=40.7128, longitude=-74.006, radius_km=25):
    return {
        "expected_revision": expected_revision,
        "coverage": {
            "mode": "RADIUS",
            "location": {"label": "New York City", "latitude": latitude, "longitude": longitude},
            "radius_km": radius_km,
        },
    }


def test_area_catalog_is_the_canonical_area_definition(service_client):
    client, _ = service_client
    response = client.get("/v1/service-areas")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_version"] == AREA_DATASET_VERSION
    assert payload["boundary_rule"] == AREA_BOUNDARY_RULE
    assert {area["id"] for area in payload["areas"]} == set(AREAS)
    assert payload["areas"][0]["label"] == AREAS[payload["areas"][0]["id"]]["label"]


def test_coverage_persists_across_get_requests(service_client):
    client, tokens = service_client
    headers = auth(tokens["owner"])

    initial = client.get("/v1/vendors/vendor-a/service-area", headers=headers)
    assert initial.status_code == 200
    assert initial.json()["coverage"] is None
    assert initial.json()["revision"] == 0

    saved = client.patch(
        "/v1/vendors/vendor-a/service-area",
        headers=headers,
        json=radius_payload(),
    )
    assert saved.status_code == 200
    assert saved.json()["revision"] == 1

    reloaded = client.get("/v1/vendors/vendor-a/service-area", headers=headers)
    assert reloaded.json()["coverage"] == saved.json()["coverage"]
    assert reloaded.json()["revision"] == 1


@pytest.mark.parametrize(
    "payload",
    [
        radius_payload(latitude=91),
        radius_payload(longitude=-181),
        radius_payload(radius_km=0),
        radius_payload(radius_km=501),
        {
            "expected_revision": 0,
            "coverage": {"mode": "AREAS", "area_ids": ["not-a-supported-area"]},
        },
        {
            "expected_revision": 0,
            "coverage": {"mode": "AREAS", "area_ids": ["sf-bay", "sf-bay"]},
        },
    ],
    ids=["invalid-latitude", "invalid-longitude", "radius-too-small", "radius-too-large", "unknown-area-id", "duplicate-area-id"],
)
def test_invalid_geographic_coverage_is_rejected(service_client, payload):
    client, tokens = service_client
    response = client.patch(
        "/v1/vendors/vendor-a/service-area",
        headers=auth(tokens["owner"]),
        json=payload,
    )

    assert response.status_code == 422


def test_organization_cannot_read_or_edit_another_vendors_coverage(service_client):
    client, tokens = service_client
    owner_headers = auth(tokens["owner"])
    other_headers = auth(tokens["other"])
    saved = client.patch(
        "/v1/vendors/vendor-a/service-area",
        headers=owner_headers,
        json=radius_payload(),
    )
    assert saved.status_code == 200

    read = client.get("/v1/vendors/vendor-a/service-area", headers=other_headers)
    edit = client.patch(
        "/v1/vendors/vendor-a/service-area",
        headers=other_headers,
        json=radius_payload(expected_revision=1, radius_km=50),
    )
    assert read.status_code == 404
    assert edit.status_code == 404

    unchanged = client.get("/v1/vendors/vendor-a/service-area", headers=owner_headers)
    assert unchanged.json()["coverage"]["radius_km"] == 25


def test_stale_edit_returns_conflict_and_does_not_overwrite_latest_coverage(service_client):
    client, tokens = service_client
    headers = auth(tokens["owner"])
    first = client.patch(
        "/v1/vendors/vendor-a/service-area",
        headers=headers,
        json=radius_payload(expected_revision=0, radius_km=25),
    )
    stale = client.patch(
        "/v1/vendors/vendor-a/service-area",
        headers=headers,
        json=radius_payload(expected_revision=0, radius_km=50),
    )

    assert first.status_code == 200
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_service_area"
    current = client.get("/v1/vendors/vendor-a/service-area", headers=headers)
    assert current.json()["coverage"]["radius_km"] == 25
