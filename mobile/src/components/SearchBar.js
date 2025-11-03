import React, { useState } from 'react';
import {View, TextInput, TouchableOpacity, Text, StyleSheet,FlatList} from 'react-native';

export default function SearchBar({origin,onOriginChange,destination,onDestinationChange,onGetRoute}){
    const [originSuggestions, setOriginSuggestions] = useState([]);
    const [destinationSuggestions, setDestinationSuggestions] = useState([]);
    const API_BASE_URL = 'http://10.0.2.2:8000';
    const fetchSuggestions = async (text,field) =>{
        if(text.length < 3){
            field == 'origin' ? setOriginSuggestions([]) : setDestinationSuggestions([]);
            return;
        }
        try{
            const response = await fetch(`${API_BASE_URL}/api/autocomplete?input_text=${encodeURIComponent(text)}`);
            const data = await response.json();
            if(data.predictions){
                const suggestions = data.predictions.map(p => ({id:p.place_id,description:p.description}));
                field == 'origin' ? setOriginSuggestions(suggestions) : setDestinationSuggestions(suggestions);
            }
        }catch(error){
            console.error("Error fetching suggestions: ",error);
        }
    };
    return(
        <View style={styles.searchContainer}>
            <TextInput
                style={styles.input}
                placeholder="From"
                value={origin}
                onChangeText={(text) =>{
                    onOriginChange(text);
                    fetchSuggestions(text,'origin');
                }}
            />
            {originSuggestions.length > 0 &&(
                <FlatList
                data={originSuggestions}
                keyExtractor={(item) => item.id}
                renderItem={({item})=>(
                    <TouchableOpacity
                    style={styles.suggestionItem}
                    onPress={()=>{
                        onOriginChange(item.description);
                        setOriginSuggestions([]);
                    }}
                    >
                    <Text>{item.description}</Text>
                    </TouchableOpacity>
                )}
                />
            )}
            <TextInput
                style={styles.input}
                placeholder="To"
                value={destination}
                onChangeText={(text) => {
                    onDestinationChange(text);
                    fetchSuggestions(text,'destination');
                }}
            />
            {destinationSuggestions.length > 0 &&(
                <FlatList
                data={destinationSuggestions}
                keyExtractor={(item) => item.id}
                renderItem={({item})=>(
                    <TouchableOpacity
                    style={styles.suggestionItem}
                    onPress={()=>{
                        onDestinationChange(item.description);
                        setDestinationSuggestions([]);
                    }}
                    >
                    <Text>{item.description}</Text>
                    </TouchableOpacity>
                )}
                />
            )}
            <TouchableOpacity style={styles.button} onPress={onGetRoute}>
                <Text style={styles.buttonText}>Get Route</Text>
            </TouchableOpacity>
        </View>
    );
}

 const styles = StyleSheet.create({
      searchContainer: {
        padding: 10,
        backgroundColor: '#fff',
      },
      input: {
        height: 40,
        borderColor: 'gray',
        borderWidth: 1,
        marginBottom: 10,
        paddingHorizontal: 10,
       borderRadius: 5,
      },
      button: {
        backgroundColor: '#007BFF',
        padding: 10,
        borderRadius: 5,
        alignItems: 'center',
      },
      buttonText: {
        color: 'white',
        fontWeight: 'bold',
    },
    suggestionItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    },
 });
