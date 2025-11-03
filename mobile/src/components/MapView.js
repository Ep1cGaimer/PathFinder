import React, { useEffect, useState } from 'react';
import { StyleSheet, Alert} from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE,Polyline } from 'react-native-maps';
import * as Location from 'expo-location'

export default function CustomMapView() {
  const [location,setLocation] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [center, setCenter] = useState(null);
  const [destination, setDestination] = useState(null);
  const [routeCoords, setRouteCoords] = useState([]);
  const [points, setPoints] = useState([]);
  const API_BASE_URL ='http://10.0.2.2:8000';

  useEffect(() => {
    (async() => {
      let { status } = await Location.requestForegroundPermissionsAsync();
      if(status !== 'granted'){
        setErrorMsg('Provide access to location premission to continue');
        Alert.alert('Location Permission', 'Permission to access location was denied');
        return;
      }
      let location = await Location.getCurrentPositionAsync({});
      setLocation(location);
    })();
  },[]);

  useEffect(() => {
    let newPoints = [];
    fetch(`${API_BASE_URL}/getNearbyScores?lat=${center.latitude}&long=${center.longitude}`)
    .then(res => res.json())
    .then(data => {
      locations = data.locations;
      for (let index = 0 ; index < locations.length; index++) {
        newPoints.push(locations[index]);
      }        
    })
    setPoints(newPoints)
  }, [center])

  useEffect(() => {
    if(destination && location){
    const origin = `${location.coords.latitude},${location.coords.longitude}`;
    const dest = `${destination.latitude},${destination.longitude}`;

    fetch(`${API_BASE_URL}/route?origin=${origin}&destination=${dest}`)
    .then(res => res.json())
    .then(data =>{
      const coords = data.polyline.map(([lat,lng]) => ({
        latitude:lat,
        longitude:lng
      }));
      setRouteCoords(coords);
    })
    .catch(err => {
      console.error("Error fetching route: ",err);
    });
    }
  },[destination,location]);


  const defaultRegion = {
    latitude: 40.7128,
    longitude: -74.0060,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  };

  
  //Accurate Location, but has some viewing issues and performance issues, disabled temporarily
  //test comment


  // Location.watchPositionAsync(
  //   {
  //     accuracy:Location.Accuracy.High,
  //     timeInterval:1000,
  //     distanceInterval:1,
  //   },
  //   (location) =>{
  //     setLocation(location);
  //   }
  // );
  const mapRegion = location ? {
    latitude: location.coords.latitude,
    longitude: location.coords.longitude,
    latitudeDelta: 0.02,
    longitudeDelta: 0.02,
  }: defaultRegion;
  return (
    <MapView
      style={styles.map}
      provider={PROVIDER_GOOGLE}
      region={mapRegion}
      showsUserLocation={true}
      showsMyLocationButton={true}
      onRegionChangeComplete={(region) =>
        setCenter({
          latitude: region.latitude,
          longitude: region.longitude
        })
      }
      onLongPress={(event) => {
        const { latitude, longitude } = event.nativeEvent.coordinate;
        setDestination({ latitude, longitude });
      }}
    >
      {location && (
        <Marker
          coordinate={{ latitude: location.coords.latitude, longitude: location.coords.longitude }}
          title="Your Location"
          description='IIITA'
          pinColor='orange'
        />
      )}
      {destination && (
        <Marker
          coordinate={destination}
          title="Destination"
          pinColor="green"
        />
      )}
      {routeCoords.length > 0 && (
        <Polyline
          coordinates={routeCoords}
          strokeColor="blue"
          strokeWidth={4}
        />
      )}     
      {points.length > 0 && (
        points.map((point) => {
            color = ""
            if (point.overall_score >= 90) color = "red"
            else if (point.overall_score >= 75) color = "orange"
            else if (point.overall_score >= 25) color = "blue"
            else color = "green"

            return <Marker
              key={point.location_id}
              coordinate={{latitude: point.latitude, longitude: point.longitude}}
              pinColor={color}
            />
        })
      )}
    </MapView>
  );
}

const styles = StyleSheet.create({
  map: {
    flex: 1,
  },
});
