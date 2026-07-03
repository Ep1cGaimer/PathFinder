export const colors = {
  ink: "#202124",
  muted: "#5F6368",
  subtle: "#80868B",
  paper: "#F8F9FA",
  surface: "#FFFFFF",
  surfaceAlt: "#F1F3F4",
  border: "#DADCE0",
  line: "rgba(255,255,255,0.72)",
  glass: "rgba(255,255,255,0.92)",
  brand: "#13795B",
  brandDark: "#0B5742",
  brandSoft: "#E3F3EC",
  good: "#188038",
  warning: "#F9AB00",
  poor: "#F29900",
  danger: "#D93025",
  unknown: "#9AA0A6",
  routeAlt: "#7B858D",
} as const;

export function qualityColor(quality: number | null | undefined): string {
  if (quality == null) return colors.unknown;
  if (quality < 30) return "#C5221F";
  if (quality < 50) return colors.poor;
  if (quality < 70) return colors.warning;
  if (quality < 85) return "#34A853";
  return colors.good;
}

export const shadow = {
  shadowColor: "#3C4043",
  shadowOpacity: 0.18,
  shadowRadius: 12,
  shadowOffset: { width: 0, height: 4 },
  elevation: 6,
} as const;
