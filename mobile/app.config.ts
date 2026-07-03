import type { ExpoConfig } from "expo/config";

const config: ExpoConfig = {
  name: "Pathfinder",
  slug: "pathfinder-road-quality",
  scheme: "pathfinder",
  version: "1.0.0",
  orientation: "portrait",
  userInterfaceStyle: "light",
  icon: "./assets/images/icon.png",
  plugins: [
    "expo-router",
    ["expo-camera", { cameraPermission: "Use your camera to report road conditions." }],
    ["expo-image-picker", { photosPermission: "Choose a road photo to assess its condition." }],
    ["expo-build-properties", { android: { minSdkVersion: 24 } }],
  ],
  android: {
    package: "com.epicgaimer.pathfinder",
    permissions: ["ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION"],
    adaptiveIcon: { foregroundImage: "./assets/images/adaptive-icon.png", backgroundColor: "#EAF1EE" },
    config: { googleMaps: { apiKey: process.env.EXPO_PUBLIC_GOOGLE_MAPS_ANDROID_KEY ?? "" } },
  },
  ios: { bundleIdentifier: "com.epicgaimer.pathfinder", supportsTablet: true },
  web: { bundler: "metro", output: "static", favicon: "./assets/images/favicon.png" },
  extra: { eas: { projectId: "475b9783-843e-4304-ab14-6d2c969150f3" } },
  owner: "epic_gaimer",
};

export default config;
