import { getApps, initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

export const isFirebaseConfigured = Boolean(
  process.env.EXPO_PUBLIC_FIREBASE_API_KEY && process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID,
);

const app = isFirebaseConfigured
  ? getApps()[0] ?? initializeApp({
      apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
      authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN,
      projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID,
      storageBucket: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET,
      messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
      appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID,
    })
  : null;

export const auth = app ? getAuth(app) : null;

export async function authToken(): Promise<string> {
  if (__DEV__ && !auth?.currentUser) return "dev-token";
  if (!auth?.currentUser) throw new Error("Sign in to contribute a road report");
  return auth.currentUser.getIdToken();
}