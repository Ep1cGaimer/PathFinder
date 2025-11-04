import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import CustomMapView from '../src/components/MapView';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location'
import  SearchBar  from '../src/components/SearchBar';
import { FlatList } from 'react-native';

type Route = {
  summary: string;
  distance_meters: number;
  duration_seconds: number;
  road_quality_score: number;
  pathfinder_score: number;
  is_recommended: boolean;
  overview_polyline: string;
};

const API_BASE_URL = 'http://10.72.90.24:8000';

export default function HomeScreen() {
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [routeRequest, setRouteRequest] = useState({
    origin: "",
    destination: ""
  });
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
  const [goToCurrentLocation, setGoToCurrentLocation] = useState(false);
  const [showRouteList, setShowRouteList] = useState(false);

  const handleLocateMe = () => {
    // toggling triggers re-render and signals map to center on location
    setGoToCurrentLocation(prev => !prev);
  };


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

  const handleGetRoute = (destination: String) =>{
    setRoutes([]);
    setSelectedRoute(null); //clear previous alternative routes
    if(!origin || !destination){
      Alert.alert('Please enter both origin and destination');
      return;
    }
    fetch(`${API_BASE_URL}/get_directions`,{
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({start: origin, end: destination}),
      })
      .then(res => res.json())
      .then(data => {
        if(data.routes && data.routes.length > 0){
          setRoutes(data.routes);
          const recommendedRoute = data.routes.find((r:Route) => r.is_recommended); //make sure to fix here, need to specify type
          setSelectedRoute(recommendedRoute || data.routes[0]);
          setShowRouteList(true);
        }else{
          Alert.alert('No routes found.');
          setRoutes([]);
          setSelectedRoute(null);
        }
      })
      .catch( err =>{
        console.log(err);
        Alert.alert('Error','Failed to fetch routes.');
        setRoutes([]);
        setSelectedRoute(null);
      });
    // setRouteRequest({origin:origin,destination:destination});
  };


  const openCamera = () => {
    router.push('/camera');
  };

  const openProfile = () => {
    router.push('/profile');
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

    const renderRouterItem = ({ item }: { item: Route }) =>(
    <TouchableOpacity
    style={[
      styles.routeItem,
      item.overview_polyline === selectedRoute?.overview_polyline && styles.selectedRouteItem,
    ]}
    onPress={() => {
      setSelectedRoute(item);
      setShowRouteList(false);
    }}
    >
      <Text style={styles.routeSummary}>{item.summary}</Text>
      <Text>Distance: {(item.distance_meters / 1000).toFixed(2)} km</Text>
      <Text>Duration: {Math.round(item.duration_seconds / 60)} mins</Text>
      <Text>Road Quality: {item.road_quality_score.toFixed(2)}</Text>
      <Text>Pathfinder Score: {item.pathfinder_score.toFixed(2)}</Text>
      {item.is_recommended && <Text style={styles.recommendedText}>Recommended</Text>}
    </TouchableOpacity>
  );


  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.userIconButton} onPress={openProfile}>
          <Ionicons name="person-circle-outline" size={28} color="#fff" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={24} color="#fff" />
        </TouchableOpacity>
      </View>
      <SearchBar
        origin={origin}
        onOriginChange={setOrigin}
        destination={destination}
        onDestinationChange={setDestination}
        onGetRoute={handleGetRoute}

      />

      <CustomMapView
      routes={routes}
      selectedRoute={selectedRoute}
      goToCurrentLocation={goToCurrentLocation}
      />
      {showRouteList && routes.length > 0 &&(
        <FlatList
        data={routes}
        renderItem={renderRouterItem}
        keyExtractor={(item: Route, index: number) => index.toString()}
        horizontal
        style={styles.routeList}
        showsHorizontalScrollIndicator = {false}
        />
      )}
      <TouchableOpacity style={styles.locationButton} onPress={handleLocateMe}>
        <Ionicons name="locate" size={24} color="#000" />
      </TouchableOpacity>

      <TouchableOpacity style={styles.cameraButton} onPress={openCamera}>
        <Ionicons name="camera" size={28} color="#fff" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 15,
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 10,
  },
  userIconButton: {
    padding: 10,
    backgroundColor: '#000',
    borderRadius: 25,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 3,
    elevation: 3,
  },
  logoutButton: {
    padding: 10,
    backgroundColor: '#000',
    borderRadius: 25,
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 3,
    elevation: 3,
  },
  locationButton: {
  position: 'absolute',
  bottom: 120, // just above the camera button (70 height + ~20px gap)
  right: 30,
  width: 70,
  height: 70,
  borderRadius: 35,
  backgroundColor: '#fff',
  justifyContent: 'center',
  alignItems: 'center',
  shadowColor: '#000',
  shadowOpacity: 0.3,
  shadowOffset: { width: 0, height: 3 },
  shadowRadius: 4,
  elevation: 5,
},

cameraButton: {
  position: 'absolute',
  bottom: 30,
  right: 30,
  width: 70,
  height: 70,
  borderRadius: 35,
  backgroundColor: '#000',
  justifyContent: 'center',
  alignItems: 'center',
  shadowColor: '#000',
  shadowOpacity: 0.3,
  shadowOffset: { width: 0, height: 3 },
  shadowRadius: 4,
  elevation: 5,
},
routeList:{
  position: 'absolute',
  bottom:200, //adjust to list above other buttons
  left: 0,
  right: 0,
  paddingHorizontal: 10,
},
routeItem: {
      backgroundColor: 'white',
      padding: 10,
      borderRadius: 10,
      marginHorizontal: 5,
      width: 250, // Fixed width for each route item
    },
  selectedRouteItem: {
      borderWidth: 2,
      borderColor: 'blue', // Highlight color for the selected route
    },
    routeSummary: {
      fontWeight: 'bold',
    },
    recommendedText: {
      color: 'green',
      fontWeight: 'bold',
   },
});