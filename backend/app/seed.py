from sqlalchemy import delete

from .database import SessionLocal
from .models import ReportStatus, RoadAssessment, RoadReport, User

DEMO_REPORTS = [
    (12.9763, 77.5929, 86), (12.9770, 77.5990, 82), (12.9780, 77.6050, 77),
    (12.9791, 77.6110, 45), (12.9798, 77.6170, 38), (12.9801, 77.6230, 42),
    (12.9797, 77.6290, 68), (12.9792, 77.6350, 76), (12.9784, 77.6408, 81),
    (12.9830, 77.6060, 91), (12.9860, 77.6180, 88), (12.9840, 77.6320, 85),
]


def seed() -> None:
    with SessionLocal.begin() as db:
        db.execute(delete(RoadReport).where(RoadReport.is_demo.is_(True)))
        user = db.get(User, "pathfinder-demo")
        if not user:
            user = User(id="pathfinder-demo", name="Pathfinder Demo")
            db.add(user)
        for index, (latitude, longitude, quality) in enumerate(DEMO_REPORTS):
            damage = 100 - quality
            report = RoadReport(
                user_id=user.id, latitude=latitude, longitude=longitude,
                description=f"Synthetic Bengaluru demonstration observation {index + 1}",
                status=ReportStatus.READY, is_demo=True,
            )
            report.assessment = RoadAssessment(
                model_version="demo-seed-v1", detections=[], surface_damage=damage,
                traffic_safety_risk=damage * 0.8, ride_discomfort=damage * 0.9,
                waterlogging=damage * 0.2, urgency_for_repair=damage,
                road_quality=quality, confidence=1.0,
            )
            db.add(report)
    print(f"Seeded {len(DEMO_REPORTS)} clearly labelled demo observations")


if __name__ == "__main__":
    seed()
