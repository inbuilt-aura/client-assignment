"""Add local demo authentication users."""
from alembic import op
import sqlalchemy as sa

revision = "0002_demo_auth_users"
down_revision = "0001_vendor_service_area"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_organization_id", "users", ["organization_id"])


def downgrade():
    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
