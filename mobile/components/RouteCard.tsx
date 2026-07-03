import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { RouteOption } from "../src/types";
import { colors } from "../src/theme";

export function RouteCard({ route, selected, onPress }: { route: RouteOption; selected: boolean; onPress: () => void }) {
  const coverage = Math.round(route.quality_coverage * 100);
  return (
    <Pressable onPress={onPress} style={[styles.card, selected && styles.selected]}>
      <View style={styles.top}>
        <View style={styles.titleRow}>
          {route.is_recommended && <View style={styles.badge}><Text style={styles.badgeText}>BEST FIT</Text></View>}
          <Text numberOfLines={1} style={styles.title}>{route.summary}</Text>
        </View>
        <Ionicons name={selected ? "checkmark-circle" : "ellipse-outline"} size={22} color={selected ? colors.brand : colors.muted} />
      </View>
      <Text style={styles.time}>{Math.round(route.duration_seconds / 60)} min <Text style={styles.distance}> ? {(route.distance_meters / 1000).toFixed(1)} km</Text></Text>
      <View style={styles.metrics}>
        <Metric label="ROAD" value={`${Math.round(route.road_quality)}/100`} />
        <Metric label="COVERAGE" value={`${coverage}%`} />
        <Metric label="SCORE" value={route.pathfinder_score.toFixed(1)} />
      </View>
    </Pressable>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return <View><Text style={styles.metricLabel}>{label}</Text><Text style={styles.metricValue}>{value}</Text></View>;
}
const styles = StyleSheet.create({
  card: { width: 270, padding: 16, marginRight: 12, borderRadius: 20, backgroundColor: "rgba(255,255,255,0.58)", borderWidth: 1, borderColor: "rgba(255,255,255,0.8)" },
  selected: { borderColor: colors.brand, backgroundColor: "rgba(240,252,247,0.92)" },
  top: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  titleRow: { flex: 1, gap: 6 }, title: { fontSize: 14, fontWeight: "700", color: colors.ink },
  badge: { alignSelf: "flex-start", backgroundColor: colors.brand, borderRadius: 8, paddingHorizontal: 7, paddingVertical: 3 },
  badgeText: { color: "white", fontWeight: "800", fontSize: 9, letterSpacing: 0.8 },
  time: { fontSize: 25, fontWeight: "800", color: colors.ink, marginTop: 12 },
  distance: { fontSize: 14, color: colors.muted, fontWeight: "600" },
  metrics: { flexDirection: "row", justifyContent: "space-between", marginTop: 14 },
  metricLabel: { fontSize: 9, letterSpacing: 0.8, color: colors.muted, fontWeight: "700" },
  metricValue: { fontSize: 14, color: colors.ink, fontWeight: "800", marginTop: 2 },
});

