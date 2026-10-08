from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ServiceArea(Base):
    __tablename__ = "vendor_service_areas"

    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id", ondelete="CASCADE"), primary_key=True)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    coverage: Mapped[dict] = mapped_column(JSON, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
