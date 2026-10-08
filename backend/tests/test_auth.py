import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, UserResponse


def test_demo_reserved_domain_is_accepted_for_login_and_current_user():
    login = LoginRequest(email="vendor-demo@nova.test", password="NOVA-demo-2026!")
    user = UserResponse(id="user-demo", email=login.email, organization_id="org-demo")

    assert login.email == "vendor-demo@nova.test"
    assert user.email == "vendor-demo@nova.test"


def test_malformed_email_is_rejected():
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="password")
