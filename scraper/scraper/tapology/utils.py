import datetime
import re
from . import consts
from .errors import NormalizeError, ParseError, InferError


def is_na(text: str) -> str:
    normed = normalize_text(text)
    if normed in ["n/a", ""]:
        return True
    return False


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
    if normed in ["loss", "lose"]:
        return consts.STATUS_LOSS
    if normed in ["draw"]:
        return consts.STATUS_DRAW
    if normed in ["cancelled", "cancelled bout"]:
        return consts.STATUS_CANCELLED
    if normed in ["no contest", "overturned to no contest", "nc"]:
        return consts.STATUS_NC
    if normed in ["upcoming", "confirmed upcoming bout"]:
        return consts.STATUS_UPCOMING
    if normed in ["unknown", "n/a", "na"]:
        return consts.STATUS_UNKNOWN
    raise NormalizeError("status", normed)


def normalize_sport(sport: str) -> str:
    normed = normalize_text(sport)
    if normed in consts.SPORTS:
        return normed
    if normed in ["mma", "pancrase", "modified mma"]:
        return consts.SPORT_MMA
    if normed in ["knuckle_mma", "bare knuck mma"]:
        return consts.SPORT_KNUCKLE_MMA
    if normed in [
        "boxing",
        "modified boxing",
    ]:
        return consts.SPORT_BOX
    if normed in [
        "boxing_cage",
        "boxing (cage)",
        "modified boxing (cage)",
    ]:
        return consts.SPORT_CAGE_BOX
    if normed in ["knuckle", "bare knuck box"]:
        return consts.SPORT_KNUCKLE_BOX
    if normed in ["kickboxing", "modified kickboxing"]:
        return consts.SPORT_KICK
    if normed in ["muay", "muay thai", "modified muay thai"]:
        return consts.SPORT_MUAY
    if normed in ["karate", "modified karate"]:
        return consts.SPORT_KARATE
    if normed in ["sanda"]:
        return consts.SPORT_SANDA
    if normed in ["lethwei"]:
        return consts.SPORT_LETHWEI
    if normed in ["grappling", "modified grappling"]:
        return consts.SPORT_GRAPPLE
    if normed in ["shootboxing"]:
        return consts.SPORT_SHOOT
    if normed in ["wrestling"]:
        return consts.SPORT_WRESTLE
    if normed in ["sambo"]:
        return consts.SPORT_SAMBO
    if normed in ["valetudo", "vale tudo"]:
        return consts.SPORT_VALE
    if normed in ["judo"]:
        return consts.SPORT_JUDO
    if normed in ["combat_jj", "combat jiu-jitsu"]:
        return consts.SPORT_COMBAT_JJ
    if normed in ["taekwondo"]:
        return consts.SPORT_TAEK
    if normed in ["slap", "slap fighting"]:
        return consts.SPORT_SLAP
    if normed in ["custom", "custom rules", "modified custom rules"]:
        return consts.SPORT_CUSTOM
    raise NormalizeError("sport", normed)


def normalize_weight_class(weight_class: str) -> str | None:
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
    if normed in ["openweight", "open weight", "open"]:
        return consts.WEIGHT_CLASS_OPEN
    if normed in ["catchweight", "catch weight", "catch"]:
        return consts.WEIGHT_CLASS_CATCH
    raise NormalizeError("weight class", normed)


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
    if normed in ["preliminary card", "prelim"]:
        return consts.BILLING_PRELIM_CARD
    if normed in ["postlim"]:
        return consts.BILLING_POSTLIM_CARD
    raise NormalizeError("billing", normed)


def normalize_division(division: str) -> str:
    normed = normalize_text(division)
    if normed.startswith("pro"):
        return consts.DIVISION_PRO
    if normed.startswith("am"):
        return consts.DIVISION_AM
    raise NormalizeError("division", normed)


def parse_date(date: str) -> str:
    normed = normalize_text(date)
    # 2014.09.09
    matched = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", normed)
    if matched is not None:
        return f"{matched.group(1):04}-{matched.group(2):02}-{matched.group(3):02}"
    # 09.09.2014
    matched = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", normed)
    if matched is not None:
        return f"{matched.group(3):04}-{matched.group(1):02}-{matched.group(2):02}"
    raise ParseError("date", normed)


def normalize_round_format(round_format: str) -> str:
    normed = normalize_text(round_format)

    # 5 x 5 minute rounds
    # 5 x 5 min
    matched = re.match(r"(\d+) x (\d+)", normed)
    if matched is not None:
        format = "-".join([matched.group(2) for _ in range(int(matched.group(1)))])
        return format

    # 5 min one round
    matched = re.match(r"(\d+) min one round$", normed)
    if matched is not None:
        format = matched.group(1)
        return format

    # 5 min round plus overtime
    matched = re.match(r"(\d+) min round plus overtime$", normed)
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
    matched = re.match(r"(\d+(?:\-\d+)+)( plus overtime)?", normed)
    if matched is not None:
        format = matched.group(1)
        if matched.group(2) is not None:
            format += "-ot"
        return format

    # 5 + 5 two rounds
    # 5 + 5 + 5 three rounds
    matched = re.match(r"(\d+(?: \+ \d+)+)", normed)
    if matched is not None:
        format = "-".join(list(map(lambda x: x.strip(), matched.group(1).split("+"))))
        return format

    # 5 min unlim rounds
    matched = re.match(r"(\d+) min unlim rounds", normed)
    if matched is not None:
        format = matched.group(1) + "-*"
        return format

    # 1 Round, No Limit
    if normed == "1 round, no limit":
        return "*"

    # 3 Rounds
    matched = re.match(r"(\d+) rounds", normed)
    if matched is not None:
        return "-".join(["?"] * int(matched.group(1)))
    raise NormalizeError("round format", normed)


def parse_round_time(round_time: str) -> dict[str, int]:
    normed = normalize_text(round_time)
    matched = re.match(r"^(\d+):(\d+)$", normed)
    if matched is not None:
        return {"m": int(matched.group(1)), "s": int(matched.group(2))}
    raise ParseError("round time", normed)


def parse_round(round: str) -> int:
    normed = normalize_text(round)
    matched = re.match(r"r(\d+)", normed)
    if matched is not None:
        return int(matched.group(1))
    raise ParseError("round", normed)


def parse_nickname(nickname: str) -> str:
    normed = normalize_text(nickname)
    matched = re.match(r"\"(.+)\"", normed)
    if matched is not None:
        return matched.group(1)
    raise ParseError("nickname", normed)


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
    raise ParseError("title info", normed)


def parse_odds(odds: str) -> float:
    normed = normalize_text(odds)

    # +210 · Moderate Underdog
    # 0 · Close
    matched = re.search(r"([\+\-])?([\d\.]+)", normed)
    if matched is not None:
        value = float(matched.group(2))
        sign = matched.group(1)
        if sign == "-":
            value *= -1
        return (value / 100) + 1.0
    raise ParseError("odds", normed)


def parse_end_time(end_time: str) -> dict:
    normed = normalize_text(end_time)
    # 1:44 round 1 of 3
    # 0:56 round 3 of 3, 10:56 total
    # 3:09 round 2, 18:09 total
    # 2:20 round 3
    # round 3 of 5
    # round 2 of 3, 3:00 total
    matched = re.match(
        r"(?:(\d+:\d+) )?round (\d+)(?: of \d+)?(?:, (\d+:\d+) total)?", normed
    )
    if matched is not None:
        round_time = matched.group(1)
        round = int(matched.group(2))
        elapsed_time = matched.group(3)
        if round_time is not None and elapsed_time is not None:
            return {"round": round, "time": round_time, "elapsed": elapsed_time}
        elif round_time is not None and elapsed_time is None:
            if round == 1:
                return {"round": round, "time": round_time, "elapsed": round_time}
            return {"round": round, "time": round_time}
        elif round_time is None and elapsed_time is None:
            return {"round": round}
        elif round_time is None and elapsed_time is not None:
            return {"round": round, "elapsed": elapsed_time}
    # 5 rounds, 25:00 total
    # 1 round, 10:00 total
    # 1 round
    # 2 rounds
    matched = re.match(r"(\d+) rounds?(?:, (\d+:\d+) total)?", normed)
    if matched is not None:
        round = int(matched.group(1))
        elapsed_time = matched.group(2)
        if elapsed_time is not None:
            return {"round": round, "elapsed": elapsed_time}
        return {"round": round}
    # 1:31 round 8/10, 22:31 total
    matched = re.match(r"(\d+:\d+) round (\d+)/\d+, (\d+:\d+) total", normed)
    if matched is not None:
        round_time = matched.group(1)
        round = int(matched.group(2))
        elapsed_time = matched.group(3)
        return {"round": round, "time": round_time, "elapsed": elapsed_time}
    # round 1
    # round 3
    matched = re.match(r"round (\d+)", normed)
    if matched is not None:
        round = int(matched.group(1))
        return {"round": round}

    # rounds, 15:00 total
    matched = re.match(r"rounds, (\d+:\d+) total", normed)
    if matched is not None:
        elapsed_time = matched.group(1)
        return {"elapsed": elapsed_time}
    raise ParseError("end time", normed)


def parse_weight_summary(weight_summary: str) -> dict[str, float]:
    normed = normalize_text(weight_summary)
    normed_split = list(map(lambda x: x.strip(), normed.split("·")))
    ret = {}

    # Heavyweight
    # *numeric weight*
    # 110 kg|kgs|lb|lbs
    # 110 kg|kgs|lb|lbs (49.9 kg|kgs|lb|lbs)
    matched = re.match(r"(.*weight|([\d\.]+) (kgs?|lbs?))", normed_split[0])
    if matched is None:
        raise ParseError("weight summary", normed)
    if matched.group(1) == "*numeric weight":
        pass
    elif matched.group(2) is not None and matched.group(3) is not None:
        value, unit = float(matched.group(2)), matched.group(3)
        ret["class"] = to_weight_class(value, unit=unit)
        ret["limit"] = to_kg(value, unit=unit)
    else:
        try:
            ret["class"] = normalize_weight_class(matched.group(1))
        except NormalizeError as e:
            raise ParseError("weight summary", normed) from e
    for s in normed_split[1:]:
        # 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        # Weigh-In 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        matched = re.match(r"(weigh-in )?([\d\.]+) (kgs?|lbs?)", s)
        if matched is None:
            raise ParseError("weight summary", normed)
        if matched.group(2) is None or matched.group(3) is None:
            raise ParseError("weight summary", normed)
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
        raise ParseError("weight summary", normed)
    return ret


def get_id_from_url(url: str) -> str:
    return url.split("/")[-1]


def parse_last_weigh_in(last_weigh_in: str) -> float:
    normed = normalize_text(last_weigh_in)
    matched = re.match(r"([\d\.]+) (kgs?|lbs?)", normed)
    if matched is not None:
        value = float(matched.group(1))
        unit = matched.group(2)
        return to_kg(value, unit=unit)
    raise ParseError("last weigh-in", normed)


def parse_height(height: str) -> float:
    normed = normalize_text(height)
    matched = re.search(r"([\d\.]+)\'([\d\.]+)\"", normed)
    if matched is not None:
        return to_meter(float(matched.group(1)), float(matched.group(2)))
    raise ParseError("height", normed)


def parse_reach(reach: str) -> float:
    normed = normalize_text(reach)
    matched = re.search(r"([\d\.]+)\"", normed)
    if matched is not None:
        return to_meter(0, float(matched.group(1)))
    raise ParseError("reach", normed)


def parse_earnings(earnings: str) -> int:
    normed = normalize_text(earnings)
    matched = re.search(r"\$([\d\,]+)", normed)
    if matched is not None:
        return int(matched.group(1).replace(",", ""))
    raise ParseError("earnings", normed)


def parse_method(method: str) -> dict:
    normed = normalize_text(method)
    normed_split = list(map(lambda x: x.strip(), normed.split(",")))
    n = len(normed_split)
    cat = normed_split[0]
    by = "unknown" if n == 1 else ",".join(normed_split[1:])
    if cat.startswith("ko/tko"):
        return {"type": consts.METHOD_TYPE_KO_TKO, "by": by}
    elif cat.startswith("submission"):
        return {"type": consts.METHOD_TYPE_SUBMISSION, "by": by}
    elif cat.startswith("decision"):
        if re.search(r"unanimous", by):
            return {"type": consts.METHOD_TYPE_DECISION, "by": "unanimous"}
        if re.search(r"majority", by):
            return {"type": consts.METHOD_TYPE_DECISION, "by": "majority"}
        if re.search(r"(split|spit|spilt)", by):
            return {"type": consts.METHOD_TYPE_DECISION, "by": "split"}
        return {"type": consts.METHOD_TYPE_DECISION, "by": by}
    elif cat.startswith("ends in a draw"):
        if re.search(r"unanimous", by):
            return {"type": consts.METHOD_TYPE_DRAW, "by": "unanimous"}
        if re.search(r"majority", by):
            return {"type": consts.METHOD_TYPE_DRAW, "by": "majority"}
        if re.search(r"(split|spit|spilt)", by):
            return {"type": consts.METHOD_TYPE_DRAW, "by": "split"}
        return {"type": consts.METHOD_TYPE_DRAW, "by": by}
    elif cat.startswith("ends in a no contest"):
        if re.search(r"unanimous", by):
            return {"type": consts.METHOD_TYPE_NC, "by": "unanimous"}
        if re.search(r"majority", by):
            return {"type": consts.METHOD_TYPE_NC, "by": "majority"}
        if re.search(r"(split|spit|spilt)", by):
            return {"type": consts.METHOD_TYPE_NC, "by": "split"}
        if is_doping(by):
            return {"type": consts.METHOD_TYPE_NC, "by": "doping"}
        return {"type": consts.METHOD_TYPE_NC, "by": by}
    elif cat.startswith("disqualificaton"):
        if re.search(r"unanimous", by):
            return {"type": consts.METHOD_TYPE_DQ, "by": "unanimous"}
        if re.search(r"majority", by):
            return {"type": consts.METHOD_TYPE_DQ, "by": "majority"}
        if re.search(r"(split|spit|spilt)", by):
            return {"type": consts.METHOD_TYPE_DQ, "by": "split"}
        if is_doping(by):
            return {"type": consts.METHOD_TYPE_DQ, "by": "doping"}
        return {"type": consts.METHOD_TYPE_DQ, "by": by}
    elif cat in ["overturned to no contest", "result overturned"]:
        return {"type": consts.METHOD_TYPE_OVERTURNED, "by": by}
    elif cat == "n/a":
        return {"type": consts.METHOD_TYPE_OTHERS, "by": by}
    elif cat == "result unknown":
        return {"type": consts.METHOD_TYPE_UNKNOWN, "by": by}
    raise ParseError("method", normed)


def parse_record(record: str) -> dict[str, int]:
    normed = normalize_text(record)
    matched = re.match(
        r"^(?:climbed to |fell to |moved to |stayed at )?(\d+)-(\d+)(?:-(\d+))?", normed
    )
    if matched is not None:
        d = matched.group(3)
        return {
            "w": int(matched.group(1)),
            "l": int(matched.group(2)),
            "d": 0 if d is None else int(d),
        }
    raise ParseError("record", normed)


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
    if weight_class == consts.WEIGHT_CLASS_OPEN:
        return None
    if weight_class == consts.WEIGHT_CLASS_CATCH:
        return None
    return consts.WEIGHT_LIMIT_S_HEAVY


def to_meter(feet: float, inch: float) -> float:
    return feet * 0.3048 + inch * 0.0254


def to_kg(value: float, unit: str = "lb") -> float:
    if unit not in ["kg", "kgs", "lb", "lbs"]:
        raise ValueError(f"Unsupported unit: {unit}")
    if unit.startswith("lb"):
        return value * 0.453592
    return value


match_url_correction_map = {
    "759886-nfc-14-david-balevski-vs-milan-markovic": "759886-nfc-14-david-balevski-vs-milan-nemanja-markovic",
    "811882-fantom-bull-fight-2-dominik-janikowski-vs-kamil-smetoch": "811882-fantom-bull-fight-2-kamil-smetoch-vs-dominik-janikowski",
    "195851-acamm-fight-nights-juan-david-bohorquez-vs-gabriel-tanaka-quintero": "195851-acamm-juan-david-bohorquez-vs-gabriel-tanaka-quintero",
    "189527-fmp-fight-night-paulino-siller-vs-neri-garcia": "189527-fmp-fight-night-paulino-el-cuate-siller-vs-neri-antonio-garcia",
    "807702-gemmaf-deutsche-meisterschaften-2023-emir-can-the-turkish-bull-al-vs-devid-bondarenko": "825639-german-amateur-mma-chamiponship-2023-emir-can-the-turkish-bull-al-vs-devid-bondarenko",
    "706957-ffc-5-matej-batinic-vs-attila-petrovszki": "818510-final-fight-championship-5-matej-batinic-vs-attila-petrovszki",
    "800525-superior-challenge-26-ederson-cristian-lion-macedo-vs-king-karl-albrektsson": "800525-superior-challenge-26-king-karl-albrektsson-vs-ederson-cristian-lion-macedo",
    "790690-combate-global-killer-kade-kottenbrook-vs-michel-martinez": "790690-combate-global-michel-martinez-vs-killer-kade-kottenbrook",
    "750457-wlf-mma-63-lilierqian-vs-jianbing-mao": "750457-wlf-mma-63-lilierqian-li-vs-jianbing-mao",
    "546185-ffc-ernis-abdulakim-uulu-vs-shaykhdin-ismailov": "546185-ffc-ernis-abdilakim-uulu-vs-shaykhdin-ismailov",
    "801729-uae-warriors-40-sabriye-the-turkish-fighter-sengul-vs-mena-mohamed-abdallah": "742402-uae-warriors-40-sabriye-the-turkish-fighter-sengul-vs-mena-allah-mohamed-abdalah",
    "629589-desert-brawl-trent-the-sandman-standing-vs-shawn-petty": "629589-desert-brawl-16-trent-the-sandman-standing-vs-shawn-petty",
    "774497-aca-young-eagles-37-ruslan-bulguchev-vs-mukhammad-urusov": "774497-aca-young-eagles-37-mukhammad-urusov-vs-ruslan-bulguchev",
    "459896-ultimax-fight-night-beksultan-beka-omurzakov-vs-bilal-aliev": "459896-ultimax-fc-6-beksultan-beka-omurzakov-vs-bilal-aliev",
    "365522-mfp-solomon-demin-vs-alexander-gubkin": "365522-mfp-solomon-kane-demin-vs-alexander-gubkin",
    "780518-open-fight-latam-victor-candia-vs-eric-sanchez": "780518-open-fight-latam-5-victor-el-loco-candia-vs-eric-sanchez",
    "704071-kok-world-series-in-kaunas-jussi-pirttikangas-vs-erikas-golubovskis": "704071-kok-world-series-in-kaunas-erikas-golubovskis-vs-jussi-pirttikangas",
    "807699-gemmaf-deutsche-meisterschaften-2023-markus-kronenberger-vs-joel-steinhoff": "825589-german-amateur-mma-chamiponship-2023-markus-kronenberger-vs-joel-steinhoff",
    "807687-gemmaf-deutsche-meisterschaften-2023-emir-can-the-turkish-bull-al-vs-marian-schneider": "825624-german-amateur-mma-chamiponship-2023-emir-can-the-turkish-bull-al-vs-marian-schneider",
    "807701-gemmaf-deutsche-meisterschaften-2023-marian-schneider-vs-soren-holthausen": "825587-german-amateur-mma-chamiponship-2023-marian-schneider-vs-soren-holthausen",
    "807690-gemmaf-deutsche-meisterschaften-2023-devid-bondarenko-vs-markus-kronenberger": "825625-german-amateur-mma-chamiponship-2023-devid-bondarenko-vs-markus-kronenberger",
    "807686-gemmaf-deutsche-meisterschaften-2023-emir-can-the-turkish-bull-al-vs-vincent-zymaj": "825586-german-amateur-mma-chamiponship-2023-emir-can-the-turkish-bull-al-vs-vincent-zymaj",
    "807694-gemmaf-deutsche-meisterschaften-2023-devid-bondarenko-vs-daniel-luthardt": "825588-german-amateur-mma-chamiponship-2023-devid-bondarenko-vs-daniel-luthardt",
    "618351-atf-5-sherzod-yuldashev-vs-sherzod-irgashev": "824387-atf-5-shakhzod-yoldashev-vs-shakhzod-ergashev",
    "459901-ultimax-fight-night-vyacheslav-gagiev-vs-sahil-mirzaev": "459901-ultimax-fc-6-vyacheslav-gagiev-vs-sahil-mirzaev",
    "793348-grachan-65-daiki-asahina-vs-atsushi-makigaya": "793348-grachan-65-atsushi-makigaya-vs-daiki-asahina",
    "807467-wlf-mma-69-yuele-huang-vs-reginaldo-vieira": "807467-wlf-mma-69-reginaldo-vieira-vs-yuele-huang",
    "459901-ultimax-fight-night-vyacheslav-gagiev-vs-sahil-mirzaev": "459901-ultimax-fc-6-vyacheslav-gagiev-vs-sahil-mirzaev",
    "538885-wlf-w-a-r-s-40-shuai-zhang-vs-xionghui-zhou": "828898-wlf-w-a-r-s-40-shuai-zhang-vs-xionghui-zhou",
    "824222-caestus-mma-marc-webster-vs-yakup-kurt": "828551-caestus-mma-marcus-webster-vs-yakup-kurt",
    "782459-open-fight-latam-pedro-gonzalez-vs-diego-tejon-alvarez": "782459-open-fight-latam-5-pedro-gonzalez-vs-diego-tejon-alvarez",
    "459763-ultimax-fight-night-rufani-valiev-vs-hamid-eftekhari": "459763-ultimax-fc-6-rufani-black-borz-valiev-vs-hamid-eftekhari",
    "770517-aba-fighting-championship-sulangrangbo-vs-baofu-li": "770517-aba-fighting-championship-sulangrangbo-sulang-vs-baofu-li",
    "391689-mfp-224-kiril-soloviev-vs-usman-sherkhonov": "391689-mfp-224-usmon-sherkhonov-vs-kiril-antikiller-soloviev",
    "378670-mfp-222-vasily-atlasov-vs-kiril-soloviev": "378670-mfp-222-vasily-atlasov-vs-kiril-antikiller-soloviev",
    "808147-gemmaf-deutsche-meisterschaften-2023-martin-horsch-vs-lukas-sundi": "825613-german-amateur-mma-chamiponship-2023-martin-horsch-vs-lukas-sundi",
}


def correct_match_url(match_url: str) -> str:
    match_id = match_url.split("/")[-1]
    if match_id not in match_url_correction_map:
        return match_url
    corrected = match_url_correction_map[match_id]
    body = match_url.split("/")[:-1]
    body.append(corrected)
    return "/".join(body)


event_url_correction_map = {
    "106352-gemmaf-deutsche-meisterschaften-2023-day-1": "108242-german-amateur-mma-chamiponship-2023-seniors",
    "95012-ffc-5": "19563-final-fight-championship-5-rodriguez-vs-simonic",
}


def correct_event_url(event_url: str) -> str:
    event_id = event_url.split("/")[-1]
    if event_id not in event_url_correction_map:
        return event_url
    corrected = event_url_correction_map[event_id]
    body = event_url.split("/")[:-1]
    body.append(corrected)
    return "/".join(body)


def is_doping(by: str) -> bool:
    normed = normalize_text(by)
    if re.search(r"(drug|doping|substance)", normed):
        return True
    return False
