import httpx
import os
import uuid
import requests
import aiofiles
from dotenv import load_dotenv
import polyline
from backend_vision import analyze_damage, compute_quality_score
load_dotenv() 

API_KEY = os.getenv("GOOGLE_API_KEY")
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
GOOGLE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

def get_analyzed_routes(start:str , end:str):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start}&destination={end}&key={API_KEY}&alternatives=true"
    response = requests.get(url)
    if response.status_code != 200:
        return{"error": "Failed to fetch routes from Google API."}
    
    data = response.json()
    print(data)
    google_routes = data.get('routes',[])
    if not google_routes:
        return {"error": "No routes found."}
    google_routes = google_routes[:3]
    
    analyzed_routes = [_analyze_single_route(route) for route in google_routes]
    for route in analyzed_routes:
        route['pathfinder_score'] = _calculate_final_score(route,analyzed_routes)
    
    sorted_routes = sorted(analyzed_routes, key=lambda r:r['pathfinder_score'],reverse=True)

    if sorted_routes:
        sorted_routes[0]['is_recommended'] = True
    return sorted_routes

def _analyze_single_route(route: dict) -> dict:
    leg = route['legs'][0]
    analyzed_route = {
        'summary' : route['summary'],
        'overview_polyline' : route['overview_polyline']['points'],
        'distance_meters' : leg['distance']['value'],
        'duration_seconds' : leg['duration']['value'],
        'road_quality_score' : 100.0,
        'is_recommended' : False
    }

    coordinates = polyline.decode(analyzed_route['overview_polyline'])
    sample_points = coordinates[::10]

    all_detections = []
    temp_dir = "temp_images"
    os.makedirs(temp_dir,exist_ok=True)

    for lat,lng in sample_points:
        street_view_url = f"https://maps.googleapis.com/maps/api/streetview?size=400x400&location={lat},{lng}&key={API_KEY}"
        image_response = requests.get(street_view_url)

        if image_response.status_code == 200:
            temp_image_path = os.path.join(temp_dir,f"{uuid.uuid4()}.jpg")
            with open(temp_image_path,'wb') as f:
                f.write(image_response.content)
            detections = analyze_damage(temp_image_path)
            if detections:
                all_detections.extend(detections)
            os.remove(temp_image_path)

    if all_detections:
        damage_score = compute_quality_score(all_detections)
        analyzed_route['road_quality_score'] = 100 - damage_score
    if not os.listdir(temp_dir):
        os.rmdir(temp_dir)
    return analyzed_route

def _calculate_final_score(route:dict, all_routes:list) -> float:
    max_dist = max(r['distance_meters'] for r in all_routes)
    min_dist = min(r['distance_meters'] for r in all_routes)
    max_time = max(r['duration_seconds'] for r in all_routes)
    min_time = min(r['duration_seconds'] for r in all_routes)
    max_qual = 100
    min_qual = 0
    norm_dist = 1 - ((route['distance_meters'] - min_dist) / (max_dist - min_dist)) if (max_dist - min_dist) > 0 else 1
    norm_time = 1 - ((route['duration_seconds'] - min_time) / (max_time - min_time)) if (max_time - min_time) > 0 else 1
    norm_qual = (route['road_quality_score'] - min_qual) / (max_qual - min_qual) if (max_qual - min_qual) > 0 else 0

    w_dist = 0.15
    w_time = 0.35
    w_qual = 0.50

    final_score = (w_dist * norm_dist) + (w_time * norm_time) + (w_qual * norm_qual)
    return round(final_score*100,2)

async def geocode_address(address: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(GEOCODE_URL,params={"address":address,"key":API_KEY})
        data = response.json()
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return location["lat"],location["lng"]
        else:
            return None,None

async def get_route(origin: str, destination: str):
    o_lat, o_lng = await geocode_address(origin)
    d_lat, d_lng = await geocode_address(destination)
    #will use the trafic data and live time returned later.
    if not o_lat or not d_lat:
        return []
    body = {
        "origin": {"location": {"latLng": {"latitude": float(o_lat), "longitude": float(o_lng)}}},
        "destination": {"location": {"latLng": {"latitude": float(d_lat), "longitude": float(d_lng)}}},
        "travelMode": "DRIVE"
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "routes.polyline.encodedPolyline"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_URL,headers=headers,json=body)
        data = response.json()
    if "routes" not in data:
        return []
    encoded_polyline = data["routes"][0]["polyline"]["encodedPolyline"]

    # Decode Google’s encoded polyline to [lat, lng]
    # print(polyline.decode(encoded_polyline))
    return polyline.decode(encoded_polyline)