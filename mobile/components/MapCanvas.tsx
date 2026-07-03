import { useEffect, useRef } from "react";
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from "react-native-maps";
import polyline from "@mapbox/polyline";
import type { RoadReport, RouteOption } from "../src/types";
import { colors } from "../src/theme";

export function MapCanvas({ routes, selected, reports }: { routes: RouteOption[]; selected?: RouteOption; reports: RoadReport[] }) {
  const map = useRef<MapView>(null);
  useEffect(() => {
    if (!selected) return;
    const points = polyline.decode(selected.encoded_polyline).map(([latitude, longitude]) => ({ latitude, longitude }));
    map.current?.fitToCoordinates(points, { edgePadding: { top: 180, left: 50, right: 50, bottom: 330 }, animated: true });
  }, [selected]);
  return (
    <MapView ref={map} provider={PROVIDER_GOOGLE} style={{ flex: 1 }} showsUserLocation
      initialRegion={{ latitude: 12.9763, longitude: 77.6206, latitudeDelta: 0.11, longitudeDelta: 0.11 }}>
      {routes.map((route) => <Polyline key={route.id}
        coordinates={polyline.decode(route.encoded_polyline).map(([latitude, longitude]) => ({ latitude, longitude }))}
        strokeColor={route.id === selected?.id ? colors.brand : colors.routeAlt}
        strokeWidth={route.id === selected?.id ? 7 : 4} zIndex={route.id === selected?.id ? 2 : 1} />)}
      {reports.map((report) => <Marker key={report.id} coordinate={{ latitude: report.latitude, longitude: report.longitude }}
        title={report.is_demo ? "Demo observation" : "Road report"}
        description={`Road quality ${Math.round(report.assessment?.road_quality ?? 50)}/100`}
        pinColor={(report.assessment?.road_quality ?? 50) >= 70 ? colors.good : (report.assessment?.road_quality ?? 50) >= 45 ? colors.warning : colors.danger} />)}
    </MapView>
  );
}

