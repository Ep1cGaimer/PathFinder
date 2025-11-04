import React, { useEffect, useState, useRef } from 'react';
import { StyleSheet, Alert, Modal, View, Text, TouchableOpacity, FlatList, Image, Dimensions } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE, Polyline, Circle } from 'react-native-maps';
import * as Location from 'expo-location';
import polyline from '@mapbox/polyline'
export default function CustomMapView({ routes,selectedRoute, goToCurrentLocation }) {
  const [location, setLocation] = useState(null);
  const [points, setPoints] = useState([]);
  const [center, setCenter] = useState({ latitude: 0.0, longitude: 0.0 });
  const [routeCoords, setRouteCoords] = useState([]);
  const mapRef = useRef(null);

  const [posts, setPosts] = useState(null);

  const [selectedPoint, setSelectedPoint] = useState(null);
  const [isModalVisible, setModalVisible] = useState(false);

  const API_BASE_URL = 'http://10.72.90.24:8000';
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

  useEffect(() =>{
    if(selectedRoute && mapRef.current){
      const coords = polyline.decode(selectedRoute.overview_polyline).map(([lat,lng])=>({
        latitude: lat,
        longitude: lng,
      }));
      mapRef.current.fitToCoordinates(coords,{
        edgePadding: {top: 50, right: 50, bottom: 250, left: 50},
        animated: true,
      });
    }
  },[selectedRoute]);

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
    <View style={{flex:1}}>
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

        {routes.map((route,index) =>{
        const isSelected = route.overview_polyline === selectedRoute?.overview_polyline;
        const coords = polyline.decode(route.overview_polyline).map(([lat,lng])=>({
          latitude: lat,
          longitude: lng,
        }));
        return(
          <Polyline
            key={index}
            coordinates={coords}
            strokeColor={isSelected ? 'blue': 'gray'}
            strokeWidth={isSelected ? 6:3}
            zIndex={isSelected ? 1 : 0}
          />
        );
      })}
      
        {/* ✅ Points */}
        {points.map((point) => {
          let color = '';

          if (point.overall_score >= 90) color = 'red';
          else if (point.overall_score >= 75) color = 'orange';
          else if (point.overall_score >= 25) color = 'blue';
          else color = 'green';

          // if (color === 'green') console.log("Green: "+point.overall_score+point.location_id)
          return (
            // <Circle
            //   key={point.location_id}
            //   center={{ latitude: point.lat, longitude: point.long }}
            //   radius={8} // in meters — scales with zoom automatically
            //   strokeColor={color}
            //   fillColor={color + '55'} // semi-transparent fill
            //   onPress={() => {
            //     console.log("Clicked!");
            //     setSelectedPoint(point);
            //     setModalVisible(true);
            //   }}
            // />
            <Marker
              key={point.location_id}
              coordinate={{ latitude: point.lat, longitude: point.long }}
              onPress={async () => {
                try {
                  const res = await fetch(`${API_BASE_URL}/getLocationDetails/${point.location_id}`);
                  if (!res.ok) {
                    Alert.alert("Error", "Failed to fetch location details");
                    return;
                  }
                  const data = await res.json();
                  // console.log(data);
                  const pointData = {
                    ...data,
                    lat: point.lat,
                    long: point.long
                  }
                  setSelectedPoint(pointData);
                  setModalVisible(true);
                } catch (err) {
                  console.error("Error fetching details:", err);
                }
              }}
            >
              <View
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 6,
                  backgroundColor: color,
                  borderWidth: 1.5,
                  borderColor: "#fff",
                }}
              />
            </Marker>

          );
        })}

        
      </MapView>
      <Modal
        visible={isModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <View style={styles.header}>
              <Text style={styles.locationText}>
                📍 {selectedPoint?.lat.toFixed(4)}, {selectedPoint?.long.toFixed(4)}
              </Text>
              <TouchableOpacity onPress={() => setModalVisible(false)}>
                <Text style={styles.closeText}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.overallRating}>
              ⭐ Overall: {selectedPoint?.overall_score?.toFixed(1) ?? "—"}
            </Text>

            <View style={{ marginBottom: 10 }}>
              <Text>🧱 Surface Damage: {selectedPoint?.surface_damage?.toFixed(1) ?? "—"}</Text>
              <Text>🚗 Traffic Safety Risk: {selectedPoint?.traffic_safety_risk?.toFixed(1) ?? "—"}</Text>
              <Text>💺 Ride Discomfort: {selectedPoint?.ride_discomfort?.toFixed(1) ?? "—"}</Text>
              <Text>💧 Waterlogging: {selectedPoint?.waterlogging?.toFixed(1) ?? "—"}</Text>
              <Text>⚠️ Urgency: {selectedPoint?.urgency_for_repair?.toFixed(1) ?? "—"}</Text>
            </View>


            <FlatList
              data={selectedPoint?.posts || []}
              keyExtractor={(item, index) => index.toString()}
              renderItem={({ item }) => {
                
                const imagePaths = Array.from(
                   { length: item.images }, // Use the image count
                   (_, i) => `uploads/${item.images_dir}/${i}` // Construct the path for each image
                 );
                return (
                  <View style={styles.postCard}>
                    <Text style={styles.textDescr}>{item.text_descr}</Text>

                      {item.posted_by && (
                        <Text style={styles.metaText}>
                          👤 Posted by: {item.posted_by}
                        </Text>
                      )}

                      {item.created_at && (
                        <Text style={styles.metaText}>
                          🕒 {new Date(item.created_at).toLocaleString()}
                        </Text>
                      )}

                      <FlatList
                        horizontal
                        data={imagePaths}
                        keyExtractor={(img, index) => index.toString()}
                        renderItem={({ item: img }) => {
                            const imgUrl = `${API_BASE_URL}/${img.replace(/^\/?/, "")}`;
                            // console.log(imgUrl)
                          return <Image source={{ uri: imgUrl }} style={styles.postImage} />;
                        }}
                      />
                  </View>
                )
                        
              }
                        }
                        />
                
            
          </View>
        </View>
      </Modal>

    </View>
    
    
  );
}

const styles = StyleSheet.create({
  modalContainer: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: "rgba(0,0,0,0.5)",
  },
  modalContent: {
    backgroundColor: "#fff",
    borderTopLeftRadius: 25,
    borderTopRightRadius: 25,
    padding: 20,
    height: Dimensions.get("window").height * 0.5,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  locationText: {
    fontWeight: "600",
    fontSize: 16,
  },
  closeText: {
    fontSize: 20,
    color: "#555",
  },
  overallRating: {
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 15,
  },
  postCard: {
    marginBottom: 15,
  },
  textDescr: {
    color: "#222",
    marginBottom: 5,
  },
  postImage: {
    width: 120,
    height: 120,
    borderRadius: 10,
    marginRight: 10,
  },
  metaText: {
    color: "#666",
    fontSize: 12,
    marginBottom: 3,
  },
  map: { flex: 1 },
});
