import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class ReportStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    reputation: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reports: Mapped[list["RoadReport"]] = relationship(back_populates="user")


class RoadReport(Base):
    __tablename__ = "road_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    snapped_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapped_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    road_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    road_segment_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    snap_distance_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    snap_status: Mapped[str] = mapped_column(String(24), default="pending")
    description: Mapped[str] = mapped_column(Text, default="")
    image_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(
            ReportStatus,
            name="report_status",
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        default=ReportStatus.PROCESSING,
    )
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User | None] = relationship(back_populates="reports")
    assessment: Mapped["RoadAssessment | None"] = relationship(
        back_populates="report", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_road_reports_status_created", "status", "created_at"),)


class RoadAssessment(Base):
    __tablename__ = "road_assessments"

    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("road_reports.id", ondelete="CASCADE"), primary_key=True
    )
    model_version: Mapped[str] = mapped_column(String(100))
    detections: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    surface_damage: Mapped[float] = mapped_column(Float)
    traffic_safety_risk: Mapped[float] = mapped_column(Float)
    ride_discomfort: Mapped[float] = mapped_column(Float)
    waterlogging: Mapped[float] = mapped_column(Float)
    urgency_for_repair: Mapped[float] = mapped_column(Float)
    road_quality: Mapped[float] = mapped_column(Float, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    report: Mapped[RoadReport] = relationship(back_populates="assessment")
