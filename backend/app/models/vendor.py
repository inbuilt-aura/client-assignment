from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
