import React, { useRef , useState} from 'react';
import { View, StyleSheet, TouchableOpacity, Text, Alert, TextInput } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import * as Location from 'expo-location';

const BACKEND_URL = 'http://10.0.2.2:8000';

export default function CameraScreen() {
    const router = useRouter();
    const [permission, requestPermission] = useCameraPermissions();
    const [locationPermission,setLocationPermission] = useState(null);
    const [currentLocation,setCurrentLocation] = useState(null);
    const cameraRef = useRef(null);
    const [step, setStep] = useState(0); 
    const [desc, setDesc] = useState("");
    const [photo, setPhoto] = useState(null);

   

  React.useEffect(() => {
    (async () => {
      let {status} = await Location.requestForegroundPermissionsAsync();
      setLocationPermission(status);
    })();
  }, []);  
  
   //to fix the error when you open immediately
    if (!permission || locationPermission === null) {
        return <View style={styles.container}><Text>Loading permissions...</Text></View>;
    }

    if (!permission.granted || locationPermission !== 'granted') {
        return (
            <View style={styles.container}>
                <Text style={styles.header}>Permissions requires</Text>
                {!permission.granted &&(
                  <TouchableOpacity onPress={requestPermission} style={styles.permissionButton}>
                    <Text style={styles.submitButtonText}>Grant camera permission</Text>
                  </TouchableOpacity>
                )}
                {locationPermission !== 'granted' && (
                <TouchableOpacity onPress={() => Location.requestForegroundPermissionsAsync().then(({ status }) => setLocationPermission(status))} style={styles.permissionButton}>
                    <Text style={styles.submitButtonText}>Grant Location Permission</Text>
                </TouchableOpacity>
                )}
            </View>
        );
    }



    const handleTextChange = (text) => {
        setDesc(text);
    };

    const takePicture = async () => {
        if (cameraRef.current && locationPermission === 'granted') {
            try {
                const location = await Location.getCurrentPositionAsync({accuracy: Location.Accuracy.High});
                setCurrentLocation({
                  latitude: location.coords.latitude,
                  longitude: location.coords.longitude
                })
                const capturedPhoto = await cameraRef.current.takePictureAsync();
                setPhoto(capturedPhoto);
                setStep(1);
            } catch (error) {
                console.error("Error taking picture or getting location: ", error);
                Alert.alert("Error", "Could not capture image or location.");
            }
        } else {
            Alert.alert("Permissions required", "Camera and location permissions are required to use this feature.");
        }
    };

    const addDescription = () => {
        sendDataToBackend(photo);
    };

    const sendDataToBackend = (capturedPhoto) => {
        const formData = new FormData();

        formData.append('images_bytes', {
            uri: capturedPhoto.uri,
            name: 'photo.jpg',
            type: 'image/jpeg',
        });

        // The user-entered description is sent here
        formData.append("text_descr", desc);

        //Add the location if it exists
        if (currentLocation) {
          formData.append("latitude", currentLocation.latitude.toString());
          formData.append("longitude", currentLocation.longitude.toString());
        }

        fetch(`${BACKEND_URL}/addPost`, {
            method: 'POST',
            body: formData,
            headers: {
                "Content-Type": "multipart/form-data",
            },
        })
            .then(data => data.json())
            .then(data => {
                console.log('Success:', data);
                Alert.alert("Upload Successful", "Image sent to backend.");
                router.back();
            })
            .catch(error => {
                console.error('Error uploading data:', error);
                Alert.alert("Upload Failed", "Could not send image to the server.");
            });
    };

    const renderCamera = () => {
        return (
            <View style={styles.container}>
                <CameraView style={styles.camera} ref={cameraRef} facing="back" />
                <View style={styles.buttonContainer}>
                    <TouchableOpacity style={styles.button} onPress={takePicture}>
                        <View style={styles.buttonInner}></View>
                    </TouchableOpacity>
                </View>
            </View>
        );
    }

    const renderDescriptionInput = () => {
        return(
            <View style={styles.descriptionContainer}>
                <Text style={styles.header}>Enter a description for the photo provided (optional)</Text>
                <TextInput
                    style={styles.textInput}
                    value={desc}
                    onChangeText={handleTextChange}
                    placeholder="Enter a short description explaining your photo"
                    multiline={true}
                    numberOfLines={4}
                />
                <TouchableOpacity style={styles.submitButton} onPress={addDescription}>
                    <Text style={styles.submitButtonText}>Submit Photo and Description</Text>
                </TouchableOpacity>
            </View>
        );
    }
    //renders two screens one for the camera and the second one for the description
    return (
        <View style={styles.container}>
            {step === 0 && renderCamera()}
            {step === 1 && renderDescriptionInput()} 
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center' //this is needed as react native components use flexbox by defult (in case of any further issues)
    },
    camera: {
        ...StyleSheet.absoluteFillObject,
    },
    buttonContainer: {
        position: 'absolute',
        bottom: 30,
        left: 0,
        right: 0,
        paddingBottom: 50,
        paddingTop: 20,
        backgroundColor: 'transparent',
        alignItems: 'center',
    },
    button: {
        width: 70,
        height: 70,
        borderRadius: 35,
        borderWidth: 4,
        borderColor: 'white',
        justifyContent: 'center',
        alignItems: 'center',
    },
    buttonInner: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: 'white',
    },
    descriptionContainer: {
        flex: 1,
        padding: 20,
        backgroundColor: '#fff',
    },
    header: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 20,
        marginTop: 50,
    },
    textInput: {
        height: 100,
        borderColor: '#ccc',
        borderWidth: 1,
        borderRadius: 5,
        padding: 10,
        marginBottom: 20,
        textAlignVertical: 'top',
    },
    submitButton: {
        backgroundColor: '#007AFF',
        padding: 15,
        borderRadius: 5,
        alignItems: 'center',
    },
    submitButtonText: {
        color: 'white',
        fontWeight: 'bold',
    },
    permissionButton: {
    backgroundColor: '#FF3B30',
    padding: 15,
    borderRadius: 5,
    marginTop: 10,
    },
    locationText: {
    fontSize: 14,
    color: '#4CAF50',
    marginBottom: 10,
}
});