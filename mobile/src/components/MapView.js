import React, { useEffect, useState, useRef } from 'react';
import { StyleSheet, Alert } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE, Polyline, Circle } from 'react-native-maps';
import * as Location from 'expo-location';

export default function CustomMapView({ routeRequest, goToCurrentLocation }) {
  const [location, setLocation] = useState(null);
  const [points, setPoints] = useState([]);
  const [center, setCenter] = useState({ latitude: 0.0, longitude: 0.0 });
  const [routeCoords, setRouteCoords] = useState([]);
  const mapRef = useRef(null);

  const API_BASE_URL = 'http://10.181.237.24:8000';
  // const FIXED_CENTER = { latitude: 0.0, longitude: 0.0 };

  // ✅ Get current location
  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied', 'Enable location permissions to continue.');
        return;
      }
      const loc = await Location.getCurrentPositionAsync({});
      setLocation(loc);
      setCenter({ latitude: loc.coords.latitude, longitude: loc.coords.longitude });
    })();
  }, []);

  // ✅ Fetch points (with lat/long mapping)
  useEffect(() => {
    if (center.latitude === 0.0 && center.longitude === 0.0) return;
    fetch(`${API_BASE_URL}/getNearbyScores?lat=${center.latitude}&long=${center.longitude}`)
      .then(res => res.json())
      .then(data => {
        if (data.locations && Array.isArray(data.locations)) {
          const validPoints = data.locations.filter(
            p => typeof p.lat === 'number' && typeof p.long === 'number'
          );
          setPoints(validPoints);
          console.log(`✅ Loaded ${validPoints.length} points`);
        }
      })
      .catch(err => console.error('Error fetching points:', err));
  }, [center]);

  // ✅ Fetch route if requested
  // useEffect(() => {
  //   if (routeRequest.origin !== "" && routeRequest.destination !=="") {
  //     fetch(
  //       `${API_BASE_URL}/route?origin=${encodeURIComponent(routeRequest.origin)}&destination=${encodeURIComponent(routeRequest.destination)}`
  //     )
  //       .then(res => res.json())
  //       .then(data => {
  //         console.log(data);
  //         if (data.polyline?.length > 0) {
  //           const coords = data.polyline.map(([lat, lng]) => ({ latitude: lat, longitude: lng }));
  //           setRouteCoords(coords);
  //         } else {
  //           Alert.alert('Error', 'Could not find a route.');
  //         }
  //       })
  //       .catch(err => console.error('Error fetching route:', err));
  //   }
  // }, [routeRequest]);

  useEffect(() => {
    if(routeRequest.origin !== "" && routeRequest.destination !== ""){
      const origin = routeRequest.origin;
      const destination = routeRequest.destination;
      fetch(`${API_BASE_URL}/route?origin=${encodeURIComponent(origin)}&destination=${
      encodeURIComponent(destination)}`)
      .then(res => {
        console.log(res)
        return res.json()
    })
      .then(data => {
        console.log(data)
        if( data.polyline && data.polyline.length > 0){
          const coords = data.polyline.map(([lat,lng]) => ({
            latitude: lat,
            longitude: lng,
          }));
          setRouteCoords(coords);
        }
        else{
          Alert.alert('Error', 'Could not find a route.');
          setRouteCoords([]);
        }
      })
      .catch(err => {
        console.error("Error fetching route: ",err);
        Alert.alert('Error', 'An error occured while fetching the route.');
      });

    }
  },[routeRequest]);

  const defaultRegion = {
    latitude: 0.0,
    longitude: 0.0,
    latitudeDelta: 0.02,
    longitudeDelta: 0.02,
  };
  useEffect(() =>{
    if (routeCoords.length > 0 && mapRef.current){
      mapRef.current.fitToCoordinates(routeCoords,{
        edgePadding: { top: 50, right: 50, bottom: 50, left: 50 },
        animated: true,
      });
    }
  },[routeCoords]);

  useEffect(() => {
    if (goToCurrentLocation && location && mapRef.current) {
      const { latitude, longitude } = location.coords;
      mapRef.current.animateToRegion(
        {
          latitude,
          longitude,
          latitudeDelta: 0.02,
          longitudeDelta: 0.02,
        },
        1000 // smooth animation duration (1 second)
      );
    }
  }, [goToCurrentLocation]);

  return (
    <MapView
      ref={mapRef}
      style={styles.map}
      provider={PROVIDER_GOOGLE}
      initialRegion={defaultRegion}
      showsUserLocation={true}
      showsMyLocationButton={false}
      onRegionChangeComplete={(region) => setCenter({
        latitude: region.latitude,
        longitude: region.longitude
      })}
    >
      {/* ✅ User Marker */}
      {location?.coords && (
        <Marker
          coordinate={{
            latitude: location.coords.latitude,
            longitude: location.coords.longitude,
          }}
          title="You"
          pinColor="orange"
        />
      )}

      {/* ✅ Route */}
      {routeCoords.length > 0 && (
        <Polyline coordinates={routeCoords} strokeColor="blue" strokeWidth={4} />
      )}

      {/* ✅ Points */}
      {points.map((point) => {
        let color = 'green';
        if (point.overall_score >= 90) color = 'red';
        else if (point.overall_score >= 75) color = 'orange';
        else if (point.overall_score >= 25) color = 'blue';

        return (
          <Circle
            key={point.location_id}
            center={{ latitude: point.lat, longitude: point.long }}
            radius={8} // in meters — scales with zoom automatically
            strokeColor={color}
            fillColor={color + '55'} // semi-transparent fill
          />
        );
      })}
    </MapView>
  );
}

const styles = StyleSheet.create({
  map: { flex: 1 },
});
