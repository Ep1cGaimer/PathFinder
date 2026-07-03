import type { PropsWithChildren } from "react";
import { StyleSheet, View, type ViewStyle } from "react-native";
import { BlurView } from "expo-blur";
import { colors, shadow } from "../src/theme";

export function GlassSurface({ children, style }: PropsWithChildren<{ style?: ViewStyle | ViewStyle[] }>) {
  return (
    <View style={[styles.shell, style]}>
      <BlurView intensity={62} tint="light" style={StyleSheet.absoluteFill} />
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: { overflow: "hidden", borderRadius: 26, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.glass, ...shadow },
  content: { flex: 1 },
});

