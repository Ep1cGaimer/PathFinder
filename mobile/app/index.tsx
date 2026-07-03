import { useEffect, useState } from "react";
import { ActivityIndicator, Alert, FlatList, Pressable, SafeAreaView, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import * as Location from "expo-location";
import { GlassSurface } from "../components/GlassSurface";
import { MapCanvas } from "../components/MapCanvas";
import { RouteCard } from "../components/RouteCard";
import { geocode, nearbyReports, recommend } from "../src/api";
import { colors, shadow } from "../src/theme";
import type { Coordinate, RoadReport, RouteOption } from "../src/types";

const CUBBON: Coordinate = { label: "Cubbon Park", latitude: 12.9763, longitude: 77.5929 };
const INDIRANAGAR: Coordinate = { label: "Indiranagar", latitude: 12.9784, longitude: 77.6408 };

export default function Home() {
  const router = useRouter();
  const [origin, setOrigin] = useState(CUBBON);
  const [destination, setDestination] = useState(INDIRANAGAR);
  const [destinationQuery, setDestinationQuery] = useState(INDIRANAGAR.label);
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [selected, setSelected] = useState<RouteOption>();
  const [reports, setReports] = useState<RoadReport[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { nearbyReports().then(setReports).catch(() => setReports([])); }, []);
  async function locate() {
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") return Alert.alert("Location unavailable", "Enable location access to route from your position.");
    const current = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    setOrigin({ label: "Current location", latitude: current.coords.latitude, longitude: current.coords.longitude });
  }
  async function findRoutes() {
    setLoading(true);
    try {
      const resolved = destinationQuery === destination.label ? destination : await geocode(destinationQuery);
      setDestination(resolved);
      const result = await recommend(origin, resolved);
      setRoutes(result.routes); setSelected(result.routes.find((route) => route.is_recommended) ?? result.routes[0]);
    } catch (error) { Alert.alert("Route unavailable", error instanceof Error ? error.message : "Try again shortly."); }
    finally { setLoading(false); }
  }
  return <View style={styles.page}>
    <MapCanvas routes={routes} selected={selected} reports={reports} />
    <SafeAreaView pointerEvents="box-none" style={StyleSheet.absoluteFill}>
      <View style={styles.topbar}>
        <View style={styles.brand}><View style={styles.logo}><Ionicons name="navigate" size={18} color="white" /></View><Text style={styles.brandText}>PATHFINDER</Text></View>
        <Pressable accessibilityLabel="Open profile" onPress={() => router.push("/profile")} style={styles.iconButton}><Ionicons name="person-outline" size={21} color={colors.ink} /></Pressable>
      </View>
      <GlassSurface style={styles.search}>
        <View style={styles.placeRow}><View style={[styles.dot, { backgroundColor: colors.brand }]} /><View style={styles.placeText}><Text style={styles.placeLabel}>FROM</Text><Text numberOfLines={1} style={styles.placeValue}>{origin.label}</Text></View><Pressable onPress={locate}><Ionicons name="locate-outline" size={23} color={colors.brand} /></Pressable></View>
        <View style={styles.divider} />
        <View style={styles.placeRow}><View style={[styles.dot, { backgroundColor: colors.danger }]} /><View style={styles.placeText}><Text style={styles.placeLabel}>TO</Text><TextInput accessibilityLabel="Destination" value={destinationQuery} onChangeText={setDestinationQuery} placeholder="Search destination" style={styles.placeInput} /></View></View>
        <Pressable onPress={findRoutes} disabled={loading} style={styles.routeButton}>{loading ? <ActivityIndicator color="white" /> : <><Text style={styles.routeButtonText}>Find quality route</Text><Ionicons name="arrow-forward" color="white" size={19} /></>}</Pressable>
      </GlassSurface>
      <View style={styles.bottom} pointerEvents="box-none">
        {routes.length > 0 && <GlassSurface style={styles.routesPanel}>
          <View style={styles.panelHeader}><View><Text style={styles.panelTitle}>Route options</Text><Text style={styles.panelSub}>Balanced by time, distance and road quality</Text></View></View>
          <FlatList horizontal data={routes} keyExtractor={(item) => item.id} showsHorizontalScrollIndicator={false} contentContainerStyle={styles.routeList}
            renderItem={({ item }) => <RouteCard route={item} selected={item.id === selected?.id} onPress={() => setSelected(item)} />} />
        </GlassSurface>}
        <Pressable onPress={() => router.push("/report")} style={styles.reportButton}><Ionicons name="camera" color="white" size={22} /><Text style={styles.reportText}>Report road</Text></Pressable>
      </View>
    </SafeAreaView>
  </View>;
}
const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: "#DCE8E2" }, topbar: { marginTop: 12, marginHorizontal: 18, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  brand: { flexDirection: "row", alignItems: "center", gap: 9 }, logo: { width: 36, height: 36, borderRadius: 13, backgroundColor: colors.brand, alignItems: "center", justifyContent: "center", ...shadow },
  brandText: { color: colors.ink, fontSize: 14, fontWeight: "900", letterSpacing: 1.6 }, iconButton: { width: 42, height: 42, borderRadius: 16, backgroundColor: colors.glassStrong, alignItems: "center", justifyContent: "center", ...shadow },
  search: { margin: 18, marginTop: 14, padding: 15, height: 190 }, placeRow: { minHeight: 45, flexDirection: "row", alignItems: "center", gap: 12 }, dot: { width: 10, height: 10, borderRadius: 5 }, placeText: { flex: 1 },
  placeLabel: { fontSize: 9, fontWeight: "800", letterSpacing: 1, color: colors.muted }, placeValue: { fontSize: 16, fontWeight: "700", color: colors.ink, marginTop: 2 }, divider: { height: 1, backgroundColor: "rgba(40,75,64,0.12)", marginVertical: 5, marginLeft: 22 },
  placeInput: { fontSize: 16, fontWeight: "700", color: colors.ink, padding: 0, marginTop: 1 },
  routeButton: { height: 47, borderRadius: 16, backgroundColor: colors.brand, marginTop: 10, flexDirection: "row", gap: 8, alignItems: "center", justifyContent: "center" }, routeButtonText: { color: "white", fontSize: 15, fontWeight: "800" },
  bottom: { position: "absolute", left: 0, right: 0, bottom: 20, alignItems: "center", gap: 12 }, routesPanel: { width: "94%", height: 230 }, panelHeader: { paddingHorizontal: 18, paddingTop: 16 }, panelTitle: { fontSize: 18, fontWeight: "800", color: colors.ink }, panelSub: { fontSize: 11, color: colors.muted, marginTop: 2 }, routeList: { padding: 12, paddingTop: 10 },
  reportButton: { height: 50, paddingHorizontal: 22, borderRadius: 18, flexDirection: "row", alignItems: "center", gap: 8, backgroundColor: colors.ink, ...shadow }, reportText: { color: "white", fontWeight: "800" },
});

