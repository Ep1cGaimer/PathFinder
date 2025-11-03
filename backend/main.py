from fastapi import FastAPI, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from directions import get_route
from typing import List
import uuid
import os
import backend_llm
import backend_vision
import aiofiles
import asyncio
import httpx
from dotenv import load_dotenv

from dataclasses import dataclass, asdict

import datetime

load_dotenv() 

# we need some math ;)
import numpy as np

# for finding cosines in get_nearby_scores()
import math

# requests library to make api calls to Google Roads API
import requests

# to convert the python datatypes/objects, etc. to json strings 
from fastapi.encoders import jsonable_encoder

# for serving files from the uploads folder
from fastapi.staticfiles import StaticFiles

# BaseModel class when inherited by a class makes that class to be directly usable by an endpoint handler function 
from pydantic import BaseModel 

# importing the database models
from database.models import User, Location

from database import db
PLACES_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# just the User model with inheriting BaseModel so that we can use User model (in form of this below model) directly as function arguments.
# see line 71.
class RequestUserModel(BaseModel):
    id: str
    name: str
    reputation: int  #using integer as a reputation measure for easier calcualtion in the future.
    created_at: str | None = None

class RequestLocationsIDModel(BaseModel):
    location_ids: List[str]

app = FastAPI()
#Add api calling between front end and backend here
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    GOOGLE_ROADS_API_KEY = os.getenv("GOOGLE_API_KEY") #Using .env for consistent results
except KeyError:
    raise RuntimeError("Check project environment variables. Set it. It is needed to get location_id from latitude/longitude")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

GOOGLE_ROADS_API_KEY = os.getenv("GOOGLE_API_KEY", "") #keep naming as google api key for consistnecy


def combine_scores(scores_llm, scores_vision):
    scores = {}
    for key in set(scores_llm.keys()) | set(scores_vision.keys()):
        v1 = scores_llm.get(key, 0)
        v2 = scores_vision.get(key, 0)
        scores[key] = (v1 + v2) / 2

    return scores

# endpoint for creating a new user 
# Example curl:
# curl -X POST "http://127.0.0.1:8000/createUser" \
#      -H "Content-Type: application/json" \
#      -d '{"id": "Sa12", "name": "Sahil Gupta", "reputation": "1000"}'
@app.post("/createUser")
def create_user(user: RequestUserModel):
    newUser = User(id=user.id,
                   name=user.name,
                   reputation=user.reputation)
    
    done = db.createUser(newUser)
    if done:
        return JSONResponse(content=jsonable_encoder({"message": "Successful!"}), status_code=201)
    else:
        return JSONResponse(content=jsonable_encoder({"message": "Error creating new user"}), status_code=500)

# in this endpoint, search the user by paramter
@app.get("/searchUser/{name}")
def search_user(name: str):
    users = db.searchForUser(name)

    if len(users) == 0:
        return JSONResponse(content=jsonable_encoder({"message": "No users found"}), status_code=200)
    else:
        return JSONResponse(content=jsonable_encoder(users), status_code=200)

# endpoint to handle a new post (image + text by the user)
# does llm rating and stores in the database.
# Example curl:
# curl -X POST "http://127.0.0.1:8000/addPost" \
#      -H "Content-Type: multipart/form-data" \
#      -F "text_descr=A very bad road."
#      -F "latitude=SOME_LAT"
#      -F "longitude=SOME_LONG"
#      -F "images_bytes=@/path/to/road1.jpg"
#      -F "images_bytes=@/path/to/road2.jpg"
@app.post('/addPost')
async def add_post(text_descr: str = Form(...), 
                   latitude: str = Form(...),
                   longitude: str = Form(...),
                   images_bytes: List[UploadFile] = File(...)):
    images = []

    images_dir = ""
    # images = []
    if len(images_bytes) == 0 and text_descr == "":
        return JSONResponse(content=jsonable_encoder({"message": "no attached images and text description found!"}), status_code=400)
    if len(images_bytes) != 0:
        uuid_number = uuid.uuid4().hex
        os.makedirs(f"uploads/upload_{uuid_number}", exist_ok=True)
        ct = 0
        for image in images_bytes:
            f = image.file
            images_dir = f"upload_{uuid_number}"
            file_path = f"upload_{uuid_number}/{str(ct)}"

            contents = await image.read()
            
            async with aiofiles.open(f"uploads/{file_path}", "wb") as out_f:
                await out_f.write(contents)

            images.append({
                "file_location": f"uploads/{file_path}",
                "mime_type": image.content_type
            })

            ct += 1

    scores_llm = await asyncio.to_thread(backend_llm.get_scores, images, text_descr)
    scores_vision = await asyncio.to_thread(backend_vision.get_scores_cv,images,text_descr)
    scores = combine_scores(scores_llm,scores_vision)
    # ATTENTION!
    # Google Maps Road API to convert given latitude-longitude to location_id needed here!
    # This part is pending (TODO!!)

    url = f"https://roads.googleapis.com/v1/snapToRoads?path={latitude},{longitude}&key={GOOGLE_ROADS_API_KEY}"
    response = requests.get(url=url)

    data = response.json()
    if len(data['snappedPoints']) != 0:
        location_id = data["snappedPoints"][0]["placeId"]
    
        newLocation = Location(location_id=location_id,
                            images_dir=images_dir,
                            images = ct,
                            text_descr=text_descr,
                            surface_damage=scores['surface_damage'],
                            traffic_safety_risk=scores['traffic_safety_risk'],
                            ride_discomfort=scores['ride_discomfort'],
                            waterlogging=scores['waterlogging'],
                            urgency_for_repair=scores['urgency_for_repair'],
                            posted_by='Sa12')
    
    done = db.addPost(newLocation)

    if done:
        return JSONResponse(content=jsonable_encoder({"message": "Successful!"}), status_code=201)
    else:
        return JSONResponse(content=jsonable_encoder({"message": "Error adding the post"}), status_code=500)

 # get a location (if it exists) from the database   
# Example curl:
# curl -X GET "http://127.0.0.1:8000/getLocation/location_id" 
@app.get("/getLocation/{location_id}")
def get_location(location_id: str):
    location: Location = db.getLocation(location_id)
    exists = location['location_id'] is not None

    if exists:
        return JSONResponse(content=jsonable_encoder(location), status_code=200)
    else:
        return JSONResponse(content=jsonable_encoder({"message": "Location Not Found!"}), status_code=404) 

# get multiple locations at once. 
# intended to be used when locating all the locations from A to B on the map.
# Example curl:
# curl -X GET "http://127.0.0.1:8000/getLocations" \
#      -H "Content-Type: application/json" \
#      -d '{"location_ids": ["loc_id1", "loc_id2", "loc_id3"]}'
@app.get("/getLocations")
def get_locations(locationIDsBody: RequestLocationsIDModel):
    locationIds = locationIDsBody.location_ids

    locations = db.getLocations(locationIds)

    if len(locations) == 0:
        return JSONResponse(content=jsonable_encoder({"message": "No locations found"}), status_code=200)
    else:
        return JSONResponse(content=jsonable_encoder(locations), status_code=200)
    
# get all the roads info thats available in the app-db around a particular location - (lat,long)
# returns the ratings of all the points lying in the square patch around the given point
# Example curl:
# curl -X GET "http://127.0.0.1:8000/getLocations?lat=XYZ&long=ABC
#      -H "Content-type: application/json"
@app.get("/getNearbyScores")
def get_nearby_scores(lat: str = Query(...), 
                      long: str = Query(...)):
    @dataclass
    class NewLocationModel:
        location_id: str 
        lat: float
        long: float
        surface_damage: float
        traffic_safety_risk: float 
        ride_discomfort: float 
        waterlogging: float 
        urgency_for_repair: float 
        created_at: datetime.datetime 

    placeid_loc_mapping = {}
    try:
        float_lat = float(lat)
        float_long = float(long)

        ct = 0
        locations = set()
        locations_to_send = {"locations": []}
        locationIds = set()
        for la in np.arange(float_lat-0.005, float_lat+0.005, 0.0005):
            long_delta = 1/(111.32 * math.cos(math.radians(la)))
            long_step = long_delta*0.05
            for lo in np.arange(float_long-long_delta, float_long+long_delta, long_step):
                if ct < 100:
                    locations.add(f"{la:.6f},{lo:.6f}")
                    ct += 1
                else:
                    points = "|".join(locations)
                    url = f"https://roads.googleapis.com/v1/nearestRoads?points={points}&key={GOOGLE_ROADS_API_KEY}"

                    data = requests.get(url=url).json()
                    # print(data)
                    # data = {}

                    snappedPoints = data.get('snappedPoints', [])
                    for i in range(0, len(snappedPoints)):
                        locationIds.add(snappedPoints[i]['placeId'])
                        placeid_loc_mapping.update({snappedPoints[i]['placeId']: snappedPoints[i]['location']})
                    locations = set()
                    ct = 0
        
        if len(locations) != 0:
            points = "|".join(locations)
            url = f"https://roads.googleapis.com/v1/nearestRoads?points={points}&key={GOOGLE_ROADS_API_KEY}"

            data = requests.get(url=url).json()

            # if snappedPoints not found, return empty array instead
            snappedPoints = data.get('snappedPoints', [])
            for i in range(0, len(snappedPoints)):
                locationIds.add(snappedPoints[i]['placeId'])

            locations = db.getLocations(locationIds)

            for i in range(0, len(locations)):
                sum_scores=float(locations[i]['surface_damage'])+float(locations[i]['traffic_safety_risk'])+float(locations[i]['ride_discomfort'])+float(locations[i]['waterlogging'])+float(locations[i]['urgency_for_repair'])
                newLocation = NewLocationModel(
                    location_id=locations[i]['location_id'],
                    lat=float(placeid_loc_mapping[locations[i]['location_id']]['location']['latitude']),
                    long=float(placeid_loc_mapping[locations[i]['location_id']]['location']['longitude']),
                    surface_damage=float(locations[i]['surface_damage']),
                    traffic_safety_risk=float(locations[i]['traffic_safety_risk']),
                    ride_discomfort=float(locations[i]['ride_discomfort']),
                    waterlogging=float(locations[i]['waterlogging']),
                    urgency_for_repair=float(locations[i]['urgency_for_repair']),
                    created_at=locations[i]['created_at'],
                    overall_score=sum_scores/5
                )

                locations_to_send['locations'].append(asdict(newLocation))

        if len(locations) == 0:
            return JSONResponse(content=jsonable_encoder({"message": "No locations found"}), status_code=200)
        else:
            return JSONResponse(content=jsonable_encoder(locations_to_send), status_code=200)     

    except ValueError:
        return JSONResponse(content=jsonable_encoder({"message": "Invalid co-ordinates!"}), status_code=500)
    
# get all the posts related to a particular point on the road thats there in the app db
# returns a json array of all the posts
# Example curl:
# curl -X GET "http://127.0.0.1:8000/getPosts/location_id
#      -H "Content-type: application/json"
@app.get("/getPosts/{location_id}")
def getPosts(location_id: str):
    posts = db.getPosts(location_id=location_id)

    if len(posts) == 0:
        return JSONResponse(content=jsonable_encoder({"message": "No posts found"}), status_code=200)
    else:
        return JSONResponse(content=jsonable_encoder(posts), status_code=200)

@app.get("/api/autocomplete")
async def api_autocomplete(input_text: str = Query(..., min_length=1)):
    params = {"input": input_text, "key": GOOGLE_ROADS_API_KEY}
    async with httpx.AsyncClient() as client:
        response = await client.get(PLACES_AUTOCOMPLETE_URL, params=params)
    return response.json()

@app.get("/api/place_details")
async def api_place_details(place_id: str = Query(...)):
    params = {"place_id": place_id, "key": GOOGLE_ROADS_API_KEY, "fields": "formatted_address,geometry"}
    async with httpx.AsyncClient() as client:
        response = await client.get(PLACES_DETAILS_URL, params=params)
    return response.json()

@app.get("/route")
async def route(origin: str = Query(...), destination: str = Query(...)):
    try:
        points = await get_route(origin, destination)
        return {"polyline": points}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)