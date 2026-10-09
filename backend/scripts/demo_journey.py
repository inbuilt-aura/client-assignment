"""Exercise the running API and internal eligibility function for a live demo."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.api.dependencies import Principal
from app.api.routes import check_event_eligibility
from app.db.session import SessionLocal
from app.schemas.service_area import EligibilityRequest


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
DEMO_EMAIL = "coverage-walkthrough@nova.test"
DEMO_PASSWORD = "NOVA-demo-2026!"
DEMO_VENDOR_ID = "vendor-walkthrough"


def request_json(path: str, *, method: str = "GET", token: str | None = None, body: dict | None = None):
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{API_BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=10) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} failed ({error.code}): {detail}") from error
    except URLError as error:
        raise RuntimeError(f"Cannot reach {API_BASE_URL}: {error.reason}") from error


def main() -> None:
    login = request_json(
        "/auth/login",
        method="POST",
        body={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    token = login["access_token"]
    user = request_json("/auth/me", token=token)
    assert user["vendor_id"] == DEMO_VENDOR_ID, f"Unexpected demo vendor: {user['vendor_id']}"
    print(f"PASS sign in: {user['email']} → {user['vendor_id']}")

    initial = request_json(f"/vendors/{DEMO_VENDOR_ID}/service-area", token=token)
    first_save = request_json(
        f"/vendors/{DEMO_VENDOR_ID}/service-area",
        method="PATCH",
        token=token,
        body={
            "expected_revision": initial["revision"],
            "coverage": {
                "mode": "RADIUS",
                "location": {"label": "New York City", "latitude": 40.7128, "longitude": -74.0060},
                "radius_km": 25,
            },
        },
    )
    assert first_save["revision"] == initial["revision"] + 1
    print(f"PASS save coverage: revision {first_save['revision']}, 25 km radius")

    reloaded = request_json(f"/vendors/{DEMO_VENDOR_ID}/service-area", token=token)
    assert reloaded["coverage"] == first_save["coverage"]
    print(f"PASS reload coverage: revision {reloaded['revision']}")

    edited = request_json(
        f"/vendors/{DEMO_VENDOR_ID}/service-area",
        method="PATCH",
        token=token,
        body={
            "expected_revision": reloaded["revision"],
            "coverage": {
                **reloaded["coverage"],
                "radius_km": 40,
            },
        },
    )
    assert edited["coverage"]["radius_km"] == 40
    print(f"PASS edit coverage: revision {edited['revision']}, 40 km radius")

    principal = Principal(user_id=user["id"], organization_id=user["organization_id"])
    with SessionLocal() as db:
        inside = check_event_eligibility(
            db,
            DEMO_VENDOR_ID,
            EligibilityRequest(latitude=40.7128, longitude=-74.0060),
            principal,
        )
        outside = check_event_eligibility(
            db,
            DEMO_VENDOR_ID,
            EligibilityRequest(latitude=34.0522, longitude=-118.2437),
            principal,
        )
    assert inside.eligible and inside.reason == "within_radius"
    assert not outside.eligible and outside.reason == "outside_radius"
    print(f"PASS internal geographic matching: NYC={inside.reason}, LA={outside.reason}")
    print("Demo journey complete. The walkthrough vendor now has a saved 40 km NYC radius.")


if __name__ == "__main__":
    main()
