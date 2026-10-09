import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User, Vendor


@pytest.fixture
def service_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestingSession() as session:
        session.add_all([
            User(id="user-a", email="a@example.test", password_hash=hash_password("password-a"), organization_id="org-a"),
            User(id="user-b", email="b@example.test", password_hash=hash_password("password-b"), organization_id="org-b"),
            Vendor(id="vendor-a", organization_id="org-a", display_name="Vendor A"),
            Vendor(id="vendor-b", organization_id="org-b", display_name="Vendor B"),
        ])
        session.commit()

    tokens = {
        "owner": create_access_token("user-a", "org-a")[0],
        "other": create_access_token("user-b", "org-b")[0],
    }
    try:
        with TestClient(app) as client:
            yield client, tokens
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()
