import httpx
import os
from dotenv import load_dotenv
import polyline

load_dotenv() 

API_KEY = os.getenv("GOOGLE_API_KEY")
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
GOOGLE_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


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
    return polyline.decode(encoded_polyline)
