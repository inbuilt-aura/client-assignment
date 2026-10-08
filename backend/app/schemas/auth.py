from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, Field


def _validate_email(value: str) -> str:
    """Validate addresses while allowing reserved domains used by local demos."""
    try:
        return validate_email(value, check_deliverability=False, test_environment=True).normalized
    except EmailNotValidError as error:
        raise ValueError(str(error)) from error


EmailAddress = Annotated[str, AfterValidator(_validate_email)]


class LoginRequest(BaseModel):
    email: EmailAddress
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: EmailAddress
    organization_id: str
