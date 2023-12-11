import datetime
import re
from . import consts
from . import errors
from typing import Union, Optional, Dict


def normalize_text(text: str, lower: bool = True) -> str:
    text = " ".join(text.split())
    text = text.replace("\n", "").replace("\t", "")
    if lower:
        text = text.lower()
    return text


def normalize_status(status: str) -> str:
    normed = normalize_text(status)
    if normed in consts.STATUSES:
        return normed
    if normed in ["win"]:
        return consts.STATUS_WIN
    if normed in ["loss"]:
        return consts.STATUS_LOSS
    if normed in ["draw"]:
        return consts.STATUS_DRAW
    if normed in ["cancelled", "cancelled bout"]:
        return consts.STATUS_CANCELLED
    if normed in ["no contest", "overturned to no contest"]:
        return consts.STATUS_NC
    if normed in ["upcoming", "confirmed upcoming bout"]:
        return consts.STATUS_UPCOMING
    if normed in ["unknown", "n/a", "na"]:
        return consts.STATUS_UNKNOWN
    raise errors.InvalidStatusValueError(status)


def normalize_sport(sport: str) -> str:
    normed = normalize_text(sport)
    if normed in consts.SPORTS:
        return normed
    if normed in ["mma", "pancrase"]:
        return consts.SPORT_MMA
    if normed in ["knuckle_mma"]:
        return consts.SPORT_KNUCKLE_MMA
    if normed in ["boxing", "boxing_cage"]:
        return consts.SPORT_BOX
    if normed in ["knuckle"]:
        return consts.SPORT_KNUCKLE_BOX
    if normed in ["kickboxing"]:
        return consts.SPORT_KICK
    if normed in ["muay"]:
        return consts.SPORT_MUAY
    if normed in ["karate"]:
        return consts.SPORT_KARATE
    if normed in ["sanda"]:
        return consts.SPORT_SANDA
    if normed in ["lethwei"]:
        return consts.SPORT_LETHWEI
    if normed in ["grappling"]:
        return consts.SPORT_GRAPPLE
    if normed in ["shootboxing"]:
        return consts.SPORT_SHOOT
    if normed in ["wrestling"]:
        return consts.SPORT_WRESTLE
    if normed in ["sambo"]:
        return consts.SPORT_SAMBO
    if normed in ["valetudo"]:
        return consts.SPORT_VALE
    if normed in ["judo"]:
        return consts.SPORT_JUDO
    if normed in ["combat_jj"]:
        return consts.SPORT_COMBAT_JJ
    if normed in ["custom"]:
        return consts.SPORT_CUSTOM
    raise errors.InvalidSportValueError(sport)


def normalize_weight_class(weight_class: str) -> str:
    normed = normalize_text(weight_class)
    if normed in consts.WEIGHT_CLASSES:
        return normed
    if normed in ["atomweight"]:
        return consts.WEIGHT_CLASS_ATOM
    if normed in ["strawweight"]:
        return consts.WEIGHT_CLASS_STRAW
    if normed in ["flyweight"]:
        return consts.WEIGHT_CLASS_FLY
    if normed in ["bantamweight"]:
        return consts.WEIGHT_CLASS_BANTAM
    if normed in ["featherweight"]:
        return consts.WEIGHT_CLASS_FEATHER
    if normed in ["lightweight"]:
        return consts.WEIGHT_CLASS_LIGHT
    if normed in ["super lightweight"]:
        return consts.WEIGHT_CLASS_S_LIGHT
    if normed in ["welterweight"]:
        return consts.WEIGHT_CLASS_WELTER
    if normed in ["super welterweight"]:
        return consts.WEIGHT_CLASS_S_WELTER
    if normed in ["middleweight"]:
        return consts.WEIGHT_CLASS_MIDDLE
    if normed in ["super middleweight"]:
        return consts.WEIGHT_CLASS_S_MIDDLE
    if normed in ["light heavyweight"]:
        return consts.WEIGHT_CLASS_L_HEAVY
    if normed in ["heavyweight"]:
        return consts.WEIGHT_CLASS_HEAVY
    if normed in ["cruiserweight"]:
        return consts.WEIGHT_CLASS_CRUISER
    if normed in ["super heavyweight"]:
        return consts.WEIGHT_CLASS_S_HEAVY
    raise errors.InvalidWeightClassValueError(weight_class)


def normalize_billing(billing: str) -> str:
    normed = normalize_text(billing)
    if normed in consts.BILLINGS:
        return normed
    if normed in ["main event"]:
        return consts.BILLING_MAIN
    if normed in ["co-main event"]:
        return consts.BILLING_CO_MAIN
    if normed in ["main card"]:
        return consts.BILLING_MAIN_CARD
    if normed in ["preliminary card"]:
        return consts.BILLING_PRELIM_CARD
    if normed in ["postlim"]:
        return consts.BILLING_POSTLIM_CARD
    raise errors.InvalidBillingValueError(billing)


def normalize_date(date: str) -> str:
    normed = normalize_text(date)
    # 2014.09.09
    matched = re.match(r"^(\d+)\.(\d+)\.(\d+)$", normed)
    if matched is not None:
        return f"{matched.group(1):04}-{matched.group(2):02}-{matched.group(3):02}"
    # 2014-09-09
    matched = re.match(r"^(\d+)\-(\d+)\-(\d+)$", normed)
    if matched is not None:
        f"{matched.group(1):04}-{matched.group(2):02}-{matched.group(3):02}"
    raise errors.InvalidDateValueError(date)


def normalize_round_format(round_format: str) -> str:
    normed = normalize_text(round_format)

    # 5 x 5 minute rounds
    # 5 x 5 min
    matched = re.match(r"^(\d+) x (\d+)", normed)
    if matched is not None:
        format = "-".join([matched.group(2) for _ in range(int(matched.group(1)))])
        return format

    # 5 min one round
    matched = re.match(r"^(\d+) min one round$", normed)
    if matched is not None:
        format = matched.group(1)
        return format

    # 5 min round plus overtime
    matched = re.match(r"^(\d+) min round plus overtime$", normed)
    if matched is not None:
        format = f"{matched.group(1)}-ot"
        return format

    # 5-5
    # 5-5-5
    # 5-5-5-5
    # 5-5 plus overtime
    # 5-5-5 plus overtime
    # 5-5-5-5 plus overtime
    # 5-5 two rounds
    matched = re.match(r"^(\d+(?:\-\d+)+)( plus overtime)?", normed)
    if matched is not None:
        format = matched.group(1)
        if matched.group(2) is not None:
            format += "-ot"
        return format

    # 5 + 5 two rounds
    # 5 + 5 + 5 three rounds
    matched = re.match(r"^(\d+(?: \+ \d+)+)", normed)
    if matched is not None:
        format = "-".join(list(map(lambda x: x.strip(), matched.group(1).split("+"))))
        return format

    # 5 min unlim rounds
    matched = re.match(r"^(\d+) min unlim rounds$", normed)
    if matched is not None:
        format = matched.group(1) + "-*"
        return format

    # 1 Round, No Limit
    matched = re.match(r"^1 round, no limit$", normed)
    if matched is not None:
        return "*"

    # 3 Rounds
    matched = re.match(r"^(\d+) rounds$", normed)
    if matched is not None:
        return "-".join(["?"] * int(matched.group(1)))
    raise errors.InvalidRoundFormatValueError(round_format)


def parse_round_time(round_time: str) -> Dict[str, int]:
    normed = normalize_text(round_time)
    matched = re.match(r"^(\d+):(\d+)$", normed)
    if matched is not None:
        return {"m": int(matched.group(1)), "s": int(matched.group(2))}
    raise errors.InvalidRoundTimePatternError(round_time)


def parse_round(round: str) -> int:
    normed = normalize_text(round)
    matched = re.match(r"^r(\d+)$", normed)
    if matched is not None:
        return int(matched.group(1))
    raise errors.InvalidRoundPatternError(round)


def parse_match_summary(match_summary: str) -> Dict:
    normed = normalize_text(match_summary)
    normed_split = list(
        filter(lambda x: x != "", list(map(lambda x: x.strip(), normed.split("·"))))
    )
    try:
        status = normalize_status(normed_split[0])
    except errors.InvalidStatusValueError as e:
        try:
            return {"method": infer_method(normed_split[0])}
        except errors.CantInferMethodError as e:
            raise errors.InvalidMatchSummaryPatternError(match_summary)
    normed = " · ".join(normed_split)
    n = len(normed_split)
    try:
        if n == 4:
            # Win|Loss · Head Kick & Punches · 0:40 · R1
            # No Contest · Accidental Kick to the Groin · 0:09 · R1
            # Draw · Accidental Thumb to Amoussou's Eye · 4:14 · R1
            # Draw · Draw · 5:00 · R2
            # Draw · Majority · 3:00 · R3
            matched = re.match(
                r"^(win|loss|draw|no contest) · ([^·]+) · (\d+:\d+) · (r\d+)$", normed
            )
            if matched is not None:
                note = matched.group(2)
                return {
                    "status": status,
                    "time": parse_round_time(matched.group(3)),
                    "round": parse_round(matched.group(4)),
                    "method": infer_method(note),
                }
        elif n == 3:
            # Win|Loss|Draw · Decision · Unanimous|Majority|Split
            matched = re.match(
                r"^(win|loss|draw) · (decision · .+)$",
                normed,
            )
            if matched is not None:
                note = matched.group(2)
                return {
                    "status": status,
                    "method": infer_method(note),
                }
            # Win|Loss · Flying Knee & Punches · R1
            # Draw · Washington Elbowed in Back of Head · R1
            # No Contest · Accidental Illegal Knee · R1
            matched = re.match(
                r"^(win|loss|draw|no contest) · ([^·]+) · (r\d+)$", normed
            )
            if matched is not None:
                note = matched.group(2)
                return {
                    "status": status,
                    "round": parse_round(matched.group(3)),
                    "method": infer_method(note),
                }
            # No Contest · 3:15 · R1
            matched = re.match(r"^no contest · (\d+:\d+) · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": status,
                    "time": parse_round_time(matched.group(1)),
                    "round": parse_round(matched.group(2)),
                }
        elif n == 2:
            # Win|Loss|Draw · Decision
            # Win|Loss · KO/TKO
            # Draw · Unanimous|Majority|Split
            # No Contest · Accidental Illegal Elbow
            matched = re.match(r"^(win|loss|draw|no contest) · (.+)$", normed)
            if matched is not None:
                note = matched.group(2)
                return {
                    "status": status,
                    "method": infer_method(note),
                }
            # No Contest · R3
            matched = re.match(r"^no contest · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": status,
                    "round": parse_round(matched.group(1)),
                }
        elif n == 1:
            # Win|Loss|Draw|No Contest
            return {
                "status": status,
            }
    except (
        errors.InvalidRoundTimePatternError,
        errors.InvalidRoundPatternError,
        errors.InvalidStatusValueError,
        errors.CantInferMethodError,
    ) as e:
        raise errors.InvalidMatchSummaryPatternError(match_summary)
    raise errors.InvalidMatchSummaryPatternError(match_summary)


def parse_title_info(title_info: str) -> Dict:
    normed = normalize_text(title_info)
    normed_split = list(
        filter(lambda x: x != "", map(lambda x: x.strip(), normed.split("·")))
    )
    if len(normed_split) == 2:
        # Champion · UFC Featherweight Championship
        return {
            "as": normed_split[0],
            "for": normed_split[1],
        }
    elif len(normed_split) == 1:
        # Tournament Championship
        return {"for": normed_split[0]}
    raise errors.InvalidTitleInfoPatternError(title_info)


def parse_odds(odds: str) -> float:
    normed = normalize_text(odds)

    # +210 · Moderate Underdog
    # 0 · Close
    matched = re.match(r"^([\+\-])?([\d\.]+)", normed)
    if matched is not None:
        value = float(matched.group(2))
        sign = matched.group(1)
        if sign == "-":
            value *= -1
        return (value / 100) + 1.0
    raise errors.InvalidOddsPatternError(odds)


def parse_weight_summary(weight_summary: str) -> Dict[str, float]:
    normed = normalize_text(weight_summary)
    normed_split = list(map(lambda x: x.strip(), normed.split("·")))
    ret = {}

    # Heavyweight
    # 110 kg|kgs|lb|lbs
    # 110 kg|kgs|lb|lbs (49.9 kg|kgs|lb|lbs)
    matched = re.match(r"^(.*weight|([\d\.]+) (kgs?|lbs?))", normed_split[0])
    if matched is None:
        raise errors.InvalidWeightSummaryPatternError(weight_summary)
    if matched.group(2) is not None and matched.group(3) is not None:
        value, unit = float(matched.group(2)), matched.group(3)
        ret["class"] = to_weight_class(value, unit=unit)
        ret["limit"] = to_kg(value, unit=unit)
    else:
        try:
            weight_class = normalize_weight_class(matched.group(1))
        except errors.InvalidWeightClassValueError as e:
            pass
        else:
            ret["class"] = weight_class
    for s in normed_split[1:]:
        # 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        # Weigh-In 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        matched = re.match(r"^(weigh-in )?([\d\.]+) (kgs?|lbs?)", s)
        if matched is None:
            raise errors.InvalidWeightSummaryPatternError(weight_summary)
        if matched.group(2) is None or matched.group(3) is None:
            raise errors.InvalidWeightSummaryPatternError(weight_summary)
        value, unit = float(matched.group(2)), matched.group(3)
        ret["limit" if matched.group(1) is None else "weigh_in"] = to_kg(
            value, unit=unit
        )
    if "class" not in ret:
        if "limit" in ret:
            ret["class"] = to_weight_class(ret["limit"])
        elif "weigh_in" in ret:
            ret["class"] = to_weight_class(ret["weigh_in"])
    if ret == {}:
        raise errors.InvalidWeightSummaryPatternError(weight_summary)
    return ret


def parse_last_weigh_in(last_weigh_in: str) -> Union[float, None]:
    normed = normalize_text(last_weigh_in)
    matched = re.match(r"^([\d\.]+) (kgs?|lbs?)", normed)
    if matched is not None:
        value = float(matched.group(1))
        unit = matched.group(2)
        return to_kg(value, unit=unit)
    if normed in consts.VALUES_NOT_AVAILABLE:
        return None
    raise errors.InvalidLastWeighInPatternError(last_weigh_in)


def parse_record(record: str) -> Dict[str, int]:
    normed = normalize_text(record)
    matched = re.match(r"^(\d+)-(\d+)-(\d+)", normed)
    if matched is not None:
        return {
            "w": int(matched.group(1)),
            "l": int(matched.group(2)),
            "d": int(matched.group(3)),
        }
    raise errors.InvalidRecordPatternError(record)


def parse_round_format(round_format: str) -> Dict:
    # 4-4-4
    # 4
    # 4-4-4-ot
    # 4-ot
    matched = re.match(r"^(\d+(?:\-(?:\d+|ot))*)$", round_format)
    if matched is not None:
        round_minutes = []
        ot = False
        for s in round_format.split("-"):
            if s == "ot":
                ot = True
            else:
                round_minutes.append(int(s))
        ret = {
            "type": consts.ROUND_FORMAT_TYPE_NORMAL,
            "ot": ot,
            "rounds": len(round_minutes),
            "minutes": sum(round_minutes),
            "round_minutes": round_minutes,
            "ot_minutes": round_minutes[-1] if ot else 0,
        }
        return ret

    # 4-*
    matched = re.match(r"^(\d+\-\*)$", round_format)
    if matched is not None:
        m = int(round_format.split("-")[0])
        return {"type": consts.ROUND_FORMAT_TYPE_UNLIM_ROUNDS, "minutes_per_round": m}

    # *
    if round_format == "*":
        return {"type": consts.ROUND_FORMAT_TYPE_UNLIM_ROUND_TIME, "rounds": 1}

    # ?
    # ?-?-?
    matched = re.match(r"^(\?(?:\-\?)*)$", round_format)
    if matched is not None:
        return {
            "type": consts.ROUND_FORMAT_TYPE_ROUND_TIME_UNKNONW,
            "rounds": len(round_format.split("-")),
        }
    raise errors.InvalidRoundFormatPatternError(round_format)


def calc_age(date: str, date_of_birth: str) -> float:
    diff = datetime.datetime.strptime(date, "%Y-%m-%d") - datetime.datetime.strptime(
        date_of_birth, "%Y-%m-%d"
    )
    return diff.days / 365.25


def to_weight_class(value: float, unit: str = "kg", margin: float = 0.02) -> str:
    if unit not in ["kg", "kgs", "lbs", "lb"]:
        raise ValueError(f"Unsupported unit: {unit}")
    if margin < 0 or 1 < margin:
        raise ValueError("Margin must be [0, 1]")
    kg = to_kg(value, unit=unit)
    scale = 1 + margin
    if kg <= consts.WEIGHT_LIMIT_ATOM * scale:
        return consts.WEIGHT_CLASS_ATOM
    if kg <= consts.WEIGHT_LIMIT_STRAW * scale:
        return consts.WEIGHT_CLASS_STRAW
    if kg <= consts.WEIGHT_LIMIT_FLY * scale:
        return consts.WEIGHT_CLASS_FLY
    if kg <= consts.WEIGHT_LIMIT_BANTAM * scale:
        return consts.WEIGHT_CLASS_BANTAM
    if kg <= consts.WEIGHT_LIMIT_FEATHER * scale:
        return consts.WEIGHT_CLASS_FEATHER
    if kg <= consts.WEIGHT_LIMIT_LIGHT * scale:
        return consts.WEIGHT_CLASS_LIGHT
    if kg <= consts.WEIGHT_LIMIT_S_LIGHT * scale:
        return consts.WEIGHT_CLASS_S_LIGHT
    if kg <= consts.WEIGHT_LIMIT_WELTER * scale:
        return consts.WEIGHT_CLASS_WELTER
    if kg <= consts.WEIGHT_LIMIT_S_WELTER * scale:
        return consts.WEIGHT_CLASS_S_WELTER
    if kg <= consts.WEIGHT_LIMIT_MIDDLE * scale:
        return consts.WEIGHT_CLASS_MIDDLE
    if kg <= consts.WEIGHT_LIMIT_S_MIDDLE:
        return consts.WEIGHT_CLASS_S_MIDDLE
    if kg <= consts.WEIGHT_LIMIT_L_HEAVY * scale:
        return consts.WEIGHT_CLASS_L_HEAVY
    if kg <= consts.WEIGHT_LIMIT_CRUISER * scale:
        return consts.WEIGHT_CLASS_CRUISER
    if kg <= consts.WEIGHT_LIMIT_HEAVY * scale:
        return consts.WEIGHT_CLASS_HEAVY
    return consts.WEIGHT_CLASS_S_HEAVY


def to_weight_limit(weight_class: str) -> Union[None, float]:
    if weight_class not in consts.WEIGHT_CLASSES:
        raise ValueError(f"invalid weight class: {weight_class}")
    if weight_class == consts.WEIGHT_CLASS_ATOM:
        return consts.WEIGHT_LIMIT_ATOM
    if weight_class == consts.WEIGHT_CLASS_STRAW:
        return consts.WEIGHT_LIMIT_STRAW
    if weight_class == consts.WEIGHT_CLASS_FLY:
        return consts.WEIGHT_LIMIT_FLY
    if weight_class == consts.WEIGHT_CLASS_BANTAM:
        return consts.WEIGHT_LIMIT_BANTAM
    if weight_class == consts.WEIGHT_CLASS_FEATHER:
        return consts.WEIGHT_LIMIT_FEATHER
    if weight_class == consts.WEIGHT_CLASS_LIGHT:
        return consts.WEIGHT_LIMIT_LIGHT
    if weight_class == consts.WEIGHT_CLASS_S_LIGHT:
        return consts.WEIGHT_LIMIT_S_LIGHT
    if weight_class == consts.WEIGHT_CLASS_WELTER:
        return consts.WEIGHT_LIMIT_WELTER
    if weight_class == consts.WEIGHT_CLASS_S_WELTER:
        return consts.WEIGHT_LIMIT_S_WELTER
    if weight_class == consts.WEIGHT_CLASS_MIDDLE:
        return consts.WEIGHT_LIMIT_MIDDLE
    if weight_class == consts.WEIGHT_CLASS_S_MIDDLE:
        return consts.WEIGHT_LIMIT_S_MIDDLE
    if weight_class == consts.WEIGHT_CLASS_L_HEAVY:
        return consts.WEIGHT_LIMIT_L_HEAVY
    if weight_class == consts.WEIGHT_CLASS_CRUISER:
        return consts.WEIGHT_LIMIT_CRUISER
    if weight_class == consts.WEIGHT_CLASS_HEAVY:
        return consts.WEIGHT_LIMIT_HEAVY
    return consts.WEIGHT_LIMIT_S_HEAVY


def to_meter(feet: float, inch: float) -> float:
    return feet * 0.3048 + inch * 0.0254


def to_kg(value: float, unit: str = "lb") -> float:
    if unit not in ["kg", "kgs", "lb", "lbs"]:
        raise ValueError(f"Unsupported unit: {unit}")
    if unit.startswith("lb"):
        return value * 0.453592
    return value


def infer_method(note: str) -> str:
    normed = normalize_text(note)
    # Overturned
    if "overturned" in normed:
        return consts.METHOD_OVERTURNED
    # Decision
    if "decision" in normed:
        if normed == "decision" or normed == "decision · draw":
            return consts.METHOD_DECISION_GENERAL
        if "unanimous" in normed:
            return consts.METHOD_DECISION_UNANIMOUS
        if "majority" in normed:
            return consts.METHOD_DECISION_MAJORITY
        if "split" in normed or "spilt" in normed or "spit" in normed:
            return consts.METHOD_DECISION_SPLIT
        if "point" in normed:
            return consts.METHOD_DECISION_POINT
        if "time limit" in normed:
            return consts.METHOD_DECISION_TIMELIMIT
        if "technical" in normed or "referee" in normed or "illegal" in normed:
            return consts.METHOD_DECISION_TECHNICAL
        if "medical" in normed or "injury" in normed or "doctor":
            return consts.METHOD_DECISION_MEDICAL
        if "retirement" in normed:
            return consts.METHOD_DECISION_RETIREMENT
    if normed == "unanimous":
        return consts.METHOD_DECISION_UNANIMOUS
    if normed == "majority":
        return consts.METHOD_DECISION_MAJORITY
    if normed == "split":
        return consts.METHOD_DECISION_SPLIT

    # Illegal
    if (
        "illegal" in normed
        or "disquali" in normed
        or "foul" in normed
        or "headbutt" in normed
        or "groin" in normed
        or "low blow" in normed
        or "eye poke" in normed
        or "forfeit" in normed
        or "ropes" in normed
        or "drug" in normed
        or "fence grabbing" in normed
        or "language" in normed
        or "unanswered" in normed
        or "dropped on head" in normed
        or "liability" in normed
        or "interference" in normed
        or "refused" in normed
        or "refusal" in normed
        or "didn't" in normed
        or "did not" in normed
        or "answer the bell" in normed
        or "finger in the eye" in normed
        or "missed" in normed
        or "misswed" in normed
        or "unsportsman" in normed
    ):
        return consts.METHOD_DQ

    # Accidental
    if (
        normed in ["referee & judging errors"]
        or "accidental" in normed
        or "malfunction" in normed
        or "both fighters" in normed
    ):
        return consts.METHOD_ACCIDENTAL

    # Walkover (bjj)
    if normed in ["walkover", "walk over"]:
        return consts.METHOD_WALKOVER

    # Ippon
    if "ippon" in normed:
        return consts.METHOD_IPPON

    # KO/TKO
    if (
        normed
        in ["ko", "knee", "knee", "hook", "cut", "cuts", "forehead cut", "standing"]
        or "tko" in normed
        or "ko/tko" in normed
        or "knockdown" in normed
        or "knock down" in normed
        or "knock out" in normed
        or "knockout" in normed
        or "knee to" in normed
        or "kick" in normed
        or "punch" in normed
        or "elbow" in normed
        or "hooks" in normed
        or "pound" in normed
        or "suplex" in normed
        or "liver" in normed
        or "knees" in normed
        or "overhand" in normed
        or "straight" in normed
        or "stomp" in normed
        or "strike" in normed
        or "slam" in normed
        or "fist" in normed
        or "body" in normed
        or "jab" in normed
        or "cut to" in normed
        or "cut from" in normed
        or "cut on" in normed
        or "upper" in normed
        or "technical" in normed
        or "counter" in normed
        or "injury" in normed
        or "dislocated" in normed
        or "medical" in normed
        or "broken" in normed
        or "uppercut" in normed
        or "flying knee" in normed
        or "ground knee" in normed
        or "t hand" in normed
        or "t hook" in normed
        or "t cross" in normed
        or "t knee" in normed
        or "towel" in normed
        or "retire" in normed
        or "abandon" in normed
        or "stoppage" in normed
        or "referee stop" in normed
        or "exhaustion" in normed
        or "painful" in normed
        or "vomit" in normed
    ):
        return consts.METHOD_KO_TKO
    # Submission
    if (
        "tapout" in normed
        or "tap out" in normed
        or "submission" in normed
        or "lock" in normed
        or "hold" in normed
        or "bar" in normed
        or "verbal" in normed
        or "triangle" in normed
        or "guillotine" in normed
        or "choke" in normed
        or "crank" in normed
        or "crunch" in normed
        or "opener" in normed
        or "stretch" in normed
        or "kimura" in normed
        or "twister" in normed
        or "d'arce" in normed
        or "crossface" in normed
        or "cross face" in normed
        or "pressure" in normed
        or "necktie" in normed
        or "smother" in normed
        or "neck tie" in normed
        or "katagatame" in normed
        or "calf slicer" in normed
        or "americana" in normed
        or "anaconda" in normed
        or "heelhook" in normed
        or "heel hook" in normed
        or "banana split" in normed
        or "cranck" in normed
        or "cholke" in normed
        or "kumura" in normed
        or "gogoplata" in normed
        or "monoplata" in normed
        or "omo plata" in normed
        or "omoplata" in normed
        or "omplata" in normed
        or "omaplata" in normed
    ):
        return consts.METHOD_SUBMISSION
    raise errors.CantInferMethodError(note)
