from pathlib import Path

from app.services.vision import vision_model


def test_known_damaged_road_detects_alligator_cracking() -> None:
    result = vision_model.assess(Path(__file__).parent / "fixtures" / "damaged_road.jpg")
    assert any(item["damage_class"] == "D20" for item in result["detections"])
    assert result["road_quality"] < 60
    assert result["model_version"].startswith("ssd-mobilenet-")
