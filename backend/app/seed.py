from app.db.session import SessionLocal
from app.models import Vendor
from app.models import User
from app.core.security import hash_password


def seed() -> None:
    with SessionLocal() as db:
        if db.get(Vendor, "vendor-demo") is None:
            db.add(Vendor(id="vendor-demo", organization_id="org-demo", display_name="Northstar Events"))
        if db.get(Vendor, "vendor-other") is None:
            db.add(Vendor(id="vendor-other", organization_id="org-other", display_name="Private Example Vendor"))
        if db.query(User).filter_by(email="vendor-demo@nova.test").first() is None:
            db.add(User(id="user-demo", email="vendor-demo@nova.test", password_hash=hash_password("NOVA-demo-2026!"), organization_id="org-demo"))
        if db.query(User).filter_by(email="other-demo@nova.test").first() is None:
            db.add(User(id="user-other", email="other-demo@nova.test", password_hash=hash_password("NOVA-demo-2026!"), organization_id="org-other"))
        db.commit()


if __name__ == "__main__":
    seed()
