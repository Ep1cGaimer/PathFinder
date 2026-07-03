'''Add canonical OpenStreetMap road segments.

Revision ID: 20260703_03
Revises: 20260703_02
'''

import sqlalchemy as sa
from alembic import op

revision = '20260703_03'
down_revision = '20260703_02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('''
        CREATE TABLE osm_road_segments (
          segment_id varchar(128) PRIMARY KEY,
          osm_way_id bigint NOT NULL,
          segment_index integer NOT NULL,
          name text,
          highway varchar(64),
          surface varchar(64),
          geom geometry(LineString, 4326) NOT NULL,
          source_updated_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE (osm_way_id, segment_index)
        )
    ''')
    op.execute('CREATE INDEX ix_osm_road_segments_geom ON osm_road_segments USING GIST (geom)')
    op.add_column('road_reports', sa.Column('road_segment_id', sa.String(128), nullable=True))
    op.add_column('road_reports', sa.Column('snap_distance_meters', sa.Float(), nullable=True))
    op.create_index('ix_road_reports_road_segment_id', 'road_reports', ['road_segment_id'])


def downgrade() -> None:
    op.drop_index('ix_road_reports_road_segment_id', table_name='road_reports')
    op.drop_column('road_reports', 'snap_distance_meters')
    op.drop_column('road_reports', 'road_segment_id')
    op.execute('DROP TABLE IF EXISTS osm_road_segments')
