# Bengaluru OSM data build

The routing graph, search index, road snapping table, and optional basemap must be built from the same OpenStreetMap extract.

1. Download Geofabrik Southern Zone data.
2. Extract `77.35,12.75,77.85,13.20` with Osmium.
3. Import roads with `osm2pgsql --output flex --style roads.lua`.
4. Run `rebuild_segments.sql` to create approximately 50 metre canonical road segments.
5. Point openrouteservice at the extracted PBF.
6. Import the same extract into Nominatim, then import Photon from that database.

Do not commit PBF files, routing graphs, Photon indexes, or PMTiles archives. They are reproducible deployment data and retain OpenStreetMap ODbL attribution requirements.
