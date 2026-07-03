import { useState } from "react";
import { ActivityIndicator, Alert, Image, Pressable, SafeAreaView, StyleSheet, Text, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import { GlassSurface } from "../components/GlassSurface";
import { submitReport } from "../src/api";
import { authToken } from "../src/auth";
import { colors } from "../src/theme";

export default function ReportScreen() {
  const router = useRouter(); const [asset, setAsset] = useState<ImagePicker.ImagePickerAsset>();
  const [description, setDescription] = useState(""); const [saving, setSaving] = useState(false);
  async function choose(camera: boolean) {
    const result = camera ? await ImagePicker.launchCameraAsync({ quality: 0.82 }) : await ImagePicker.launchImageLibraryAsync({ mediaTypes: ["images"], quality: 0.82 });
    if (!result.canceled) setAsset(result.assets[0]);
  }
  async function submit() {
    if (!asset) return Alert.alert("Photo required", "Capture or choose a clear road-surface photo.");
    setSaving(true);
    try {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (permission.status !== "granted") throw new Error("Location permission is required for road reports");
      const location = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const blob = await fetch(asset.uri).then((response) => response.blob());
      const form = new FormData();
      form.append("latitude", String(location.coords.latitude)); form.append("longitude", String(location.coords.longitude));
      form.append("description", description); form.append("image", blob, asset.fileName ?? "road.jpg");
      const report = await submitReport(form, await authToken());
      Alert.alert("Road assessed", `Quality score: ${Math.round(report.assessment?.road_quality ?? 0)}/100`, [{ text: "View map", onPress: () => router.replace("/") }]);
    } catch (error) { Alert.alert("Could not submit", error instanceof Error ? error.message : "Try again"); }
    finally { setSaving(false); }
  }
  return <SafeAreaView style={styles.page}><View style={styles.header}><Pressable onPress={() => router.back()} style={styles.back}><Ionicons name="arrow-back" size={22} color={colors.ink} /></Pressable><Text style={styles.title}>Report road quality</Text><View style={{ width: 42 }} /></View>
    <GlassSurface style={styles.card}><View style={styles.content}>
      <Pressable onPress={() => choose(true)} style={styles.preview}>{asset ? <Image source={{ uri: asset.uri }} style={StyleSheet.absoluteFill} /> : <><View style={styles.cameraIcon}><Ionicons name="camera" size={28} color="white" /></View><Text style={styles.previewTitle}>Capture the road surface</Text><Text style={styles.help}>Point down the road, avoid faces and number plates.</Text></>}</Pressable>
      <View style={styles.actions}><Pressable onPress={() => choose(true)} style={styles.secondary}><Ionicons name="camera-outline" size={20} color={colors.brand} /><Text style={styles.secondaryText}>Camera</Text></Pressable><Pressable onPress={() => choose(false)} style={styles.secondary}><Ionicons name="images-outline" size={20} color={colors.brand} /><Text style={styles.secondaryText}>Library</Text></Pressable></View>
      <Text style={styles.label}>OPTIONAL CONTEXT</Text><TextInput value={description} onChangeText={setDescription} multiline maxLength={1000} placeholder="Potholes after rain, broken lane markings?" placeholderTextColor="#82928D" style={styles.input} />
      <View style={styles.privacy}><Ionicons name="shield-checkmark-outline" size={20} color={colors.brand} /><Text style={styles.privacyText}>Your photo is assessed by the pretrained road-damage model before it influences routes.</Text></View>
      <Pressable onPress={submit} disabled={saving} style={styles.submit}>{saving ? <ActivityIndicator color="white" /> : <><Text style={styles.submitText}>Assess and submit</Text><Ionicons name="sparkles" size={18} color="white" /></>}</Pressable>
    </View></GlassSurface></SafeAreaView>;
}
const styles = StyleSheet.create({ page: { flex: 1, backgroundColor: colors.paper }, header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", padding: 18 }, back: { width: 42, height: 42, borderRadius: 15, backgroundColor: "white", alignItems: "center", justifyContent: "center" }, title: { fontSize: 17, fontWeight: "800", color: colors.ink }, card: { flex: 1, margin: 16, marginTop: 2 }, content: { flex: 1, padding: 18 }, preview: { height: 260, borderRadius: 22, overflow: "hidden", backgroundColor: "#DDE9E3", alignItems: "center", justifyContent: "center", padding: 24 }, cameraIcon: { width: 58, height: 58, borderRadius: 20, backgroundColor: colors.brand, alignItems: "center", justifyContent: "center" }, previewTitle: { fontSize: 18, fontWeight: "800", color: colors.ink, marginTop: 16 }, help: { color: colors.muted, textAlign: "center", marginTop: 6, lineHeight: 19 }, actions: { flexDirection: "row", gap: 10, marginVertical: 14 }, secondary: { flex: 1, height: 48, borderRadius: 15, borderWidth: 1, borderColor: "#C8D8D1", flexDirection: "row", gap: 7, alignItems: "center", justifyContent: "center" }, secondaryText: { color: colors.brand, fontWeight: "700" }, label: { fontSize: 10, letterSpacing: 1, fontWeight: "800", color: colors.muted, marginTop: 5 }, input: { minHeight: 84, marginTop: 8, borderRadius: 16, backgroundColor: "rgba(255,255,255,.72)", padding: 14, color: colors.ink, textAlignVertical: "top" }, privacy: { flexDirection: "row", gap: 9, marginVertical: 14, alignItems: "center" }, privacyText: { flex: 1, color: colors.muted, fontSize: 11, lineHeight: 16 }, submit: { height: 54, borderRadius: 18, backgroundColor: colors.brand, flexDirection: "row", gap: 9, alignItems: "center", justifyContent: "center" }, submitText: { color: "white", fontWeight: "800", fontSize: 15 } });

