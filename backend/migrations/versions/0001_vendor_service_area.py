"""Create vendors and vendor service area tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_vendor_service_area"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
    )
    op.create_index("ix_vendors_organization_id", "vendors", ["organization_id"])
    op.create_table(
        "vendor_service_areas",
        sa.Column("vendor_id", sa.String(length=64), sa.ForeignKey("vendors.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("coverage", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("vendor_service_areas")
    op.drop_index("ix_vendors_organization_id", table_name="vendors")
    op.drop_table("vendors")
