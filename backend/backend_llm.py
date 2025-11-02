import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import List
import backend_vision

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

def sanitize_gemini_output(output: str) -> str:
    return output[8:-3]

def get_scores(images: List[dict], text_descr: str) -> dict:
    arr = []
    for i in range(0, len(images)):
        with open(images[i]['file_location'], "rb") as f:
            b = f.read()
        arr.append(
            types.Part.from_bytes(data=b, mime_type=images[i]['mime_type'])
        )
    arr.append(
        f"""
        You are a road quality assessment expert.  
        Given the following data:
        - Road report description (text)
        - Road image(s)
        - Location coordinates

        Analyze the road condition and give the following scores (0-100) with 100 being the worst possible condition for that category and less score meaning better condition for the category:

        1. Surface Damage Score: Severity of visible damage such as potholes, cracks, or uneven surface.
        2. Traffic Safety Risk Score: How dangerous this road section is for vehicles, pedestrians, and cyclists.
        3. Ride Comfort Score: Smoothness of ride and comfort level for vehicles and passengers.
        4. Waterlogging/Drainage Issue Score: Likelihood or evidence of water accumulation problems.
        5. Urgency for Repair Score: Priority with which authorities should repair this road section.

        The text description is as follows (if not null): 
        {text_descr}

        Return the result as strict JSON in the following format:

        {{
            "surface_damage": int,
            "traffic_safety_risk": int,
            "ride_discomfort": int,
            "waterlogging": int,
            "urgency_for_repair": int
        }}

        If any category cannot be determined from the provided data, give a reasonable estimate based on available clues.

        """
    )

    res = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=arr,
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),

        )
    )

    # print(res.text)
    
    return json.loads(sanitize_gemini_output(res.text))

