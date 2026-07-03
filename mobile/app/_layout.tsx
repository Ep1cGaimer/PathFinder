import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { GestureHandlerRootView } from "react-native-gesture-handler";

export default function Layout() {
  return <GestureHandlerRootView style={{ flex: 1 }}>
    <StatusBar style="dark" />
    <Stack screenOptions={{ headerShown: false, animation: "fade" }} />
  </GestureHandlerRootView>;
}

