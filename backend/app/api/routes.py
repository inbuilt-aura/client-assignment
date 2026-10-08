from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from threading import Lock
from time import monotonic, sleep
import json

from app.api.dependencies import Principal, get_principal, require_vendor
from app.core.areas import AREAS
from app.core.config import settings
from app.db.session import get_db
from app.models import ServiceArea, Vendor
from app.models import User
from app.core.security import create_access_token, verify_password
from app.schemas.service_area import EligibilityRequest, EligibilityResponse, LocationResult, ServiceAreaPatch
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse
from app.services.coverage import evaluate_coverage, validate_area_ids

router = APIRouter()
_location_cache: dict[str, tuple[float, list[LocationResult]]] = {}
_geocoder_lock = Lock()
_last_geocoder_request = 0.0


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.casefold()).one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"code": "invalid_credentials", "message": "Email or password is incorrect."})
    token, expires_in = create_access_token(user.id, user.organization_id)
    return LoginResponse(access_token=token, expires_in=expires_in)


@router.get("/auth/me", response_model=UserResponse)
def current_user(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    user = db.get(User, principal.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail={"code": "authentication_required"})
    return UserResponse(id=user.id, email=user.email, organization_id=user.organization_id)


@router.get("/locations/search", response_model=list[LocationResult])
def search_locations(q: str = Query(min_length=2, max_length=100)):
    """Explicit, server-proxied Nominatim search; deliberately not autocomplete."""
    query = " ".join(q.split())
    cached = _location_cache.get(query.casefold())
    if cached and cached[0] > monotonic():
        return cached[1]

    if settings.geocoding_provider != "nominatim":
        raise HTTPException(status_code=503, detail={"code": "geocoding_provider_unavailable"})

    global _last_geocoder_request
    try:
        # Serialize calls and keep this application's public Nominatim traffic <= 1 req/sec.
        with _geocoder_lock:
            wait = 1.0 - (monotonic() - _last_geocoder_request)
            if wait > 0:
                sleep(wait)
            _last_geocoder_request = monotonic()
            url = f"{settings.nominatim_base_url.rstrip('/')}/search?{urlencode({'q': query, 'format': 'jsonv2', 'limit': 6, 'addressdetails': 1})}"
            request = Request(url, headers={"User-Agent": settings.geocoding_user_agent, "Accept": "application/json"})
            with urlopen(request, timeout=8) as response:
                payload = json.load(response)
    except (URLError, TimeoutError, ValueError) as error:
        raise HTTPException(status_code=502, detail={"code": "location_search_failed"}) from error

    results = [
        LocationResult(
            id=f"osm:{place['osm_type']}:{place['osm_id']}",
            label=place["display_name"],
            latitude=float(place["lat"]),
            longitude=float(place["lon"]),
        )
        for place in payload
        if place.get("lat") and place.get("lon") and place.get("display_name")
    ]
    _location_cache[query.casefold()] = (monotonic() + 3600, results)
    return results


@router.get("/vendors/{vendor_id}/service-area")
def get_service_area(vendor_id: str, db: Session = Depends(get_db), principal: Principal = Depends(get_principal)):
    require_vendor(db, vendor_id, principal)
    saved = db.get(ServiceArea, vendor_id)
    return {
        "vendor_id": vendor_id,
        "revision": saved.revision if saved else 0,
        "coverage": saved.coverage if saved else None,
        "updated_at": saved.updated_at if saved else None,
    }


@router.patch("/vendors/{vendor_id}/service-area")
def patch_service_area(vendor_id: str, body: ServiceAreaPatch, db: Session = Depends(get_db), principal: Principal = Depends(get_principal)):
    require_vendor(db, vendor_id, principal)
    payload = body.coverage.model_dump(mode="json")
    if payload["mode"] == "AREAS":
        try:
            validate_area_ids(payload["area_ids"])
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"code": "invalid_area_ids", "message": str(error)}) from error

    # Lock the vendor row before checking revision to serialize concurrent writers.
    db.query(Vendor).filter_by(id=vendor_id).with_for_update().one()
    saved = db.get(ServiceArea, vendor_id)
    current_revision = saved.revision if saved else 0
    if body.expected_revision != current_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": "stale_service_area", "message": "Coverage changed since it was loaded.", "current_revision": current_revision},
        )
    if saved is None:
        saved = ServiceArea(vendor_id=vendor_id, mode=payload["mode"], coverage=payload, revision=1)
        db.add(saved)
    else:
        saved.mode = payload["mode"]
        saved.coverage = payload
        saved.revision += 1
    db.commit()
    db.refresh(saved)
    return {"vendor_id": vendor_id, "revision": saved.revision, "coverage": saved.coverage, "updated_at": saved.updated_at}


def check_event_eligibility(db: Session, vendor_id: str, event: EligibilityRequest, principal: Principal) -> EligibilityResponse:
    """Internal service entry point; intentionally not exposed as a public endpoint."""
    require_vendor(db, vendor_id, principal)
    saved = db.get(ServiceArea, vendor_id)
    if saved is None:
        return EligibilityResponse(eligible=False, reason="coverage_not_configured")
    return evaluate_coverage(saved.coverage, event.latitude, event.longitude, event.area_id)
