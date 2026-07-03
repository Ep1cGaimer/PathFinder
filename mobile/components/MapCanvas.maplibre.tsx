import { useEffect, useMemo, useRef } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Camera, type CameraRef, GeoJSONSource, Layer, Map, Marker } from '@maplibre/maplibre-react-native';
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

function feature(segment: RoadQualitySegment, routeId?: string, width?: number): LineFeature {
  return {
    type: 'Feature', properties: { color: qualityColor(segment.road_quality), routeId, width },
    geometry: { type: 'LineString', coordinates: polyline.decode(segment.encoded_polyline).map(([lat, lng]) => [lng, lat]) },
  };
}

export function MapCanvas(props: Props) {
  const camera = useRef<CameraRef>(null);
  const nearby = useMemo<GeoJSON.FeatureCollection<GeoJSON.LineString>>(() => ({
    type: 'FeatureCollection', features: props.nearbySegments.map((segment) => feature(segment)),
  }), [props.nearbySegments]);
  const routes = useMemo<GeoJSON.FeatureCollection<GeoJSON.LineString>>(() => ({
    type: 'FeatureCollection',
    features: props.routes.flatMap((route) => {
      const active = route.id === props.selected?.id;
      const segments = route.quality_segments?.length
        ? route.quality_segments
        : [{ encoded_polyline: route.encoded_polyline, road_quality: null } as RoadQualitySegment];
      return segments.map((segment) => feature(segment, route.id, active ? 7 : 4));
    }),
  }), [props.routes, props.selected]);
  const reportPoints = useMemo<GeoJSON.FeatureCollection<GeoJSON.Point>>(() => ({
    type: 'FeatureCollection',
    features: props.showReports ? props.reports.map((report) => {
      const point = report.snapped_location ?? report;
      return {
        type: 'Feature', properties: { color: qualityColor(report.assessment?.road_quality) },
        geometry: { type: 'Point', coordinates: [point.longitude, point.latitude] },
      };
    }) : [],
  }), [props.reports, props.showReports]);

  useEffect(() => {
    if (!props.selected) return;
    const points = polyline.decode(props.selected.encoded_polyline);
    const lngs = points.map(([, lng]) => lng);
    const lats = points.map(([lat]) => lat);
    camera.current?.fitBounds(
      [Math.min(...lngs), Math.min(...lats), Math.max(...lngs), Math.max(...lats)],
      { padding: { top: 110, right: 45, bottom: 300, left: 45 }, duration: 500 },
    );
  }, [props.selected]);

  return <Map
    style={StyleSheet.absoluteFill}
    mapStyle={process.env.EXPO_PUBLIC_MAP_STYLE_URL ?? 'https://tiles.openfreemap.org/styles/liberty'}
    compass={false}
    onRegionDidChange={(event) => {
      const [west, south, east, north] = event.nativeEvent.bounds;
      props.onViewportChange({ min_lat: south, min_lng: west, max_lat: north, max_lng: east, zoom: Math.round(event.nativeEvent.zoom) });
    }}
  >
    <Camera ref={camera} initialViewState={{ center: [77.6206, 12.9763], zoom: 12.7 }} />
    <GeoJSONSource id='quality-roads' data={nearby}>
      <Layer id='quality-roads-line' type='line' paint={{ 'line-color': ['get', 'color'], 'line-width': 4, 'line-opacity': 0.78 }} />
    </GeoJSONSource>
    <GeoJSONSource id='pathfinder-routes' data={routes} onPress={(event) => {
      const routeId = event.nativeEvent.features?.[0]?.properties?.routeId;
      const route = props.routes.find((item) => item.id === routeId);
      if (route) props.onSelectRoute(route);
    }}>
      <Layer id='route-casing' type='line' paint={{ 'line-color': '#FFFFFF', 'line-width': ['+', ['get', 'width'], 4], 'line-opacity': 0.9 }} />
      <Layer id='route-quality' type='line' paint={{ 'line-color': ['get', 'color'], 'line-width': ['get', 'width'], 'line-opacity': 0.96 }} />
    </GeoJSONSource>
    <GeoJSONSource id='report-points' data={reportPoints}>
      <Layer id='report-circles' type='circle' paint={{ 'circle-color': ['get', 'color'], 'circle-radius': 6, 'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 3 }} />
    </GeoJSONSource>
    <Marker id='origin' lngLat={[props.origin.longitude, props.origin.latitude]}>
      <View style={[styles.endpoint, { backgroundColor: colors.brand }]}><Text style={styles.text}>A</Text></View>
    </Marker>
    <Marker id='destination' lngLat={[props.destination.longitude, props.destination.latitude]}>
      <View style={[styles.endpoint, { backgroundColor: colors.ink }]}><Text style={styles.text}>B</Text></View>
    </Marker>
  </Map>;
}

const styles = StyleSheet.create({
  endpoint: { width: 30, height: 30, borderRadius: 15, borderWidth: 3, borderColor: 'white', alignItems: 'center', justifyContent: 'center', elevation: 6 },
  text: { color: 'white', fontWeight: '800', fontSize: 11 },
});
