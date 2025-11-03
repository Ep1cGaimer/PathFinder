import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import CustomMapView from '../src/components/MapView';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location'
import  SearchBar  from '../src/components/SearchBar';

export default function HomeScreen() {
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [routeRequest, setRouteRequest] = useState({
    origin: "",
    destination: ""
  });

  useEffect(() => {
    (async ()=> {
      let {status} = await Location.requestForegroundPermissionsAsync();
      if(status !== 'granted'){
        Alert.alert('Permission access to location was denied');
        return;
      }

      let location = await Location.getCurrentPositionAsync({});
      const reverseGeocode = await Location.reverseGeocodeAsync(location.coords);
      if(reverseGeocode.length > 0){
        const address = reverseGeocode[0];
        setOrigin(`${address.name}, ${address.city}, ${address.region}`); //sets current location as origin
      }
    })();
  },[]);

  const handleGetRoute = () =>{
    if(!origin || !destination){
      Alert.alert('Please enter both origin and destination');
      return;
    }
    setRouteRequest({origin:origin,destination:destination});
  }

  const openCamera = () => {
    router.push('/camera');
  };

  const handleLogout = async () => {
    if (isLoggingOut) return;

    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Logout',
          onPress: async () => {
            setIsLoggingOut(true);
            try {
              const auth = await import('@react-native-firebase/auth');
              await auth.default().signOut();
              router.replace('/login');
            } catch (error: any) {
              let errorMessage = 'Failed to logout. Please try again.';

              if (error.code === 'auth/network-request-failed') {
                errorMessage = 'Network error. Please check your connection.';
              } else if (error.code === 'auth/too-many-requests') {
                errorMessage = 'Too many attempts. Please try again later.';
              } else if (error.message) {
                errorMessage = error.message;
              }

              console.error('Logout error:', error);
              Alert.alert('Logout Failed', errorMessage);
            } finally {
              setIsLoggingOut(false);
            }
          },
          style: 'destructive',
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>PathFinder</Text>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color="black" />
        </TouchableOpacity>
      </View>
      <SearchBar
        origin={origin}
        onOriginChange={setOrigin}
        destination={destination}
        onDestinationChange={setDestination}
        onGetRoute={handleGetRoute}
        
      />
      
      <CustomMapView routeRequest={routeRequest}/>
      <TouchableOpacity style={styles.cameraButton} onPress={openCamera}>
        <Ionicons name="camera" size={28} color="white" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginTop: 50,
    marginBottom: 10,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    flex: 1,
    textAlign: 'center',
  },
  logoutButton: {
    padding: 8,
  },
  cameraButton: {
    position: 'absolute',
    bottom: 30,
    right: 30,
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#007BFF',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 3 },
    shadowRadius: 4,
    elevation: 5,
  },
});
