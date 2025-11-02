from fastapi import FastAPI, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from directions import get_route
from typing import List
import uuid
import os
import backend_llm
import aiofiles
import asyncio

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

# just the User model with inheriting BaseModel so that we can use User model (in form of this below model) directly as function arguments.
# see line 71.
class RequestUserModel(BaseModel):
    id: str
    name: str
    reputation: str
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
    GOOGLE_ROADS_API_KEY = os.environ['GOOGLE_ROADS_API_KEY'] # set your environment variable in cmd using 'set DB_PASSWORD=roadsAPI123' before running it
except KeyError:
    raise RuntimeError("Required environment variable GOOGLE_ROADS_API_KEY not found on your system. Set it. It is needed to get location_id from latitude/longitude")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

GOOGLE_ROADS_API_KEY = os.getenv("GOOGLE_ROADS_API_KEY", "")

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
        return JSONResponse(content=jsonable_encoder(users), status_code=204)
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

    scores = await asyncio.to_thread(backend_llm.get_scores, images, text_descr)

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
        return JSONResponse(content=jsonable_encoder(locations), status_code=204)
    else:
        return JSONResponse(content=jsonable_encoder(locations), status_code=200)

@app.get("/getNearbyScores")
def get_nearby_scores(lat: str = Query(...), 
                      long: str = Query(...)):
    try:
        float_lat = float(lat)
        float_long = float(long)

        ct = 0
        locations = set()
        locationIds = set()
        for la in np.arange(float_lat-0.005, float_lat+0.005, 0.0005):
            long_delta = 1/(111.32 * math.cos(math.radians(la)))
            long_step = long_delta*0.05
            for lo in np.arange(float_long-long_delta, float_long+long_delta, long_step):
                if ct < 100:
                    locations.add(str(la)+","+str(lo))
                    ct += 1
                else:
                    points = "|".join(locations)
                    url = f"https://roads.googleapis.com/v1/nearestRoads?points={points}&key={GOOGLE_ROADS_API_KEY}"

                    data = requests.get(url=url).json()

                    snappedPoints = data['snappedPoints']
                    for i in range(0, len(snappedPoints)):
                        locationIds.add(snappedPoints[i]['placeId'])
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

        if len(locations) == 0:
            return JSONResponse(content=jsonable_encoder(locations), status_code=204)
        else:
            return JSONResponse(content=jsonable_encoder(locations), status_code=200)     

    except ValueError:
        return JSONResponse(content=jsonable_encoder({"message": "Invalid co-ordinates!"}), status_code=500)

@app.get("/route")
async def route(
    origin: str = Query(...),
    destination: str = Query(...)
):
    points = await get_route(origin, destination)
    return {"polyline": points}
