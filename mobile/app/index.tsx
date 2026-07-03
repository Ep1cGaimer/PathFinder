import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { ActivityIndicator, Alert, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import * as Location from "expo-location";
import { MapCanvas } from "../components/MapCanvas";
import { RouteCard } from "../components/RouteCard";
import { autocomplete, geocode, nearbyReports, nearbyRoadQuality, recommend } from "../src/api";
import { colors, shadow } from "../src/theme";
import type { Coordinate, MapBounds, PlaceSuggestion, RoadQualitySegment, RoadReport, RouteOption } from "../src/types";

const CUBBON: Coordinate = { label: "Cubbon Park", latitude: 12.9763, longitude: 77.5929 };
const INDIRANAGAR: Coordinate = { label: "Indiranagar", latitude: 12.9784, longitude: 77.6408 };
const DEFAULT_BOUNDS: MapBounds = { min_lat: 12.90, min_lng: 77.50, max_lat: 13.05, max_lng: 77.75, zoom: 13 };
const AUTOCOMPLETE_SESSION_TOKEN = "pathfinder-web-session";

function subscribeDesktop(callback: () => void) {
  if (typeof window === "undefined" || !window.matchMedia) return () => undefined;
  const media = window.matchMedia("(min-width: 900px)");
  media.addEventListener("change", callback);
  return () => media.removeEventListener("change", callback);
}

function desktopSnapshot() {
  return typeof window !== "undefined" && Boolean(window.matchMedia?.("(min-width: 900px)").matches);
}

export default function Home() {
  const router = useRouter();
  const desktop = useSyncExternalStore(subscribeDesktop, desktopSnapshot, () => false);
  const [origin, setOrigin] = useState(CUBBON);
  const [destination, setDestination] = useState(INDIRANAGAR);
  const [destinationQuery, setDestinationQuery] = useState(INDIRANAGAR.label);
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [routes, setRoutes] = useState<RouteOption[]>([]);
  const [selected, setSelected] = useState<RouteOption>();
  const [reports, setReports] = useState<RoadReport[]>([]);
  const [nearbySegments, setNearbySegments] = useState<RoadQualitySegment[]>([]);
  const [showQuality, setShowQuality] = useState(true);
  const [showReports, setShowReports] = useState(false);
  const [loading, setLoading] = useState(false);
  const [qualityLoading, setQualityLoading] = useState(true);
  const lastBounds = useRef(DEFAULT_BOUNDS);
  const fetchTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const selectedSuggestion = useRef<string | null>(null);

  useEffect(() => {
    nearbyReports().then(setReports).catch(() => setReports([]));
  }, []);

  useEffect(() => {
    if (!showQuality) return;
    nearbyRoadQuality(lastBounds.current)
      .then(setNearbySegments)
      .catch(() => setNearbySegments([]))
      .finally(() => setQualityLoading(false));
  }, [showQuality]);

  useEffect(() => {
    if (destinationQuery.trim().length < 2 || destinationQuery === destination.label || destinationQuery === selectedSuggestion.current) return;
    const timer = setTimeout(() => {
      autocomplete(destinationQuery.trim(), AUTOCOMPLETE_SESSION_TOKEN)
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, 250);
    return () => clearTimeout(timer);
  }, [destination.label, destinationQuery]);

  const handleViewport = useCallback((bounds: MapBounds) => {
    lastBounds.current = bounds;
    if (!showQuality) return;
    if (fetchTimer.current) clearTimeout(fetchTimer.current);
    fetchTimer.current = setTimeout(() => {
      nearbyRoadQuality(bounds).then(setNearbySegments).catch(() => undefined);
    }, 350);
  }, [showQuality]);

  const selectRoute = useCallback((route: RouteOption) => setSelected(route), []);

  function toggleQuality() {
    const next = !showQuality;
    setShowQuality(next);
    if (!next) setNearbySegments([]);
    else setQualityLoading(true);
  }

  async function locate() {
    const permission = await Location.requestForegroundPermissionsAsync();
    if (permission.status !== "granted") {
      Alert.alert("Location unavailable", "Enable location access to route from your position.");
      return;
    }
    const current = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
    setOrigin({ label: "Current location", latitude: current.coords.latitude, longitude: current.coords.longitude });
  }

  async function findRoutes() {
    if (!destinationQuery.trim()) return;
    setLoading(true);
    setSuggestions([]);
    try {
      const resolved = destinationQuery === destination.label ? destination : await geocode(destinationQuery.trim());
      setDestination(resolved);
      const result = await recommend(origin, resolved);
      setRoutes(result.routes);
      setSelected(result.routes.find((route) => route.is_recommended) ?? result.routes[0]);
      nearbyRoadQuality(lastBounds.current).then(setNearbySegments).catch(() => undefined);
    } catch (error) {
      Alert.alert("Route unavailable", error instanceof Error ? error.message : "Try again shortly.");
    } finally {
      setLoading(false);
    }
  }

  const searchForm = <>
    <View style={styles.fieldRow}>
      <View style={[styles.endpointDot, { backgroundColor: colors.brand }]}><Text style={styles.endpointLetter}>A</Text></View>
      <View style={styles.fieldBody}>
        <Text style={styles.fieldLabel}>START</Text>
        <Text numberOfLines={1} style={styles.fieldValue}>{origin.label}</Text>
      </View>
      <Pressable accessibilityLabel="Use current location" onPress={locate} style={styles.fieldAction}><Ionicons name="locate-outline" size={21} color={colors.brand} /></Pressable>
    </View>
    <View style={styles.connector} />
    <View style={styles.fieldRow}>
      <View style={[styles.endpointDot, { backgroundColor: colors.ink }]}><Text style={styles.endpointLetter}>B</Text></View>
      <View style={styles.fieldBody}>
        <Text style={styles.fieldLabel}>DESTINATION</Text>
        <TextInput
          accessibilityLabel="Destination"
          value={destinationQuery}
          onChangeText={(value) => { selectedSuggestion.current = null; setDestinationQuery(value); setSuggestions([]); }}
          onSubmitEditing={findRoutes}
          placeholder="Search Bengaluru"
          placeholderTextColor={colors.subtle}
          returnKeyType="search"
          style={styles.fieldInput}
        />
      </View>
    </View>
    {suggestions.length > 0 && <View style={styles.suggestions}>
      {suggestions.slice(0, 5).map((item) => <Pressable key={item.place_id} onPress={() => { selectedSuggestion.current = item.label; setDestinationQuery(item.label); setSuggestions([]); }} style={styles.suggestion}>
        <Ionicons name="location-outline" size={19} color={colors.muted} />
        <Text numberOfLines={2} style={styles.suggestionText}>{item.label}</Text>
      </Pressable>)}
    </View>}
    <Pressable onPress={findRoutes} disabled={loading} style={[styles.routeButton, loading && styles.disabled]}>
      {loading ? <ActivityIndicator color="white" /> : <><Ionicons name="navigate" size={18} color="white" /><Text style={styles.routeButtonText}>Find the best road</Text></>}
    </Pressable>
  </>;

  const routeResults = routes.length > 0 ? <>
    <View style={styles.resultsHeader}>
      <View><Text style={styles.resultsTitle}>Route options</Text><Text style={styles.resultsSub}>Balanced for time and road condition</Text></View>
      <Text style={styles.resultsCount}>{routes.length}</Text>
    </View>
    <ScrollView style={styles.resultsScroll} contentContainerStyle={styles.resultsContent} showsVerticalScrollIndicator={false}>
      {routes.map((route) => <RouteCard key={route.id} route={route} selected={route.id === selected?.id} onPress={() => setSelected(route)} />)}
    </ScrollView>
  </> : <View style={styles.emptyState}>
    <View style={styles.emptyIcon}><Ionicons name="map-outline" size={24} color={colors.brand} /></View>
    <Text style={styles.emptyTitle}>Choose your destination</Text>
    <Text style={styles.emptyText}>Pathfinder compares travel time with crowdsourced road-surface observations.</Text>
  </View>;

  return <View style={styles.page}>
    <MapCanvas
      routes={routes}
      selected={selected}
      nearbySegments={nearbySegments}
      reports={reports}
      origin={origin}
      destination={destination}
      showReports={showReports}
      onSelectRoute={selectRoute}
      onViewportChange={handleViewport}
    />
    <SafeAreaView pointerEvents="box-none" style={StyleSheet.absoluteFill}>
      {desktop ? <View pointerEvents="auto" style={styles.sidebar}>
        <View style={styles.header}>
          <View style={styles.brandMark}><Ionicons name="navigate" size={18} color="white" /></View>
          <View style={styles.brandCopy}><Text style={styles.brand}>Pathfinder</Text><Text style={styles.tagline}>Better roads. Better routes.</Text></View>
          <Pressable accessibilityLabel="Open profile" onPress={() => router.push("/profile")} style={styles.profileButton}><Ionicons name="person-outline" size={21} color={colors.ink} /></Pressable>
        </View>
        <View style={styles.searchSection}>{searchForm}</View>
        <View style={styles.separator} />
        <View style={styles.resultsArea}>{routeResults}</View>
        <Pressable onPress={() => router.push("/report")} style={styles.sidebarReport}><Ionicons name="camera-outline" size={20} color={colors.brand} /><Text style={styles.sidebarReportText}>Report a road condition</Text></Pressable>
      </View> : <>
        <View pointerEvents="auto" style={styles.mobileHeader}>
          <View style={styles.mobileBrandRow}><View style={styles.brandMark}><Ionicons name="navigate" size={17} color="white" /></View><Text style={styles.mobileBrand}>Pathfinder</Text><Pressable accessibilityLabel="Open profile" onPress={() => router.push("/profile")} style={styles.mobileProfile}><Ionicons name="person-outline" size={20} color={colors.ink} /></Pressable></View>
          {searchForm}
        </View>
        {routes.length > 0 && <View pointerEvents="auto" style={styles.mobileSheet}><View style={styles.sheetHandle} />{routeResults}</View>}
      </>}

      <View pointerEvents="auto" style={[styles.layerControls, desktop ? styles.layerDesktop : styles.layerMobile]}>
        <Pressable accessibilityRole="switch" accessibilityState={{ checked: showQuality }} onPress={toggleQuality} style={[styles.layerButton, showQuality && styles.layerActive]}>
          {qualityLoading ? <ActivityIndicator size="small" color={colors.brand} /> : <Ionicons name="analytics-outline" size={18} color={showQuality ? colors.brand : colors.muted} />}
          <Text style={[styles.layerText, showQuality && styles.layerTextActive]}>Road quality</Text>
        </Pressable>
        <Pressable accessibilityRole="switch" accessibilityState={{ checked: showReports }} onPress={() => setShowReports((value) => !value)} style={[styles.layerButton, showReports && styles.layerActive]}>
          <Ionicons name="radio-button-on-outline" size={18} color={showReports ? colors.brand : colors.muted} />
          <Text style={[styles.layerText, showReports && styles.layerTextActive]}>Reports</Text>
        </Pressable>
      </View>

      <View pointerEvents="none" style={[styles.legend, desktop ? styles.legendDesktop : styles.legendMobile]}>
        <Text style={styles.legendTitle}>ROAD QUALITY</Text>
        <View style={styles.legendScale}><View style={[styles.legendBand, { backgroundColor: colors.danger }]} /><View style={[styles.legendBand, { backgroundColor: colors.poor }]} /><View style={[styles.legendBand, { backgroundColor: colors.warning }]} /><View style={[styles.legendBand, { backgroundColor: "#34A853" }]} /><View style={[styles.legendBand, { backgroundColor: colors.good }]} /></View>
        <View style={styles.legendLabels}><Text style={styles.legendLabel}>Rough</Text><Text style={styles.legendLabel}>Smooth</Text></View>
      </View>

      {!desktop && <Pressable onPress={() => router.push("/report")} style={[styles.floatingReport, routes.length > 0 && styles.floatingReportRaised]}><Ionicons name="camera" size={21} color="white" /></Pressable>}
    </SafeAreaView>
  </View>;
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: "#E8EAED" },
  sidebar: { width: 410, height: "100%", backgroundColor: colors.surface, borderRightWidth: 1, borderRightColor: colors.border, ...shadow },
  header: { height: 74, paddingHorizontal: 18, flexDirection: "row", alignItems: "center", borderBottomWidth: 1, borderBottomColor: colors.border },
  brandMark: { width: 36, height: 36, borderRadius: 11, backgroundColor: colors.brand, alignItems: "center", justifyContent: "center" },
  brandCopy: { marginLeft: 11, flex: 1 }, brand: { color: colors.ink, fontSize: 18, fontWeight: "700" }, tagline: { color: colors.muted, fontSize: 11, marginTop: 1 },
  profileButton: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceAlt },
  searchSection: { padding: 18, paddingBottom: 16 },
  fieldRow: { minHeight: 55, borderWidth: 1, borderColor: colors.border, borderRadius: 12, paddingHorizontal: 12, flexDirection: "row", alignItems: "center", backgroundColor: colors.surface },
  endpointDot: { width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center" }, endpointLetter: { color: "white", fontSize: 10, fontWeight: "800" },
  fieldBody: { flex: 1, paddingHorizontal: 10 }, fieldLabel: { color: colors.subtle, fontSize: 9, fontWeight: "700", letterSpacing: 0.8 }, fieldValue: { color: colors.ink, fontSize: 14, fontWeight: "600", marginTop: 2 },
  fieldInput: { padding: 0, color: colors.ink, fontSize: 15, fontWeight: "600", marginTop: 1, outlineStyle: "none" } as never,
  fieldAction: { width: 34, height: 34, alignItems: "center", justifyContent: "center" }, connector: { height: 8, width: 2, backgroundColor: colors.border, marginLeft: 23 },
  suggestions: { marginTop: 8, borderWidth: 1, borderColor: colors.border, borderRadius: 12, overflow: "hidden", backgroundColor: colors.surface, ...shadow },
  suggestion: { minHeight: 48, paddingHorizontal: 13, paddingVertical: 9, flexDirection: "row", gap: 9, alignItems: "center", borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border }, suggestionText: { flex: 1, color: colors.ink, fontSize: 13 },
  routeButton: { height: 48, marginTop: 13, borderRadius: 12, backgroundColor: colors.brand, flexDirection: "row", gap: 8, alignItems: "center", justifyContent: "center" }, disabled: { opacity: 0.7 }, routeButtonText: { color: "white", fontWeight: "700", fontSize: 14 },
  separator: { height: 1, backgroundColor: colors.border }, resultsArea: { flex: 1 }, resultsHeader: { paddingHorizontal: 18, paddingTop: 17, paddingBottom: 10, flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  resultsTitle: { color: colors.ink, fontSize: 16, fontWeight: "700" }, resultsSub: { color: colors.muted, fontSize: 11, marginTop: 2 }, resultsCount: { color: colors.brand, backgroundColor: colors.brandSoft, borderRadius: 12, minWidth: 24, height: 24, textAlign: "center", lineHeight: 24, fontWeight: "700" },
  resultsScroll: { flex: 1 }, resultsContent: { paddingBottom: 10 }, emptyState: { flex: 1, paddingHorizontal: 34, alignItems: "center", justifyContent: "center" }, emptyIcon: { width: 52, height: 52, borderRadius: 26, backgroundColor: colors.brandSoft, alignItems: "center", justifyContent: "center" }, emptyTitle: { color: colors.ink, fontSize: 16, fontWeight: "700", marginTop: 14 }, emptyText: { color: colors.muted, textAlign: "center", lineHeight: 19, fontSize: 12, marginTop: 6 },
  sidebarReport: { margin: 14, height: 48, borderRadius: 12, borderWidth: 1, borderColor: colors.border, flexDirection: "row", gap: 8, alignItems: "center", justifyContent: "center" }, sidebarReportText: { color: colors.brand, fontSize: 13, fontWeight: "700" },
  layerControls: { position: "absolute", gap: 8 }, layerDesktop: { top: 18, right: 18 }, layerMobile: { top: 226, right: 12 }, layerButton: { height: 40, paddingHorizontal: 12, borderRadius: 8, backgroundColor: colors.surface, flexDirection: "row", alignItems: "center", gap: 7, borderWidth: 1, borderColor: colors.border, ...shadow }, layerActive: { borderColor: colors.brand, backgroundColor: colors.brandSoft }, layerText: { color: colors.muted, fontSize: 12, fontWeight: "600" }, layerTextActive: { color: colors.brandDark },
  legend: { position: "absolute", width: 154, padding: 10, borderRadius: 8, backgroundColor: "rgba(255,255,255,0.96)", borderWidth: 1, borderColor: colors.border, ...shadow }, legendDesktop: { right: 18, bottom: 20 }, legendMobile: { right: 12, bottom: 88 }, legendTitle: { color: colors.muted, fontSize: 9, fontWeight: "800", letterSpacing: 0.8 }, legendScale: { height: 6, marginTop: 7, flexDirection: "row", borderRadius: 3, overflow: "hidden" }, legendBand: { flex: 1 }, legendLabels: { flexDirection: "row", justifyContent: "space-between", marginTop: 4 }, legendLabel: { color: colors.subtle, fontSize: 9 },
  mobileHeader: { margin: 12, padding: 12, borderRadius: 16, backgroundColor: "rgba(255,255,255,0.97)", borderWidth: 1, borderColor: colors.border, ...shadow }, mobileBrandRow: { height: 38, flexDirection: "row", alignItems: "center", marginBottom: 9 }, mobileBrand: { flex: 1, marginLeft: 9, fontSize: 17, color: colors.ink, fontWeight: "700" }, mobileProfile: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.surfaceAlt, alignItems: "center", justifyContent: "center" },
  mobileSheet: { position: "absolute", left: 0, right: 0, bottom: 0, maxHeight: "42%", minHeight: 210, borderTopLeftRadius: 22, borderTopRightRadius: 22, backgroundColor: colors.surface, ...shadow }, sheetHandle: { width: 40, height: 4, borderRadius: 2, backgroundColor: colors.border, alignSelf: "center", marginTop: 8 },
  floatingReport: { position: "absolute", right: 16, bottom: 24, width: 52, height: 52, borderRadius: 16, backgroundColor: colors.brand, alignItems: "center", justifyContent: "center", ...shadow }, floatingReportRaised: { bottom: "44%" },
});