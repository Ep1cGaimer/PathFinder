import hashlib
import json
import math

import polyline
from sqlalchemy import delete, text

from .database import SessionLocal
from .models import ReportStatus, RoadAssessment, RoadReport, User
from .services.routing import STORE_SEGMENTS_SQL

DEMO_ROUTES = [
    ("east", "ipenAgwqxMcCmCyDsDYZmB~B}@|@_@b@IHSTe@g@{@u@g@g@u@s@c@c@WUUUiBcBY[CACCQSSQSOu@k@sAcAeAw@IGKKSYcBwBMSc@m@EGKOAACCEGPQ`@Ev@AL?f@?|@Ar@?FAR?PAJ@\\Bb@DVDPBr@EHAVAD?JARCFA\\IJCDC@ALKPi@f@uBH]L_@Tu@nC_M|AyG@CBOFOBOr@kDR{@d@qBf@{B^cBBIXsAj@aCBMDK@IFUj@cCFY@GBKJe@j@gCDUFOFY@C|@aE~A}G`@gBbAkE^cBz@qD@GBMDOVFH@tAZd@Lh@Jh@Lv@PF@LD@GXoBZ_CVgBBQNgAHi@Jo@Fg@BK@E@KBQDSFc@F_@DYBSRmAFe@Fk@F_@Dk@By@AW?KAE?IAQAOMk@E]?WBM@KDYCYAQGu@E]CQKo@CMI]Ka@Oe@GSAEQg@_@cA{@gBe@y@Ue@We@Q_@w@yAo@kAs@wAA??AIOYe@MWIO_@e@q@k@{@i@{AeAYQoAg@u@e@g@[KMACUi@g@qAYq@UWa@]WUIGG]C[@uBBe@F{@Bu@By@DaAF{ADy@JkC@Y@_@@o@?KA[GwIG{FAgB?M?O?K?GAK?SAWAqACoA?QAw@?I?KAmA?EAyA?C?KA{@?MC}ACoA?S?A?Q?SNAP?LAdBEh@A|@AfAE^AlBCvAC|HIRAP?nJWVA"),
    ("south", "ipenAgwqxMcCmCyDsDYZmB~B}@|@_@b@IHzAxA`GxFDBVRFH\\d@^x@`@|@jAnCFJl@|A@@Xx@HPVr@NZNVb@f@DHBDHT@?FBB@HHDL?LAJf@ThAZxBn@LDn@LV@N@~BOTCTCd@En@ERCNAv@GD?d@ErBMD?TC@?HArAK~AK\\C\\C`@ERAvAKhAKZAfAIh@CHAH?BAJA@?DCLIZc@@S@a@Bo@?[?WHa@JQJIBENGVIPIHCNEBAvAi@h@SxCiAj@WNAj@HPBRDH?HBp@J\\Fr@JnBXh@H^HDEv@u@j@MXA`@@ZF^R\\Zl@j@TR^^h@h@VVNPHHFHJHHH|AjA^ZRNPJDBDBz@j@h@\\f@ZXPB@RLJDz@b@PJLH\\Fl@LrATj@JnARF@H@f@JzDl@z@LB@PBPDj@FlAPjBVLAPGHKDERWdEiFZg@h@sBfBiHLe@n@gCHe@@G?IB]CI?GBOHIHCHA@?H]t@mCFMHWJOJOX[NSTUZ[VYbAeADE@ApAm@t@[j@OTILERKLI\\OPKrAi@~@[f@Sb@Op@[LIVQVUr@o@j@m@pAaBPYf@eABEd@}@Zg@h@i@ZWJGRGfBUpAKZEjBUf@E~BQzBIfIe@PALC^GhB{@bCuAx@i@v@y@NQ^k@d@eATs@FYLi@Js@@Qz@{LRwBBg@HsAFm@NgBBS?EBU@KLcBBW@[Dg@Di@B_@@IBQLq@FW@A@I@GBEFY`@sADOXo@|A{CbB}C@ADINYDEDIDGLHBBFA@?F@j@AJ@B?l@GPAhAEfAIjAe@FARCr@Cz@?\\@zAVZDp@JH@H@XDfC\\b@FRBl@Hr@Jp@HVDVDTB`@aGj@@t@@lA?EjB"),
    ("northwest", "ipenAgwqxMcCmCyDsDYZmB~B}@|@_@b@IHzAxA`GxFDBVRFH\\d@^x@`@|@jAnCFJl@|A@@Xx@HPVr@NZNVb@f@DHBDHT@?FBB@HHDL?LAJGJGDA@KBC?G?GAKLEFKJg@t@e@j@ININm@z@EF]j@uAxBYd@U`@QXm@dA]l@w@rAaBtCu@rAw@lAEFMRU\\MPIN}@hBOf@Kv@Cd@C\\ChAGlAKjCALA\\APA\\ANEpAAVG|BALARCh@Ab@GlBAZAv@Av@?p@?N?D?F@Hg@BIDIFIFK@C?mBFG@I?qBHM@]@WAw@K{BS{BQO?{ADC?q@@I@qAJ{BR[BgAJqFh@UBG?}BTw@Hq@Zg@n@e@r@CDQl@YbAADCHCHU`AIRQVMLGFEDYVSLGD_@PMJ}@FUB{@DmBDgBDI@W?eA@iA@G?G?K?K?]?oBBeA@iA?kCBuA@w@@wA@E?]?E?q@@S?_A@Q?}B@iDBM?kBBA?o@?W@gDBaD@I??H?hAAfAA|AoDBmCD"),
    ("diagonal", "csonA{tjxMTAB?@C?Kv@@\\@h@@Cc@Cq@@iA@MBMPq@V}@V{@XeARq@J]FSPm@VaAV}@XaATy@V_A@eB@c@?K@qAPGfAa@rCcApA]JC\\Id@ONENCf@KnAWhAOnC]hCKL@r@HD?LDVH`@Pz@`@FBh@TJDf@RfAh@jAl@ZNh@d@rAdANJFDVLv@\\|EpBlBgEfByDrDqHfAeBhBuDv@}AbC{Et@_BJSlCqFFMFOACAI@KBIHGLEL?HGVQnDeCpA}@FEj@_@HIRKl@c@DCZSPMPMLINMB?PKFCh@QpAm@@CBAFE\\a@HMh@u@LUXg@Ne@DKHURkAHi@B_AAs@]oEK}AA}@Fy@Lk@fAgCxCsHHODIBGJSFMP]nAiCDI`BiD|@iBpCqFd@{@v@yARa@|@gBTQ\\QXIPEj@MR?v@ArKGrDKP?`CAPARAtAKdBSdBUPGFAtAURC\\GD?NCzC_@\\EhC[nBONALAN?J@DA\\ELAH?XEXCj@IPCx@Kj@E|DYTAx@ILCbAIRAhAI`@ENAdBUTGLEZUn@q@jB{BbByBlCgDNSHMDIRUFGFEFGNKPMBClAuABENODEDEROhEcDJGr@o@~BoBp@u@POTWNWPWDKNc@GA{Bk@k@Ms@QVeA@G`@aBJg@Pu@BKbAkEBGJc@DS@EFU@IDQJUHa@H[DSLe@b@aB@CLc@PAJ@\\Bb@DVDPBr@EHAVAD?JARCFA\\IJCDC@ALKPi@f@uBH]L_@Tu@nC_M|AyG@CBOFOBOr@kDR{@d@qBf@{B^cBBIXsAj@aCBMDK@IFUj@cCFY@GBKJe@j@gCDUFOFY@C|@aE~A}G`@gBbAkE^cBz@qD@GBMDOVFH@tAZd@Lh@Jh@Lv@PF@LD@GXoBZ_CVgBBQNgAHi@Jo@Fg@BK@E@KBQDSFc@F_@DYBSRmAFe@Fk@F_@Dk@By@AW?KAE?IAQAOMk@E]?WBM@KDYCYAQGu@E]CQKo@CMI]Ka@Oe@GSAEQg@_@cA{@gBe@y@Ue@We@Q_@w@yAo@kAs@wAA??AIOYe@MWIO_@e@q@k@{@i@{AeAYQoAg@u@e@g@[KMACUi@g@qAYq@UWa@]WUIGG]C[@uBBe@F{@Bu@By@DaAF{ADy@JkC@Y@_@@o@?KA[GwIG{FAgB?M?O?K?GAK?SAWAqACoA?QAw@?I?KAmA?EAyA?C?KA{@?MC}ACoA?S?A?Q?SNAP?LAdBEh@A|@AfAE^AlBCvAC|HIRAP?nJWVA"),
    ("northsouth", "op|mAu`rxMyAAI~AKlAEr@AD?BIRO?}AAw@Ay@AqDCu@Em@Ay@Ac@AO?c@?k@AmA?yAAiADYD_MZE?e@@qFDsB@ICSIo@g@AG_@_@m@m@q@k@o@q@_@a@IGe@]IIaAg@w@a@m@QGC}@]c@IMDs@TQDg@FWDK?MCMCKEe@]OMOMQOOMs@g@IGsAq@ECEA{AbBe@l@GDMLOJg@b@MJKHMHEBk@Zc@Rg@N}@\\s@XGBy@j@IDODu@Js@Rs@ZmAj@EBGD{@|@ONo@t@o@p@MPUf@o@rBKb@ADI\\@@DDDL@JCHEHIDSPGLGJiAvEkAzEaAnDGTa@h@kB|BiAzAKTKb@ETA@Of@WhAU|@Mj@_@|AIl@E\\?DCNANCZAD??Eb@ADC~@CVARCz@EdAGjAKjAQz@Ql@CFCL?HAPMAGGMOsC_DSOEEIG_BiAmAw@yBkA}Au@EAQKaAc@g@UIE[OKCa@Qe@UMEw@]KEs@Ye@SGCUIAA_C_AOG_@MQIIEsDcBeAa@eA]YKc@Me@OEAMEYIUCW]OQgAaAKK][mBeBa@WI?WAa@?e@Us@k@_Au@UMQEA?OEe@Em@Di@Dc@Ts@ZCBEBWROJs@r@OR{AbBEFGHED_CpCKPa@b@kBxBe@h@MNy@x@[\\w@t@k@n@o@t@Y\\IHKPe@p@cA|AQXIRINMd@OFQPODQ?MIsDwBSMaAk@kAw@OI}AgAgAs@aCgBo@_@GEm@a@YMwBaAg@UcDuA[Qc@U]QUMu@a@kBaAmGoDGCCCIEOIKG{@a@aBg@KCSIq@[qAk@KGcBo@UEMCQE[I_@QMGg@YEAo@SGCi@Mo@SICOESGGCCAcAUSEY?O@OH_@\\{JhMo@n@]To@PuAP}Gj@M@g@Fa@BqFb@YHSVQHWDI@K@I@MB]@KCGCIIIACASCcBLkANgAL_@DYDSBkBTC?SBcC\\i@H}Gt@K@wCFu@Bc@BkBFsC@iGAW@Y@Y@_@EgAAm@@O?mAAsA?wADkJTiMVsDD[?cC@A?iMOqFEmBAqAAuDAwBDaGHY?qGDo@?m@?o@Am@EYCQC_AMsCu@aBWwASs@EKNEDaAQy@Mm@KeB]y@Oa@IaAOQEQCq@Mk@G}AQSC[EqB]_AS{Bk@_AY}DuAICw@UgF{AsBs@aCy@SIYK_A]_Aa@k@Uq@SwAQ{@KqCe@_Be@}@Ws@Ue@MOGk@Qs@IQ?I?wA?qACuAEs@?G?[COAE?QE_@GYE]G_BMQAwCU}Ce@F_AHsCHe@R]\\m@BCt@i@^UPOLSJa@@IDm@Hq@Bc@Fk@B[JyAJgA@KJcAR{@DMNm@R{@Lg@XmAT{ARAhASdA[l@OJCr@S\\KVGfA[Rs@HYLSf@GLCjAZXHt@`@RPF@"),
    ("westeast", "}khnAm~ixM`A@fFDFqFDiC@iA@_A?[DaDtAJF@tAAB?tB@xA@xABbAA|@g@z@]bAMH?F?d@AZ?T?H@H?bA@X@H?L?r@uAz@cA|@w@@S|@wAXe@H[Di@FqE@W@WB[BMBMBI@IBIh@}@HITYNSLYLWHYFWHg@Fc@?EFwA?ICg@?K?OB]?IDe@BUNqB^{EJw@^gDFm@PYAYAC?KCOCSCK_AgECIKa@CEAGCIK]Mk@EKGMQa@CYAU?SHq@F]HST[b@i@NK\\UHIDIBIBGpAq@NIp@YNENCNAN?P?N?LALERKLKJIDCJQR]D[@A@a@Ee@OoAASAIEg@CMCq@Ii@Ko@AGOwAMkBGmAAk@?m@F}CNcE?m@BuCBiAFmA@[HwAF_BDmBJmALw@Po@Xq@t@sA@CHMLUPWbBkCt@wA`@w@`BsCv@iA`BoC\\k@@ADGXg@Va@FKDEl@kAb@o@f@s@FMBCBEFIJGCKAMDMDG@AKSMa@{@qBGOc@eAAAw@sBo@{A_@{@M]Sc@O]CGSUKGGEGESOyCuCe@c@iCcC[Ye@g@{@u@g@g@u@s@c@c@WUUUiBcBY[CACCQSSQSOu@k@sAcAeAw@IGKKSYcBwBMSc@m@EGKOAACCEGPQ`@Ev@AL?f@?|@Ar@?FAR?PAJ@\\Bb@DVDPBr@EHAVAD?JARCFA\\IJCDC@ALKPi@f@uBH]L_@Tu@nC_M|AyG@CBOFOBOr@kDR{@d@qBf@{B^cBBIXsAj@aCBMDK@IFUj@cCFY@GBKJe@j@gCDUFOFY@C|@aE~A}G`@gBbAkE^cBz@qD@GBMOEqCm@CAOCKCDMBMNm@R{@LUn@gCLm@ZoANm@ZoAFSLo@BMR}@No@@E`@kBF]BI?CH_ABQHiA?E@MSCUCa@KYCe@Gq@GA?E?I?K?KBYAe@C@IOKeAEM?cC@GIaAiCq@aBOi@Ui@Ui@Ok@Ge@E]COM{@K}@CqACg@A]CiAAICeACu@AMCuAAOCk@Aa@cBYc@GYRSJaCa@c@EWCYFEf@CX?h@g@@"),
]


def route_chunks(name: str, encoded: str, edges_per_chunk: int = 12) -> list[dict]:
    points = polyline.decode(encoded)
    chunks = []
    for index, start in enumerate(range(0, len(points) - 1, edges_per_chunk)):
        chunk = points[start : min(start + edges_per_chunk + 1, len(points))]
        if len(chunk) < 2:
            continue
        wkt_points = ",".join(f"{longitude} {latitude}" for latitude, longitude in chunk)
        chunks.append({
            "segment_hash": hashlib.sha256(f"demo:{name}:{index}".encode()).hexdigest(),
            "encoded_polyline": polyline.encode(chunk, 5),
            "wkt": f"SRID=4326;LINESTRING({wkt_points})",
            "points": chunk,
        })
    return chunks


def seed() -> None:
    route_groups = [route_chunks(name, encoded) for name, encoded in DEMO_ROUTES]
    pieces = [piece for group in route_groups for piece in group]
    with SessionLocal.begin() as db:
        db.execute(delete(RoadReport).where(RoadReport.is_demo.is_(True)))
        db.execute(text("DELETE FROM road_segments"))
        user = db.get(User, "pathfinder-demo")
        if not user:
            user = User(id="pathfinder-demo", name="Pathfinder Demo")
            db.add(user)
            db.flush()

        db.execute(
            STORE_SEGMENTS_SQL,
            {"segments": json.dumps([
                {key: piece[key] for key in ("segment_hash", "encoded_polyline", "wkt")}
                for piece in pieces
            ])},
        )

        for route_index, group in enumerate(route_groups):
            for segment_index, piece in enumerate(group):
                latitude, longitude = piece["points"][len(piece["points"]) // 2]
                quality = round(max(24, min(92, 58 + 28 * math.sin(route_index * 1.7 + segment_index / 3.4))), 1)
                damage = 100 - quality
                report = RoadReport(
                    user_id=user.id,
                    latitude=latitude,
                    longitude=longitude,
                    description=f"Synthetic Bengaluru {DEMO_ROUTES[route_index][0]} corridor observation {segment_index + 1}",
                    status=ReportStatus.READY,
                    is_demo=True,
                )
                report.assessment = RoadAssessment(
                    model_version="demo-seed-v3",
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
    print(f"Seeded {len(pieces)} labeled observations across {len(DEMO_ROUTES)} actual-road corridors")


if __name__ == "__main__":
    seed()