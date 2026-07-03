import { Pressable, StyleSheet, Text, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { RouteOption } from "../src/types";
import { colors, qualityColor } from "../src/theme";

export function RouteCard({ route, selected, onPress }: { route: RouteOption; selected: boolean; onPress: () => void }) {
  const coverage = Math.round(route.quality_coverage * 100);
  const minutes = Math.max(1, Math.round(route.duration_seconds / 60));
  const qualityLabel = coverage === 0 ? "No quality data" : `${Math.round(route.road_quality)}/100 road quality`;
  return (
    <Pressable accessibilityRole="button" accessibilityState={{ selected }} onPress={onPress} style={[styles.card, selected && styles.selected]}>
      <View style={styles.leading}><View style={[styles.routeLine, { backgroundColor: qualityColor(coverage ? route.road_quality : null) }]} /></View>
      <View style={styles.content}>
        <View style={styles.titleRow}>
          <Text numberOfLines={1} style={styles.time}>{minutes} min</Text>
          {route.is_recommended && <View style={styles.badge}><Text style={styles.badgeText}>BEST</Text></View>}
        </View>
        <Text numberOfLines={1} style={styles.summary}>{route.summary || "Recommended route"}</Text>
        <Text style={styles.meta}>{(route.distance_meters / 1000).toFixed(1)} km - {qualityLabel}</Text>
        <View style={styles.coverageRow}>
          <View style={styles.coverageTrack}><View style={[styles.coverageFill, { width: `${coverage}%` }]} /></View>
          <Text style={styles.coverageText}>{coverage}% observed</Text>
        </View>
      </View>
      <Ionicons name={selected ? "checkmark-circle" : "chevron-forward"} size={21} color={selected ? colors.brand : colors.subtle} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { minHeight: 112, paddingHorizontal: 16, paddingVertical: 14, flexDirection: "row", alignItems: "center", borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border, backgroundColor: colors.surface },
  selected: { backgroundColor: colors.brandSoft },
  leading: { width: 18, alignSelf: "stretch", alignItems: "center", paddingVertical: 3 },
  routeLine: { width: 5, flex: 1, minHeight: 54, borderRadius: 4 },
  content: { flex: 1, paddingHorizontal: 10 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  time: { fontSize: 20, lineHeight: 24, fontWeight: "700", color: colors.ink },
  badge: { backgroundColor: colors.brand, borderRadius: 10, paddingHorizontal: 7, paddingVertical: 3 },
  badgeText: { color: "white", fontSize: 9, fontWeight: "800", letterSpacing: 0.5 },
  summary: { color: colors.ink, fontSize: 14, fontWeight: "600", marginTop: 2 },
  meta: { color: colors.muted, fontSize: 12, marginTop: 3 },
  coverageRow: { marginTop: 9, flexDirection: "row", alignItems: "center", gap: 9 },
  coverageTrack: { height: 4, borderRadius: 2, backgroundColor: colors.border, flex: 1, overflow: "hidden" },
  coverageFill: { height: 4, borderRadius: 2, backgroundColor: colors.brand },
  coverageText: { fontSize: 10, color: colors.subtle, width: 72, textAlign: "right" },
});