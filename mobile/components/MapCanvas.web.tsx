import { useEffect, useRef } from "react";
import { importLibrary, setOptions } from "@googlemaps/js-api-loader";
import polyline from "@mapbox/polyline";
import type { RoadReport, RouteOption } from "../src/types";
import { colors } from "../src/theme";

export function MapCanvas({ routes, selected, reports }: { routes: RouteOption[]; selected?: RouteOption; reports: RoadReport[] }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let active = true;
    async function draw() {
      if (!host.current) return;
      const key = process.env.EXPO_PUBLIC_GOOGLE_MAPS_WEB_KEY;
      if (!key) {
        host.current.style.background = "radial-gradient(circle at 65% 32%, #d6e7df 0 7%, transparent 8%), linear-gradient(135deg,#e8efeb,#cadbd4)";
        return;
      }
      setOptions({ key, v: "weekly" });
      const { Map, Polyline } = await importLibrary("maps");
      const { LatLngBounds } = await importLibrary("core");
      const { AdvancedMarkerElement } = await importLibrary("marker");
      if (!active || !host.current) return;
      const map = new Map(host.current, { center: { lat: 12.9763, lng: 77.6206 }, zoom: 13, mapId: "DEMO_MAP_ID", disableDefaultUI: true, zoomControl: true });
      const bounds = new LatLngBounds();
      routes.forEach((route) => {
        const path = polyline.decode(route.encoded_polyline).map(([lat, lng]) => ({ lat, lng }));
        path.forEach((point) => bounds.extend(point));
        new Polyline({ map, path, strokeColor: route.id === selected?.id ? colors.brand : colors.routeAlt, strokeWeight: route.id === selected?.id ? 7 : 4, strokeOpacity: route.id === selected?.id ? 1 : 0.55 });
      });
      reports.forEach((report) => new AdvancedMarkerElement({ map, position: { lat: report.latitude, lng: report.longitude }, title: `Road quality ${Math.round(report.assessment?.road_quality ?? 50)}` }));
      if (!bounds.isEmpty()) map.fitBounds(bounds, 64);
    }
    draw().catch(console.error);
    return () => { active = false; };
  }, [routes, selected, reports]);
  return <div ref={host} style={{ width: "100%", height: "100%", backgroundColor: "#d9e5df" }} />;
}

