import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native'
import React, { useState } from 'react'
import { useRouter } from 'expo-router';

const BACKEND_URL = 'http://10.0.2.2:8000';

const RegisterScreen = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleRegister = async () => {
    if (!name || !email || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    if (password.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters long');
      return;
    }

    setLoading(true);
    try {
      const auth = await import('@react-native-firebase/auth');
      const userCredential = await auth.default().createUserWithEmailAndPassword(email, password);
      const user = userCredential.user;
      await user.updateProfile({
        displayName: name,
      });
      const res = await fetch(`${BACKEND_URL}/createUser`,{
        method: "POST",
        headers: {
          "Content-Type":"application/json",
        },
        body: JSON.stringify({
          id: user.uid,
          name: name,
          reputation: 4, //the default reputation will be of 4 (out of 10) 
          created_at: new Date().toISOString(),
        }),
      });
      if(res.ok){
          Alert.alert(
          'Success',
          'Account created successfully!',
          [
            {
              text: 'OK',
              onPress: () => router.replace("/home")
            }
          ]
        );
      }
      else{
          Alert.alert(
          `Failed ${res.status}`,
          'Account not stored in backend',
          [
            {
              text: 'Try Again',
              onPress: () => router.replace("/register")
            }
          ]
        );
      }
      
    } catch (error) {
      let errorMessage = 'An error occurred during registration';

      if (error.code === 'auth/email-already-in-use') {
        errorMessage = 'This email is already registered';
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = 'Invalid email address';
      } else if (error.code === 'auth/weak-password') {
        errorMessage = 'Password is too weak. Use at least 6 characters';
      } else if (error.code === 'auth/network-request-failed') {
        errorMessage = 'Network error. Please check your connection';
      } else if (error.code === 'auth/too-many-requests') {
        errorMessage = 'Too many attempts. Please try again later';
      } else if (error.code === 'auth/operation-not-allowed') {
        errorMessage = 'Registration is currently disabled';
      } else if (error.code === 'auth/internal-error') {
        errorMessage = 'Internal error occurred. Please try again';
      } else if (error.message) {
        errorMessage = error.message;
      }

      Alert.alert('Registration Failed', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.firstpart}>
        <Text style={styles.logoText}>PathFinder</Text>
      </View>

      <View style={styles.middlepart}>
        <TextInput
          style={styles.input}
          placeholder='Enter Name'
          placeholderTextColor={"black"}
          value={name}
          onChangeText={setName}
          editable={!loading}
        />

        <TextInput
          style={styles.input}
          placeholder='Enter Email ID'
          placeholderTextColor={"black"}
          keyboardType='email-address'
          value={email}
          onChangeText={setEmail}
          autoCapitalize='none'
          editable={!loading}
        />

        <TextInput
          style={styles.input}
          placeholder='Set Password'
          placeholderTextColor={"black"}
          secureTextEntry={true}
          value={password}
          onChangeText={setPassword}
          editable={!loading}
        />

        <TextInput
          style={[
            styles.input,
            confirmPassword && password !== confirmPassword && styles.inputError
          ]}
          placeholder='Confirm Password'
          placeholderTextColor={"black"}
          secureTextEntry={true}
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          editable={!loading}
        />

        {confirmPassword && password !== confirmPassword && (
          <Text style={styles.errorText}>Passwords do not match</Text>
        )}

        <TouchableOpacity
          style={[styles.registerButton, loading && styles.registerButtonDisabled]}
          onPress={handleRegister}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.registerButtonText}>Register</Text>
          )}
        </TouchableOpacity>

        <View style={styles.existingUserContainer}>
          <Text style={styles.existingUser}>Already have an account? </Text>
          <TouchableOpacity onPress={() => router.push("/login")} disabled={loading}>
            <Text style={styles.login}>Login</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.lastpart}>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  container:{
    flex: 1,
    backgroundColor: '#fff',
  },
  firstpart:{
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoText:{
    fontSize: 45,
    fontWeight: 'bold',
    color: '#000',
  },
  middlepart:{
    flex: 2,
    justifyContent: 'center',
    alignItems: 'center',
  },
  lastpart:{
    flex: 1,
  },
  input: {
    width: '80%',
    height: 50,
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    marginBottom: 15,
    fontSize: 16,
    color:'black',
  },
  registerButton: {
    width:'80%',
    height:50,
    backgroundColor:'black',
    borderRadius:8,
    justifyContent:'center',
    alignItems:'center',
    marginTop:15,
    shadowColor:'#000',
    shadowOffset:{ width: 0, height: 2 },
    shadowOpacity:0.2,
    shadowRadius:2,
    elevation:3,
  },
  registerButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  existingUserContainer: {
    flexDirection: 'row',
    marginTop: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  existingUser: {
    fontSize: 14,
    color: 'black',
  },
  login: {
    textDecorationLine: 'underline',
    fontWeight: 'bold',
    color: 'black',
  },
  inputError: {
    borderColor: 'red',
    borderWidth: 2,
  },
  errorText: {
    color: 'red',
    fontSize: 12,
    width: '80%',
    marginTop: -10,
    marginBottom: 5,
  },
  registerButtonDisabled: {
    opacity: 0.6,
  },
})

export default RegisterScreen;
