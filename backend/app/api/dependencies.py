from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User, Vendor

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: str
    organization_id: str


def get_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=401, detail={"code": "authentication_required"})
    claims = decode_access_token(credentials.credentials)
    user = db.get(User, claims["sub"])
    if user is None or user.organization_id != claims["org"]:
        raise HTTPException(status_code=401, detail={"code": "invalid_or_expired_token"})
    return Principal(user_id=user.id, organization_id=user.organization_id)


def require_vendor(db: Session, vendor_id: str, principal: Principal) -> Vendor:
    vendor = db.get(Vendor, vendor_id)
    if vendor is None or vendor.organization_id != principal.organization_id:
        # Avoid leaking whether a vendor belongs to another organization.
        raise HTTPException(status_code=404, detail={"code": "vendor_not_found"})
    return vendor
