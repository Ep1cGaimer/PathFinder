local roads = osm2pgsql.define_way_table('osm_roads_raw', {
    { column = 'osm_way_id', type = 'int8' },
    { column = 'name', type = 'text' },
    { column = 'highway', type = 'text' },
    { column = 'surface', type = 'text' },
    { column = 'geom', type = 'linestring', projection = 4326 },
})

function osm2pgsql.process_way(object)
    if not object.tags.highway then
        return
    end
    roads:insert({
        osm_way_id = object.id,
        name = object.tags.name,
        highway = object.tags.highway,
        surface = object.tags.surface,
        geom = object:as_linestring(),
    })
end
