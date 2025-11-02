import tensorflow as tf
import numpy as np
import cv2
import os
from PIL import Image
import pillow_avif
MODEL_PATH = "../trainedModels/ssd_mobilenet_innference_graph.pb"  # Fixed typo in filename
CONFIDENCE_THRESHOLD = 0.4


CLASS_MAP = {
    1: "D00",  # Longitudinal crack (wheel mark part)
    2: "D01",  # Longitudinal crack (construction joint)
    3: "D10",  # Lateral crack (equal interval)
    4: "D11",  # Lateral crack (construction joint)
    5: "D20",  # Alligator crack
    6: "D40",  # Rutting/bump/pothole/separation
    7: "D43",  # Crosswalk blur
    8: "D44"   # White line blur
}

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.compat.v1.GraphDef()
    with tf.compat.v1.gfile.GFile(MODEL_PATH,"rb") as fid:  # Fixed deprecated tf.io.Gfile to tf.compat.v1.gfile.GFile
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name="")
sess = tf.compat.v1.Session(graph=detection_graph)

print("Model loaded successfully")

image_tensor = detection_graph.get_tensor_by_name("image_tensor:0")
boxes_tensor = detection_graph.get_tensor_by_name("detection_boxes:0")
scores_tensor = detection_graph.get_tensor_by_name("detection_scores:0")
classes_tensor = detection_graph.get_tensor_by_name("detection_classes:0")
num_tensor = detection_graph.get_tensor_by_name("num_detections:0")

def analyze_damage(image_path: str):
    try:
        image = Image.open(image_path).convert("RGB")
    except:
        print(f"[ERROR] Could not load image: {e}")
        return None
    image_np_expanded = np.expand_dims(image,axis=0)

    (boxes, scores, classes,num) = sess.run(
        [boxes_tensor,scores_tensor,classes_tensor,num_tensor],
        feed_dict={image_tensor: image_np_expanded}
    )

    detections = []
    for i in range(int(num[0])):
        score = scores[0][i]
        if score < CONFIDENCE_THRESHOLD:
            continue
        class_id = int(classes[0][i])
        detections.append({
            "class": CLASS_MAP.get(class_id,"Unknown"),
            "confidence": float(score)
        })

    return detections


def get_scores_cv(images):

    all_detections = []
    for img in images:
        detections = analyze_damage(img["file_location"])
        all_detections.extend(detections)

    summary = {}

    for d in all_detections:
        summary[d["class"]] = summary.get(d["class"],0) + 1
    
    # START OF CHANGES: Added vision-based scoring for all 5 categories
    surface_damage_score = compute_surface_damage_score(all_detections)
    traffic_safety_score = compute_traffic_safety_score(all_detections)
    ride_discomfort_score = compute_ride_discomfort_score(all_detections)
    # Waterlogging score from text description if available, otherwise default
    waterlogging_score = compute_waterlogging_score(all_detections)
    urgency_score = compute_urgency_score(all_detections)
    # END OF CHANGES
    
    return {
        #comented out as not needed for now.
        # "detections": all_detections,
        # "summary": summary,
        # "total_detections": len(all_detections),
        "surface_damage": surface_damage_score,
        "traffic_safety_risk": traffic_safety_score,
        "ride_discomfort": ride_discomfort_score,
        "waterlogging": waterlogging_score,
        "urgency_for_repair": urgency_score
    }

# START OF CHANGES: Added helper functions to map vision detections to 5 scoring categories
def compute_surface_damage_score(detections):
    """
    Calculate surface damage score based on detected damage types
    Weighted scoring where more severe damage types contribute higher scores
    """
    if len(detections) == 0:
        return 0
    
    # Weights for different damage types
    weights = {
        "D00": 8,   # Longitudinal crack (wheel mark)
        "D01": 8,   # Longitudinal crack (construction joint)
        "D10": 10,  # Lateral crack (equal interval)
        "D11": 10,  # Lateral crack (construction joint)
        "D20": 25,  # Alligator crack (severe)
        "D40": 40,  # Rutting/bump/pothole/separation (most severe)
        "D43": 5,   # Crosswalk blur (minimal surface impact)
        "D44": 5    # White line blur (minimal surface impact)
    }
    
    total_weight = sum(weights.get(d["class"], 5) * d["confidence"] for d in detections)
    # Average weighted score normalized to 0-100 scale
    score = min(100, (total_weight / len(detections)) * 2)  # Multiply by 2 to get to 0-100 scale
    return round(score, 2)

def compute_traffic_safety_score(detections):
    """
    Calculate traffic safety risk based on damage types that affect safety
    """
    if len(detections) == 0:
        return 0
    
    # Safety-critical damage types
    safety_weights = {
        "D40": 50,  # Potholes/bumps are major safety hazards
        "D20": 30,  # Alligator cracks can cause accidents
        "D43": 15,  # Crosswalk blur affects pedestrian safety
        "D44": 10,  # White line blur affects vehicle guidance
        "D00": 5,   # Longitudinal cracks less critical for safety
        "D01": 5,
        "D10": 5,
        "D11": 5
    }
    
    total_weight = sum(safety_weights.get(d["class"], 0) * d["confidence"] for d in detections if d["class"] in safety_weights)
    if len(detections) == 0:
        return 0
    
    score = min(100, total_weight / len(detections))
    return round(score, 2)

def compute_ride_discomfort_score(detections):
    """
    Calculate ride comfort score based on surface irregularities
    """
    if len(detections) == 0:
        return 0
    
    # All surface damages affect ride comfort
    comfort_weights = {
        "D00": 5,   # Longitudinal cracks
        "D01": 5,
        "D10": 8,   # Lateral cracks (more jarring)
        "D11": 8,
        "D20": 20,  # Alligator cracks (very uncomfortable)
        "D40": 45,  # Potholes (extremely uncomfortable)
        "D43": 2,   # Crosswalk blur (minimal comfort impact)
        "D44": 2    # White line blur (minimal comfort impact)
    }
    
    total_weight = sum(comfort_weights.get(d["class"], 2) * d["confidence"] for d in detections)
    score = min(100, (total_weight / len(detections)) * 1.8)  # Scaled to 0-100
    return round(score, 2)


#Change this to use potholes instead of text.
def compute_waterlogging_score(detections):
    if len(detections) == 0:
        return 0
    # All surface damages affect ride comfort
    comfort_weights = {
        "D00": 0,   # Longitudinal cracks
        "D01": 0,
        "D10": 10,   # Lateral cracks (more jarring)
        "D11": 8,
        "D20": 15,  # Alligator cracks (very uncomfortable)
        "D40": 70,  # Potholes (extremely uncomfortable)
        "D43": 0,   # Crosswalk blur (minimal comfort impact)
        "D44": 0    # White line blur (minimal comfort impact)
    }
    
    total_weight = sum(comfort_weights.get(d["class"], 2) * d["confidence"] for d in detections)
    score = min(100, (total_weight / len(detections)) * 1.8)
    return round(score, 2)

def compute_urgency_score(detections):
    """
    Calculate repair urgency based on damage severity and safety impact
    """
    if len(detections) == 0:
        return 0
    
    # Urgency weights (higher for immediate repair needs)
    urgency_weights = {
        "D40": 100, # Potholes need immediate attention
        "D20": 70,  # Alligator cracks indicate structural issues
        "D10": 25,  # Lateral cracks (structural concern)
        "D11": 25,  # Construction joint cracks
        "D00": 15,  # Longitudinal cracks (less urgent)
        "D01": 15,
        "D43": 20,  # Crosswalk blur affects safety
        "D44": 10   # White line blur affects guidance
    }
    
    total_weight = sum(urgency_weights.get(d["class"], 10) * d["confidence"] for d in detections)
    score = min(100, total_weight / len(detections))
    return round(score, 2)
# END OF CHANGES

def compute_quality_score(detections):
    #will change based on whats seems right just a starting point.
    weights = {
        "D00": 10, "D01": 10,
        "D10": 15, "D11": 15,  
        "D20": 30,             
        "D40": 50,             
        "D43": 5, "D44": 5   
    }

    if len(detections) == 0:
        return 0
    
    total_weight = sum(weights.get(d["class"], 10) * d["confidence"] for d in detections)
    score = min(100, total_weight / len(detections))
    return round(score, 2)

