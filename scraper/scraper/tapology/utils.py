import datetime
import re
from . import consts
from .errors import NormalizeError, ParseError, InferError


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
    raise NormalizeError("status", status)


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
    raise NormalizeError("sport", sport)


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
    raise NormalizeError("weight class", weight_class)


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
    raise NormalizeError("billing", billing)


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
    raise NormalizeError("date", date)


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
    raise NormalizeError("round format", round_format)


def parse_round_time(round_time: str) -> dict[str, int]:
    normed = normalize_text(round_time)
    matched = re.match(r"^(\d+):(\d+)$", normed)
    if matched is not None:
        return {"m": int(matched.group(1)), "s": int(matched.group(2))}
    raise ParseError("round time", round_time)


def parse_round(round: str) -> int:
    normed = normalize_text(round)
    matched = re.match(r"^r(\d+)$", normed)
    if matched is not None:
        return int(matched.group(1))
    raise ParseError("round", round)


def parse_match_summary(sport: str, status: str, match_summary: str) -> dict:
    sport = normalize_sport(sport)
    status = normalize_status(status)
    normed_split = list(
        filter(
            lambda x: x != "",
            list(map(lambda x: x.strip(), normalize_text(match_summary).split("·"))),
        )
    )
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
                r"^(?:win|loss|draw|no contest) · ([^·]+) · (\d+:\d+) · (r\d+)$", normed
            )
            if matched is not None:
                note = matched.group(1)
                return {
                    "time": parse_round_time(matched.group(2)),
                    "round": parse_round(matched.group(3)),
                    "method": infer_method(sport, status, note),
                }
        elif n == 3:
            # Win|Loss|Draw|No Contest · Decision · Unanimous|Majority|Split
            matched = re.match(
                r"^(?:win|loss|draw|no contest) · (decision · .+)$",
                normed,
            )
            if matched is not None:
                note = matched.group(1)
                return {
                    "method": infer_method(sport, status, note),
                }

            # Win|Loss|Draw|No Contest · 3:15 · R1
            matched = re.match(
                r"^(?:win|loss|draw|no contest) · (\d+:\d+) · (r\d+)$", normed
            )
            if matched is not None:
                return {
                    "time": parse_round_time(matched.group(1)),
                    "round": parse_round(matched.group(2)),
                    "method": consts.METHOD_UNKNOWN,
                }

            # Win|Loss|Draw|No Contest · Flying Knee & Punches · R1
            matched = re.match(
                r"^(?:win|loss|draw|no contest) · ([^·]+) · (r\d+)$", normed
            )
            if matched is not None:
                note = matched.group(1)
                return {
                    "round": parse_round(matched.group(2)),
                    "method": infer_method(sport, status, note),
                }
        elif n == 2:
            # Win|Loss|Draw|No Contest · R3
            matched = re.match(r"^(?:win|loss|draw|no contest) · (r\d+)$", normed)
            if matched is not None:
                return {
                    "round": parse_round(matched.group(1)),
                    "method": consts.METHOD_UNKNOWN,
                }

            # Win|Loss|Draw|No Contest · KO/TKO
            matched = re.match(r"^(?:win|loss|draw|no contest) · (.+)$", normed)
            if matched is not None:
                note = matched.group(1)
                return {
                    "method": infer_method(sport, status, note),
                }
        elif n == 1:
            # Win|Loss|Draw|No Contest
            return {"method": consts.METHOD_UNKNOWN}
    except (
        NormalizeError,
        ParseError,
        InferError,
    ):
        raise ParseError("match summary", match_summary)
    raise ParseError("match summary", match_summary)


def parse_title_info(title_info: str) -> dict[str, str]:
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
    raise ParseError("title info", title_info)


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
    raise ParseError("odds", odds)


def parse_weight_summary(weight_summary: str) -> dict[str, float]:
    normed = normalize_text(weight_summary)
    normed_split = list(map(lambda x: x.strip(), normed.split("·")))
    ret = {}

    # Heavyweight
    # 110 kg|kgs|lb|lbs
    # 110 kg|kgs|lb|lbs (49.9 kg|kgs|lb|lbs)
    matched = re.match(r"^(.*weight|([\d\.]+) (kgs?|lbs?))", normed_split[0])
    if matched is None:
        raise ParseError("weight summary", weight_summary)
    if matched.group(2) is not None and matched.group(3) is not None:
        value, unit = float(matched.group(2)), matched.group(3)
        ret["class"] = to_weight_class(value, unit=unit)
        ret["limit"] = to_kg(value, unit=unit)
    else:
        try:
            weight_class = normalize_weight_class(matched.group(1))
        except NormalizeError:
            pass
        else:
            ret["class"] = weight_class
    for s in normed_split[1:]:
        # 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        # Weigh-In 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        matched = re.match(r"^(weigh-in )?([\d\.]+) (kgs?|lbs?)", s)
        if matched is None:
            raise ParseError("weight summary", weight_summary)
        if matched.group(2) is None or matched.group(3) is None:
            raise ParseError("weight summary", weight_summary)
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
        raise ParseError("weight summary", weight_summary)
    return ret


def parse_last_weigh_in(last_weigh_in: str) -> float | None:
    normed = normalize_text(last_weigh_in)
    matched = re.match(r"^([\d\.]+) (kgs?|lbs?)", normed)
    if matched is not None:
        value = float(matched.group(1))
        unit = matched.group(2)
        return to_kg(value, unit=unit)
    if normed in consts.VALUES_NOT_AVAILABLE:
        return None
    raise ParseError("last weigh-in", last_weigh_in)


def parse_record(record: str) -> dict[str, int]:
    normed = normalize_text(record)
    matched = re.match(r"^(\d+)-(\d+)-(\d+)", normed)
    if matched is not None:
        return {
            "w": int(matched.group(1)),
            "l": int(matched.group(2)),
            "d": int(matched.group(3)),
        }
    raise ParseError("record", record)


def parse_round_format(round_format: str) -> dict:
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
            "type": consts.ROUND_FORMAT_TYPE_REGULAR,
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
    raise ParseError("round format", round_format)


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


def to_weight_limit(weight_class: str) -> float | None:
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


def infer_method(sport: str, status: str, note: str) -> str:
    normed = normalize_text(note)
    if sport not in [
        consts.SPORT_MMA,
    ]:
        return consts.METHOD_UNKNOWN

    if status == consts.STATUS_DRAW:
        if normed == "draw":
            return consts.METHOD_UNKNOWN
        if "decision" in normed or normed in ["unanimous", "majority", "split"]:
            return consts.METHOD_DECISION
        if "time limit" in normed:
            return consts.METHOD_TIMELIMIT
        if (
            "illegal" in normed
            or "accident" in normed
            or "unsportsman" in normed
            or "disq" in normed
        ):
            return consts.METHOD_FOUL
        if "injur" in normed:
            return consts.METHOD_STOPPAGE_DOCTOR
    elif status == consts.STATUS_NC:
        if normed in ["nc", "no contest"]:
            return consts.METHOD_UNKNOWN
        if "drug" in normed or "doping" in normed or "inhaler" in normed:
            return consts.METHOD_DOPING
        if "overturn" in normed:
            return consts.METHOD_OVERTURNED
        if "weight" in normed:
            return consts.METHOD_OVERWEIGHT
        if "time limit" in normed:
            return consts.METHOD_TIMELIMIT
        if "exhibit" in normed:
            return consts.METHOD_EXHIBITION
        if (
            normed
            in [
                "fight stopped due to rain",
                "fight ended early due to lightning",
                "canvas too slippery to continue",
            ]
            or "power outage" in normed
        ):
            return consts.METHOD_OUTSIDE_INCIDENT
        if "both" in normed or "double" in normed:
            return consts.METHOD_BOTH
        if (
            "error" in normed
            or "mistake" in normed
            or "thought" in normed
            or "premature" in normed
            or "ring malf" in normed
            or "cage malf" in normed
        ):
            return consts.METHOD_OFFICIAL_ERROR
        if (
            normed in ["round went over time"]
            or "illegal" in normed
            or "foul" in normed
            or "accident" in normed
            or "prohibit" in normed
            or "forbid" in normed
            or "inten" in normed
            or "inadv" in normed
            or "headbut" in normed
            or "groin" in normed
            or "low blow" in normed
            or "poke" in normed
            or "back of" in normed
            or "fell" in normed
            or "soccer" in normed
            or "knee to grounded" in normed
            or "knee to a downed" in normed
            or "knee to downed" in normed
            or "kick to grounded" in normed
            or "head of grounded" in normed
            or "knee to the head" in normed
            or "dropped on head" in normed
            or "lotion" in normed
            or "spine" in normed
            or "grease" in normed
            or "finger in" in normed
            or "thumb in" in normed
            or "hair pull" in normed
            or "unsportsman" in normed
            or "over fight length" in normed
            or "after the bell" in normed
        ):
            return consts.METHOD_FOUL
        if (
            normed in ["cut"]
            or "injur" in normed
            or "medical" in normed
            or "doctor" in normed
            or "due to cut" in normed
            or "cut from" in normed
        ):
            return consts.METHOD_STOPPAGE_DOCTOR
        if (
            normed in [""]
            or "unanimous" in normed
            or "majority" in normed
            or "split" in normed
        ):
            return consts.METHOD_UNKNOWN
        if (
            normed in ["knee", "refusal"]
            or "strikes" in normed
            or "punches" in normed
            or "right" in normed
            or "left" in normed
            or "kick" in normed
            or "choke" in normed
            or "lock" in normed
            or "armbar" in normed
        ):
            return consts.METHOD_OVERWEIGHT
    elif status in [consts.STATUS_WIN, consts.STATUS_LOSS]:
        if "overturn" in normed:
            return consts.METHOD_OVERTURNED
        if "drug" in normed or "doping" in normed:
            return consts.METHOD_DOPING
        if "weight" in normed:
            return consts.METHOD_OVERWEIGHT
        if (
            normed in ["round went over time"]
            or "illegal" in normed
            or "foul" in normed
            or "accident" in normed
            or "prohibit" in normed
            or "disq" in normed
            or "forbid" in normed
            or "inten" in normed
            or "inadv" in normed
            or "headbut" in normed
            or "groin" in normed
            or "biting" in normed
            or "low blow" in normed
            or "poke" in normed
            or "back of" in normed
            or "fell" in normed
            or "unanswer" in normed
            or "knee to grounded" in normed
            or "knee to a downed" in normed
            or "knee to downed" in normed
            or "kick to grounded" in normed
            or "head of grounded" in normed
            or "knee to the head" in normed
            or "dropped on head" in normed
            or "corner interference" in normed
            or "lotion" in normed
            or "spine" in normed
            or "grease" in normed
            or "liability" in normed
            or "finger in" in normed
            or "thumb in" in normed
            or "hair pull" in normed
            or "unsportsman" in normed
            or "over fight length" in normed
            or "did not" in normed
            or "didn't" in normed
            or "failed to" in normed
            or "answer the bell" in normed
            or "answer bell" in normed
            or "after stop" in normed
            or "after the bell" in normed
            or "mouthpiece" in normed
            or "mouth protector" in normed
            or "running from" in normed
        ):
            return consts.METHOD_DQ
        if "corner stop" in normed or "towel" in normed or "refus" in normed:
            return consts.METHOD_STOPPAGE_CORNER
        if (
            normed in ["forehead cut", "cut", "cuts"]
            or "doctor stop" in normed
            or "injury" in normed
            or "medical" in normed
            or "broken" in normed
            or "disloc" in normed
            or "cut on" in normed
            or "cut to" in normed
            or "doctor's stop" in normed
            or "dr. stop" in normed
            or "vomit" in normed
            or "hematoma" in normed
            or "bleeding" in normed
        ):
            return consts.METHOD_STOPPAGE_DOCTOR
        if (
            "retir" in normed
            or "abandon" in normed
            or "exhaust" in normed
            or "unable to continue" in normed
        ):
            return consts.METHOD_RETIREMENT
        if "decision" in normed or normed in ["unanimous", "majority", "split"]:
            if normed == "decision":
                return consts.METHOD_DECISION
            if "una" in normed:
                return consts.METHOD_DECISION_UNANIMOUS
            if "maj" in normed:
                return consts.METHOD_DECISION_MAJORITY
            if "spl" in normed:
                return consts.METHOD_DECISION_SPLIT
            if "point" in normed:
                return consts.METHOD_DECISION_POINTS
        if (
            normed in ["ko/tko", "ko", "tko", "knee"]
            or "pound" in normed
            or "punch" in normed
            or "strik" in normed
            or "kick" in normed
            or "knock" in normed
            or "knees" in normed
            or "jab" in normed
            or "straight" in normed
            or "slam" in normed
            or "stomp" in normed
            or "bomb" in normed
            or "liver" in normed
            or "body" in normed
            or "hooks" in normed
            or "counter" in normed
            or "suplex" in normed
            or "upper" in normed
            or "elbow" in normed
            or "overhand" in normed
            or "fist" in normed
            or "jumping" in normed
            or "flying" in normed
            or "right hand" in normed
            or "left hand" in normed
            or "right hook" in normed
            or "left hook" in normed
            or "right cross" in normed
            or "left cross" in normed
            or "eree stop" in normed
            or "ref stop" in normed
            or "knee &" in normed
            or "knee from" in normed
            or "knee to" in normed
            or "forearms" in normed
            or "pnuch" in normed
            or "punhe" in normed
            or "painful reception" in normed
        ):
            return consts.METHOD_KO_TKO
        if (
            normed in ["submission"]
            or "choke" in normed
            or "lock" in normed
            or "hold" in normed
            or "tap" in normed
            or "bar" in normed
            or "kimura" in normed
            or "crank" in normed
            or "gatame" in normed
            or "americ" in normed
            or "triang" in normed
            or "stretch" in normed
            or "verbal" in normed
            or "anacon" in normed
            or "guillot" in normed
            or "cravat" in normed
            or "heel hook" in normed
            or "heelhook" in normed
            or "neck tie" in normed
            or "necktie" in normed
            or "cross face" in normed
            or "crossface" in normed
            or "twister" in normed
            or "plata" in normed
            or "chin in the eye" in normed
            or "crucifix" in normed
            or "calf slice" in normed
            or "calf crush" in normed
            or "mataleao" in normed
            or "boston crab" in normed
            or "windshield" in normed
            or "can opener" in normed
            or "kmura" in normed
            or "kumura" in normed
        ):
            return consts.METHOD_SUBMISSION
    raise InferError("method", note)
