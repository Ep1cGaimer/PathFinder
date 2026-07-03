"""Add road snapping metadata and the route-derived segment catalog.

Revision ID: 20260703_02
Revises: 20260702_01
"""

import sqlalchemy as sa
from alembic import op

revision = "20260703_02"
down_revision = "20260702_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("road_reports", sa.Column("snapped_latitude", sa.Float(), nullable=True))
    op.add_column("road_reports", sa.Column("snapped_longitude", sa.Float(), nullable=True))
    op.add_column("road_reports", sa.Column("road_place_id", sa.String(255), nullable=True))
    op.add_column(
        "road_reports",
        sa.Column("snap_status", sa.String(24), nullable=False, server_default="pending"),
    )
    op.execute(
        """
        ALTER TABLE road_reports ADD COLUMN effective_geom geography(Point, 4326)
        GENERATED ALWAYS AS (
          ST_SetSRID(ST_MakePoint(
            COALESCE(snapped_longitude, longitude),
            COALESCE(snapped_latitude, latitude)
          ), 4326)::geography
        ) STORED
        """
    )
    op.execute("CREATE INDEX ix_road_reports_effective_geom ON road_reports USING GIST (effective_geom)")
    op.execute(
        """
        CREATE TABLE road_segments (
          segment_hash varchar(64) PRIMARY KEY,
          encoded_polyline text NOT NULL,
          geom geography(LineString, 4326) NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          last_seen_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_road_segments_geom ON road_segments USING GIST (geom)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS road_segments")
    op.execute("DROP INDEX IF EXISTS ix_road_reports_effective_geom")
    op.execute("ALTER TABLE road_reports DROP COLUMN IF EXISTS effective_geom")
    op.drop_column("road_reports", "snap_status")
    op.drop_column("road_reports", "road_place_id")
    op.drop_column("road_reports", "snapped_longitude")
    op.drop_column("road_reports", "snapped_latitude")
