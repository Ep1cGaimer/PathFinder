import { useEffect, useRef, useState } from 'react';
import maplibregl, { type GeoJSONSource, type Map as MapLibreMap, type Marker } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import polyline from '@mapbox/polyline';
import type { Coordinate, MapBounds, RoadQualitySegment, RoadReport, RouteOption } from '../src/types';
import { colors, qualityColor } from '../src/theme';

type Props = {
  routes: RouteOption[];
  selected?: RouteOption;
  nearbySegments: RoadQualitySegment[];
  reports: RoadReport[];
  origin: Coordinate;
  destination: Coordinate;
  showReports: boolean;
  onSelectRoute: (route: RouteOption) => void;
  onViewportChange: (bounds: MapBounds) => void;
};

type LineFeature = GeoJSON.Feature<GeoJSON.LineString, { color: string; routeId?: string; width?: number }>;

function lineFeature(segment: RoadQualitySegment, routeId?: string, width?: number): LineFeature {
  return {
    type: 'Feature',
    properties: { color: qualityColor(segment.road_quality), routeId, width },
    geometry: {
      type: 'LineString',
      coordinates: polyline.decode(segment.encoded_polyline).map(([lat, lng]) => [lng, lat]),
    },
  };
}

function markerElement(label: string, color: string, small = false) {
  const element = document.createElement('div');
  element.textContent = small ? '' : label;
  element.style.cssText = small
    ? `width:12px;height:12px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 2px 7px #0005`
    : `width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:${color};color:white;border:3px solid white;box-shadow:0 2px 8px #0006;font:800 12px system-ui`;
  return element;
}

export function MapCanvas(props: Props) {
  const { onViewportChange } = props;
  const host = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markers = useRef<Marker[]>([]);
  const onViewportChangeRef = useRef(onViewportChange);
  const routesRef = useRef(props.routes);
  const onSelectRouteRef = useRef(props.onSelectRoute);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    onViewportChangeRef.current = onViewportChange;
    routesRef.current = props.routes;
    onSelectRouteRef.current = props.onSelectRoute;
  }, [onViewportChange, props.routes, props.onSelectRoute]);

  useEffect(() => {
    if (!host.current || mapRef.current) return;
    setReady(false);
    const map = new maplibregl.Map({
      container: host.current,
      style: process.env.EXPO_PUBLIC_MAP_STYLE_URL ?? 'https://tiles.openfreemap.org/styles/liberty',
      center: [77.6206, 12.9763],
      zoom: 12.7,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.on('load', () => setReady(true));
    map.on('moveend', () => {
      const bounds = map.getBounds();
      onViewportChangeRef.current({
        min_lat: bounds.getSouth(), min_lng: bounds.getWest(),
        max_lat: bounds.getNorth(), max_lng: bounds.getEast(), zoom: Math.round(map.getZoom()),
      });
    });
    mapRef.current = map;
    return () => {
      setReady(false);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const nearby: GeoJSON.FeatureCollection<GeoJSON.LineString> = {
      type: 'FeatureCollection', features: props.nearbySegments.map((segment) => lineFeature(segment)),
    };
    const routeFeatures: LineFeature[] = [];
    props.routes.forEach((route) => {
      const active = route.id === props.selected?.id;
      const segments = route.quality_segments?.length
        ? route.quality_segments
        : [{ encoded_polyline: route.encoded_polyline, road_quality: null } as RoadQualitySegment];
      segments.forEach((segment) => routeFeatures.push(lineFeature(segment, route.id, active ? 7 : 4)));
    });
    const routeData: GeoJSON.FeatureCollection<GeoJSON.LineString> = { type: 'FeatureCollection', features: routeFeatures };

    if (!map.getSource('quality-roads')) {
      map.addSource('quality-roads', { type: 'geojson', data: nearby });
      map.addLayer({ id: 'quality-roads', type: 'line', source: 'quality-roads', paint: {
        'line-color': ['get', 'color'], 'line-width': 4, 'line-opacity': 0.78,
      }});
    } else (map.getSource('quality-roads') as GeoJSONSource).setData(nearby);

    if (!map.getSource('pathfinder-routes')) {
      map.addSource('pathfinder-routes', { type: 'geojson', data: routeData });
      map.addLayer({ id: 'route-casing', type: 'line', source: 'pathfinder-routes', paint: {
        'line-color': '#FFFFFF', 'line-width': ['+', ['get', 'width'], 4], 'line-opacity': 0.9,
      }});
      map.addLayer({ id: 'route-quality', type: 'line', source: 'pathfinder-routes', paint: {
        'line-color': ['get', 'color'], 'line-width': ['get', 'width'], 'line-opacity': 0.95,
      }});
      map.on('click', 'route-quality', (event) => {
        const routeId = event.features?.[0]?.properties?.routeId;
        const route = routesRef.current.find((item) => item.id === routeId);
        if (route) onSelectRouteRef.current(route);
      });
      map.on('mouseenter', 'route-quality', () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'route-quality', () => { map.getCanvas().style.cursor = ''; });
    } else (map.getSource('pathfinder-routes') as GeoJSONSource).setData(routeData);

    markers.current.forEach((marker) => marker.remove());
    markers.current = [];
    if (props.showReports) props.reports.forEach((report) => {
      const point = report.snapped_location ?? report;
      markers.current.push(new maplibregl.Marker({ element: markerElement('', qualityColor(report.assessment?.road_quality), true) })
        .setLngLat([point.longitude, point.latitude]).addTo(map));
    });
    markers.current.push(
      new maplibregl.Marker({ element: markerElement('A', colors.brand) }).setLngLat([props.origin.longitude, props.origin.latitude]).addTo(map),
      new maplibregl.Marker({ element: markerElement('B', colors.ink) }).setLngLat([props.destination.longitude, props.destination.latitude]).addTo(map),
    );
  }, [props, ready]);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map || !props.selected) return;
    const bounds = new maplibregl.LngLatBounds();
    polyline.decode(props.selected.encoded_polyline).forEach(([lat, lng]) => bounds.extend([lng, lat]));
    map.fitBounds(bounds, { padding: { top: 80, right: 70, bottom: 100, left: 430 }, maxZoom: 16 });
  }, [props.selected, ready]);

  return <div ref={host} style={{ width: '100%', height: '100%', background: '#E9EEF1' }} />;
}
