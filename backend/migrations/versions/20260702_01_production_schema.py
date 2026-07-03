"""Create the production PostGIS schema."""
from alembic import op

revision = "20260702_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE TYPE report_status AS ENUM ('processing', 'ready', 'failed')")
    op.execute("""
      CREATE TABLE users (
        id VARCHAR(128) PRIMARY KEY, name VARCHAR(120) NOT NULL,
        reputation INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      )
    """)
    op.execute("""
      CREATE TABLE road_reports (
        id UUID PRIMARY KEY, user_id VARCHAR(128) REFERENCES users(id),
        latitude DOUBLE PRECISION NOT NULL, longitude DOUBLE PRECISION NOT NULL,
        description TEXT NOT NULL DEFAULT '', image_key VARCHAR(512),
        status report_status NOT NULL DEFAULT 'processing', is_demo BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        geom geography(Point,4326) GENERATED ALWAYS AS (
          ST_SetSRID(ST_MakePoint(longitude, latitude),4326)::geography
        ) STORED
      )
    """)
    op.execute("CREATE INDEX ix_road_reports_geom ON road_reports USING GIST (geom)")
    op.execute("CREATE INDEX ix_road_reports_status_created ON road_reports (status, created_at)")
    op.execute("""
      CREATE TABLE road_assessments (
        report_id UUID PRIMARY KEY REFERENCES road_reports(id) ON DELETE CASCADE,
        model_version VARCHAR(100) NOT NULL, detections JSONB NOT NULL DEFAULT '[]',
        surface_damage DOUBLE PRECISION NOT NULL, traffic_safety_risk DOUBLE PRECISION NOT NULL,
        ride_discomfort DOUBLE PRECISION NOT NULL, waterlogging DOUBLE PRECISION NOT NULL,
        urgency_for_repair DOUBLE PRECISION NOT NULL, road_quality DOUBLE PRECISION NOT NULL,
        confidence DOUBLE PRECISION NOT NULL
      )
    """)
    op.execute("CREATE INDEX ix_road_assessments_quality ON road_assessments (road_quality)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS road_assessments")
    op.execute("DROP TABLE IF EXISTS road_reports")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TYPE IF EXISTS report_status")
