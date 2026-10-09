from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from threading import Lock
from time import monotonic, sleep
import json
from difflib import get_close_matches
from uuid import uuid4

from app.api.dependencies import Principal, get_principal, require_vendor
from app.core.areas import AREA_BOUNDARY_RULE, AREA_DATASET_VERSION, AREAS
from app.core.config import settings
from app.db.session import get_db
from app.models import ServiceArea, Vendor
from app.models import User
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.service_area import EligibilityRequest, EligibilityResponse, LocationResult, ServiceAreaCatalog, ServiceAreaPatch
from app.schemas.auth import LoginRequest, LoginResponse, SignupRequest, UserResponse
from app.services.coverage import evaluate_coverage, validate_area_ids

router = APIRouter()
_location_cache: dict[str, tuple[float, list[LocationResult]]] = {}
_geocoder_lock = Lock()
_last_geocoder_request = 0.0
_LOCATION_WORDS = {
    "jersey", "francisco", "angeles", "oakland", "york", "newark", "boston", "chicago",
    "seattle", "austin", "dallas", "denver", "miami", "atlanta", "portland", "phoenix",
    "san", "jose", "los", "new", "city", "united", "states", "california", "texas",
    "florida", "oregon", "washington", "massachusetts", "pennsylvania", "connecticut",
    "delaware", "maryland", "virginia", "carolina", "georgia", "colorado", "nevada",
    "arizona", "ohio", "illinois", "michigan", "minnesota", "wisconsin", "hawaii",
    "alaska", "tennessee", "kentucky", "indiana", "missouri", "louisiana", "maine",
    "montana", "wyoming", "idaho", "utah", "iowa", "kansas", "arkansas", "alabama",
    "mississippi", "vermont", "hampshire", "island", "mexico", "jersey",
}


@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.casefold()).one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"code": "invalid_credentials", "message": "Email or password is incorrect."})
    token, expires_in = create_access_token(user.id, user.organization_id)
    return LoginResponse(access_token=token, expires_in=expires_in)


@router.post("/auth/signup", response_model=LoginResponse, status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    email = body.email.casefold()
    if db.query(User).filter(User.email == email).one_or_none() is not None:
        raise HTTPException(status_code=409, detail={"code": "email_already_registered", "message": "An account with this email already exists."})
    organization_id = f"org-{uuid4().hex}"
    vendor_id = f"vendor-{uuid4().hex}"
    user = User(id=f"user-{uuid4().hex}", email=email, password_hash=hash_password(body.password), organization_id=organization_id)
    db.add_all([user, Vendor(id=vendor_id, organization_id=organization_id, display_name=body.business_name)])
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": "email_already_registered", "message": "An account with this email already exists."}) from error
    token, expires_in = create_access_token(user.id, organization_id)
    return LoginResponse(access_token=token, expires_in=expires_in)


@router.get("/auth/me", response_model=UserResponse)
def current_user(principal: Principal = Depends(get_principal), db: Session = Depends(get_db)):
    user = db.get(User, principal.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail={"code": "authentication_required"})
    vendor = db.query(Vendor).filter(Vendor.organization_id == user.organization_id).order_by(Vendor.id).first()
    return UserResponse(id=user.id, email=user.email, organization_id=user.organization_id, vendor_id=vendor.id if vendor else None)


@router.get("/service-areas", response_model=ServiceAreaCatalog)
def service_area_catalog():
    """Return the canonical area choices used by validation and eligibility."""
    return ServiceAreaCatalog(
        dataset_version=AREA_DATASET_VERSION,
        boundary_rule=AREA_BOUNDARY_RULE,
        areas=[{"id": area_id, "label": area["label"], "detail": area["detail"]} for area_id, area in AREAS.items()],
    )


@router.get("/locations/search", response_model=list[LocationResult])
def search_locations(q: str = Query(min_length=2, max_length=100)):
    """Explicit, server-proxied Nominatim search; deliberately not autocomplete."""
    query = " ".join(q.split())
    cached = _location_cache.get(query.casefold())
    if cached and cached[0] > monotonic():
        return cached[1]

    if settings.geocoding_provider != "nominatim":
        raise HTTPException(status_code=503, detail={"code": "geocoding_provider_unavailable"})

    def nominatim_search(search_query: str):
        global _last_geocoder_request
        # Serialize calls and keep this application's public Nominatim traffic <= 1 req/sec.
        with _geocoder_lock:
            wait = 1.0 - (monotonic() - _last_geocoder_request)
            if wait > 0:
                sleep(wait)
            _last_geocoder_request = monotonic()
            url = f"{settings.nominatim_base_url.rstrip('/')}/search?{urlencode({'q': search_query, 'format': 'jsonv2', 'limit': 6, 'addressdetails': 1})}"
            request = Request(url, headers={"User-Agent": settings.geocoding_user_agent, "Accept": "application/json"})
            with urlopen(request, timeout=8) as response:
                return json.load(response)

    try:
        payload = nominatim_search(query)
        if not payload:
            words = query.split()
            corrected_words = []
            changed = False
            for word in words:
                candidates = get_close_matches(word.casefold(), _LOCATION_WORDS, n=1, cutoff=0.70) if len(word) >= 4 else []
                corrected = candidates[0] if candidates else word
                changed = changed or corrected.casefold() != word.casefold()
                corrected_words.append(corrected)
            if changed:
                payload = nominatim_search(" ".join(corrected_words))
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
