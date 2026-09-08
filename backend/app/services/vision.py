import hashlib
import threading
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ..config import get_settings

CLASS_MAP = {1: "D00", 2: "D01", 3: "D10", 4: "D11", 5: "D20", 6: "D40", 7: "D43", 8: "D44"}
SEVERITY = {"D00": 15, "D01": 12, "D10": 20, "D11": 18, "D20": 65, "D40": 100, "D43": 20, "D44": 12}


class VisionModel:
    def __init__(self) -> None:
        self._session: Any = None
        self._graph: Any = None
        self._lock = threading.Lock()
        self.path = Path(get_settings().model_path)
        self.version = self._version()

    def _version(self) -> str:
        if not self.path.exists():
            return "ssd-mobilenet-missing"
        return f"ssd-mobilenet-{hashlib.sha256(self.path.read_bytes()).hexdigest()[:12]}"

    def _load(self) -> None:
        if self._session is not None:
            return
        with self._lock:
            if self._session is not None:
                return
            if not self.path.exists():
                raise RuntimeError(f"Vision model not found: {self.path}")
            import tensorflow as tf
            graph = tf.Graph()
            with graph.as_default():
                definition = tf.compat.v1.GraphDef()
                definition.ParseFromString(self.path.read_bytes())
                tf.import_graph_def(definition, name="")
            self._graph = graph
            self._session = tf.compat.v1.Session(graph=graph)

    def assess(self, image_path: Path) -> dict:
        self._load()
        image = Image.open(image_path).convert("RGB").resize((300, 300))
        array = np.expand_dims(np.asarray(image), axis=0)
        tensors = [self._graph.get_tensor_by_name(name) for name in (
            "detection_boxes:0", "detection_scores:0", "detection_classes:0", "num_detections:0"
        )]
        image_tensor = self._graph.get_tensor_by_name("image_tensor:0")
        _, scores, classes, count = self._session.run(tensors, feed_dict={image_tensor: array})
        detections = [
            {"damage_class": CLASS_MAP[int(classes[0][i])], "confidence": round(float(scores[0][i]), 4)}
            for i in range(int(count[0]))
            if scores[0][i] >= 0.4 and int(classes[0][i]) in CLASS_MAP
        ]
        weighted = [SEVERITY[item["damage_class"]] * item["confidence"] for item in detections]
        if weighted:
            sorted_weights = sorted(weighted, reverse=True)
            primary_damage = sorted_weights[0]
            secondary_damage = sum(w * 0.15 for w in sorted_weights[1:])
            damage = min(100.0, primary_damage + secondary_damage)
        else:
            damage = 0.0
        confidence = max((item["confidence"] for item in detections), default=0.0)
        return {
            "model_version": self.version, "detections": detections,
            "surface_damage": round(damage, 1),
            "traffic_safety_risk": round(min(100, damage * 0.85), 1),
            "ride_discomfort": round(min(100, damage * 0.9), 1),
            "waterlogging": round(min(100, damage * 0.25), 1),
            "urgency_for_repair": round(min(100, damage * 1.05), 1),
            "road_quality": round(100 - damage, 1), "confidence": round(confidence, 4),
        }


vision_model = VisionModel()
