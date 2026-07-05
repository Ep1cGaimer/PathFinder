import math

from sqlalchemy import delete

from .database import SessionLocal
from .models import ReportStatus, RoadAssessment, RoadReport, User
from .services.routing import STORE_SEGMENTS_SQL, _route_pieces

DEMO_ROUTE_POLYLINE = "ipenAgwqxMcCmCyDsDYZmB~B}@|@_@b@IHSTe@g@{@u@g@g@u@s@c@c@WUUUiBcBY[CACCQSSQSOu@k@sAcAeAw@IGKKSYcBwBMSc@m@EGKOAACCEGPQ`@Ev@AL?f@?|@Ar@?FAR?PAJ@\\Bb@DVDPBr@EHAVAD?JARCFA\\IJCDC@ALKPi@f@uBH]L_@Tu@nC_M|AyG@CBOFOBOr@kDR{@d@qBf@{B^cBBIXsAj@aCBMDK@IFUj@cCFY@GBKJe@j@gCDUFOFY@C|@aE~A}G`@gBbAkE^cBz@qD@GBMDOVFH@tAZd@Lh@Jh@Lv@PF@LD@GXoBZ_CVgBBQNgAHi@Jo@Fg@BK@E@KBQDSFc@F_@DYBSRmAFe@Fk@F_@Dk@By@AW?KAE?IAQAOMk@E]?WBM@KDYCYAQGu@E]CQKo@CMI]Ka@Oe@GSAEQg@_@cA{@gBe@y@Ue@We@Q_@w@yAo@kAs@wAA??AIOYe@MWIO_@e@q@k@{@i@{AeAYQoAg@u@e@g@[KMACUi@g@qAYq@UWa@]WUIGG]C[@uBBe@F{@Bu@By@DaAF{ADy@JkC@Y@_@@o@?KA[GwIG{FAgB?M?O?K?GAK?SAWAqACoA?QAw@?I?KAmA?EAyA?C?KA{@?MC}ACoA?S?A?Q?SNA?RK@"


def seed() -> None:
    pieces = _route_pieces(DEMO_ROUTE_POLYLINE)
    with SessionLocal.begin() as db:
        db.execute(delete(RoadReport).where(RoadReport.is_demo.is_(True)))
        user = db.get(User, "pathfinder-demo")
        if not user:
            user = User(id="pathfinder-demo", name="Pathfinder Demo")
            db.add(user)
            db.flush()

        db.execute(
            STORE_SEGMENTS_SQL,
            {
                "segments": __import__("json").dumps(
                    [
                        {
                            "segment_hash": piece["segment_hash"],
                            "encoded_polyline": piece["encoded_polyline"],
                            "wkt": piece["wkt"],
                        }
                        for piece in pieces
                    ]
                )
            },
        )

        for index, piece in enumerate(pieces):
            first, second = piece["points"]
            latitude = (first[0] + second[0]) / 2
            longitude = (first[1] + second[1]) / 2
            quality = round(62 + 25 * math.sin(index / 13), 1)
            damage = 100 - quality
            report = RoadReport(
                user_id=user.id,
                latitude=latitude,
                longitude=longitude,
                description=f"Synthetic Bengaluru route observation {index + 1}",
                status=ReportStatus.READY,
                is_demo=True,
            )
            report.assessment = RoadAssessment(
                model_version="demo-seed-v2",
                detections=[],
                surface_damage=damage,
                traffic_safety_risk=damage * 0.8,
                ride_discomfort=damage * 0.9,
                waterlogging=damage * 0.2,
                urgency_for_repair=damage,
                road_quality=quality,
                confidence=0.92,
            )
            db.add(report)
    print(f"Seeded {len(pieces)} labeled observations on actual OSRM road geometry")


if __name__ == "__main__":
    seed()