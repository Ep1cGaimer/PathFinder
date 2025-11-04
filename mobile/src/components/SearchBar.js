import React, { useState } from 'react';
import {View, TextInput, TouchableOpacity, Text, StyleSheet,FlatList} from 'react-native';

export default function SearchBar({origin,onOriginChange,destination,onDestinationChange,onGetRoute}){
    const [originSuggestions, setOriginSuggestions] = useState([]);
    const [destinationSuggestions, setDestinationSuggestions] = useState([]);
    const API_BASE_URL = 'http://10.72.90.24:8000';
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
            <View style={styles.inputWrapper}>
                <TextInput
                    style={styles.input}
                    placeholder="From"
                    placeholderTextColor="#999"
                    value={origin}
                    onChangeText={(text) =>{
                        onOriginChange(text);
                        fetchSuggestions(text,'origin');
                    }}
                />
                {originSuggestions.length > 0 &&(
                    <View style={styles.suggestionsContainer}>
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
                    </View>
                )}
            </View>

            <View style={styles.inputWrapper}>
                <TextInput
                    style={styles.input}
                    placeholder="To"
                    placeholderTextColor="#999"
                    value={destination}
                    onChangeText={(text) => {
                        onDestinationChange(text);
                        fetchSuggestions(text,'destination');
                    }}
                />
                {destinationSuggestions.length > 0 &&(
                    <View style={styles.suggestionsContainer}>
                        <FlatList
                        data={destinationSuggestions}
                        keyExtractor={(item) => item.id}
                        renderItem={({item})=>(
                            <TouchableOpacity
                            style={styles.suggestionItem}
                            onPress={()=>{
                                onDestinationChange(item.description);
                                setDestinationSuggestions([]);
                                onGetRoute(item.description);
                            }}
                            >
                            <Text>{item.description}</Text>
                            </TouchableOpacity>
                        )}
                        />
                    </View>
                )}
            </View>
        </View>
    );
}

 const styles = StyleSheet.create({
      searchContainer: {
        position: 'absolute',
        top: 110,
        left: 12,
        right: 12,
        zIndex: 5,
        backgroundColor: 'transparent',
      },
      inputWrapper: {
        marginBottom: 8,
      },
      input: {
        height: 52,
        backgroundColor: '#fff',
        paddingHorizontal: 16,
        borderRadius: 12,
        fontSize: 15,
        color: '#000',
        shadowColor: '#000',
        shadowOpacity: 0.15,
        shadowOffset: { width: 0, height: 3 },
        shadowRadius: 6,
        elevation: 5,
      },
      suggestionsContainer: {
        backgroundColor: '#fff',
        borderRadius: 12,
        marginTop: 8,
        maxHeight: 200,
        shadowColor: '#000',
        shadowOpacity: 0.15,
        shadowOffset: { width: 0, height: 3 },
        shadowRadius: 6,
        elevation: 5,
      },
      button: {
        backgroundColor: '#000',
        padding: 15,
        borderRadius: 12,
        alignItems: 'center',
        marginTop: 4,
        shadowColor: '#000',
        shadowOpacity: 0.15,
        shadowOffset: { width: 0, height: 2 },
        shadowRadius: 5,
        elevation: 4,
      },
      buttonText: {
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 16,
    },
    suggestionItem: {
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    },
 });