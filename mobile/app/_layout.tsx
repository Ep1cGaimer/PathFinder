import React from 'react';
import { Stack } from 'expo-router';
import { useEffect, useState } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';

export default function RootLayout() {
  const [isFirebaseReady, setIsFirebaseReady] = useState(false);

  useEffect(() => {
    const initializeFirebase = async () => {
      try {
        const firebase = await import('@react-native-firebase/app');
        const apps = firebase.default.apps;

        if (apps.length === 0) {
          await firebase.default.initializeApp({
            apiKey: "AIzaSyCekrXLWKtRHundaDjtr5MhRxnOrNDZzNY",
            authDomain: "pathfinder-b5c55.firebaseapp.com",
            projectId: "pathfinder-b5c55",
            storageBucket: "pathfinder-b5c55.firebasestorage.app",
            messagingSenderId: "256841323755",
            appId: "1:256841323755:android:39cbf950e067a8db015aae"
          });
        }

        setIsFirebaseReady(true);
      } catch (error) {
        console.error('Firebase initialization failed:', error);
        setIsFirebaseReady(true);
      }
    };

    initializeFirebase();
  }, []);

  if (!isFirebaseReady) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#007BFF" />
      </View>
    );
  }

  return (
    <Stack>
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="login" options={{ headerShown: false }} />
      <Stack.Screen name="register" options={{ headerShown: false }} />
      <Stack.Screen name="home" options={{ headerShown: false }} />
      <Stack.Screen name="camera" options={{ headerShown: false }} />
      <Stack.Screen name="profile" options={{ headerShown: false }} />
    </Stack>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
});