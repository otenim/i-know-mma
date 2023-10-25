import scrapy
import re
from scrapy.http import Request, TextResponse
from scrapy.selector import Selector, SelectorList
from collections.abc import Generator
from typing import List, Union, Dict, Optional


# Weight Limits (MMA)
WEIGHT_LIMIT_ATOM = 47.6272
WEIGHT_LIMIT_STRAW = 52.1631
WEIGHT_LIMIT_FLY = 56.699
WEIGHT_LIMIT_BANTAM = 61.235
WEIGHT_LIMIT_FEATHER = 65.7709
WEIGHT_LIMIT_LIGHT = 70.3068
WEIGHT_LIMIT_WELTER = 77.1107
WEIGHT_LIMIT_MIDDLE = 83.9146
WEIGHT_LIMIT_LIGHT_HEAVY = 92.9864
WEIGHT_LIMIT_HEAVY = 120.202


# Weight Classes (MMA)
WEIGHT_CLASS_ATOM = "atom"
WEIGHT_CLASS_STRAW = "straw"
WEIGHT_CLASS_FLY = "fly"
WEIGHT_CLASS_BANTAM = "bantam"
WEIGHT_CLASS_FEATHER = "feather"
WEIGHT_CLASS_LIGHT = "light"
WEIGHT_CLASS_WELTER = "welter"
WEIGHT_CLASS_MIDDLE = "middle"
WEIGHT_CLASS_LIGHT_HEAVY = "light_heavy"
WEIGHT_CLASS_HEAVY = "heavy"
WEIGHT_CLASS_SUPER_HEAVY = "super_heavy"


# Sport
SPORT_MMA = "mma"
SPORT_KNUCKLE_MMA = "knuckle_mma"
SPORT_BOX = "box"
SPORT_KNUCKLE_BOX = "knuckle_box"
SPORT_KICK = "kick"
SPORT_MUAY = "muay"
SPORT_KARATE = "karate"
SPORT_SANDA = "sanda"
SPORT_LETHWEI = "lethwei"
SPORT_GRAPPLE = "grapple"
SPORT_SHOOT = "shoot"
SPORT_WRESTLE = "wrestle"
SPORT_SAMBO = "sambo"
SPORT_VALE = "vale"
SPORT_JUDO = "judo"
SPORT_CUSTOM = "custom"


# Expected values for bout's sport
VALUES_SPORT_MMA = ["mma"]
VALUES_SPORT_KNUCKLE_MMA = ["knuckle_mma"]
VALUES_SPORT_BOX = ["boxing", "boxing_cage"]
VALUES_SPORT_KNUCKLE_BOX = ["knuckle"]
VALUES_SPORT_KICK = ["kickboxing"]
VALUES_SPORT_MUAY = ["muay"]
VALUES_SPORT_KARATE = ["karate"]
VALUES_SPORT_SANDA = ["sanda"]
VALUES_SPORT_LETHWEI = ["lethwei"]
VALUES_SPORT_GRAPPLE = ["grappling"]
VALUES_SPORT_SHOOT = ["shootboxing"]
VALUES_SPORT_WRESTLE = ["wrestling"]
VALUES_SPORT_SAMBO = ["sambo"]
VALUES_SPORT_VALE = ["valetudo"]
VALUES_SPORT_JUDO = ["judo"]
VALUES_SPORT_CUSTOM = ["custom"]


# Bout's status
STATUS_WIN = "win"
STATUS_LOSS = "loss"
STATUS_CANCELLED = "cancelled"
STATUS_DRAW = "draw"
STATUS_UPCOMING = "upcoming"
STATUS_NO_CONTEST = "no_contest"
STATUS_UNKNOWN = "unknown"


# Expected values for bout's status
VALUES_STATUS_WIN = ["win", "won", "w"]
VALUES_STATUS_LOSS = ["loss", "lose", "lost", "l"]
VALUES_STATUS_CANCELLED = ["cancelled", "c"]
VALUES_STATUS_DRAW = ["draw", "d"]
VALUES_STATUS_UPCOMING = ["upcoming"]
VALUES_STATUS_NO_CONTEST = ["no contest", "no_contest", "nocontest"]
VALUES_STATUS_UNKNOWN = ["unknown"]


# Configs
STATUS_TO_SKIP = [
    STATUS_CANCELLED,
    STATUS_UPCOMING,
    STATUS_NO_CONTEST,
    STATUS_UNKNOWN,
]
SPORTS_TO_SKIP = [SPORT_CUSTOM]
SKIP_AMATEUR_FIGHTERS = True
SKIP_INEXPERIENCED_FIGHTERS = True
MINIMUM_PRO_MMA_BOUT_COUNT_REQUIRED = 3


class FightersSpider(scrapy.Spider):
    name = "fighters"
    start_urls = ["https://www.tapology.com/search"]

    def parse(self, response: TextResponse) -> Generator[Request, None, None]:
        urls = response.xpath(
            "//div[@class='siteSearchFightersByWeightClass']/dd/a/@href"
        ).getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_fighter_list)

    def parse_fighter_list(
        self, response: TextResponse
    ) -> Generator[Request, None, None]:
        fighters = response.xpath("//table[@class='siteSearchResults']/tr")[1:]
        for fighter in fighters:
            record = fighter.xpath("./td[7]/text()[normalize-space()]").get()
            if record is None:
                self.logger.error(
                    "Unexpected page structure: could not find the mma record column on the fighters' list"
                )
                continue
            matched = re.match(r"^(?:(Am) )?(\d+)-(\d+)-(\d+)(?:, \d+ NC)?$", record)
            if matched is None:
                self.logger.error(f"Unexpected mma record format was found: {record}")
                continue
            if (SKIP_INEXPERIENCED_FIGHTERS or SKIP_AMATEUR_FIGHTERS) and matched.group(
                1
            ) == "Am":
                continue
            if (
                SKIP_INEXPERIENCED_FIGHTERS
                and sum(
                    [
                        int(matched.group(2)),
                        int(matched.group(3)),
                        int(matched.group(4)),
                    ]
                )
                < MINIMUM_PRO_MMA_BOUT_COUNT_REQUIRED
            ):
                continue
            url = fighter.xpath("./td[1]/a/@href").get()
            if url is not None:
                yield response.follow(url, callback=self.parse_fighter)

        # To the next page
        next_url = response.xpath(
            "//span[@class='moreLink']/nav[@class='pagination']/span[@class='next']/a/@href"
        ).get()
        if next_url is not None:
            yield response.follow(next_url, callback=self.parse_fighter_list)

    def parse_fighter(self, response: TextResponse):
        ret = {}

        # Fighter url (must)
        # NOTE: response.url is never None
        ret["url"] = response.url

        # Fighter name (must)
        name = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h1[not(@*)]/text()[normalize-space()]"
        ).get()
        if name is None:
            self.logger.error(
                "Unexpected page structure: could not find the fighter's name"
            )
            return
        ret["name"] = name

        ###########################################################
        #
        # Scrape fighter's profile
        #
        ###########################################################
        # Stores fighter's profile
        profile = {}

        # Fighter's nickname (optional)
        nickname = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h4[@class='preTitle nickname']/text()[normalize-space()]"
        ).re_first(r"^\"(.*)\"$")
        if nickname is not None:
            profile["nickname"] = nickname

        # The section which stores fighter's profile data (must)
        profile_section = response.xpath("//div[@class='details details_two_columns']")
        if len(profile_section) == 0:
            self.logger.error(
                "Unexpected page structure: could not find the profile section"
            )
            return

        # Date of birth (optional)
        date_of_birth = profile_section.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()[normalize-space()]"
        ).re(r"^(\d+)\.(\d+)\.(\d+)$")
        if len(date_of_birth) == 3:
            profile["date_of_birth"] = {
                "y": int(date_of_birth[0]),
                "m": int(date_of_birth[1]),
                "d": int(date_of_birth[2]),
            }

        # Weight class (optional)
        weight_class = profile_section.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if weight_class:
            normed = normalize_weight_class(weight_class)
            if normed is not None:
                profile["weight_class"] = normed
            else:
                self.logger.error(f"Unexpected weight class was found: {weight_class}")

        # Affiliation (optional)
        affili_section = profile_section.xpath(
            "./ul/li/strong[text()='Affiliation:']/following-sibling::span[1]/a"
        )
        if len(affili_section) == 1:
            url = affili_section.xpath("./@href").get()
            if url is not None:
                name = affili_section.xpath("./text()[normalize-space()]").get()
                if name is not None:
                    profile["affiliation"] = {
                        "url": url,
                        "name": name,
                    }

        # Height (optional)
        # Format: "5\'9\" (175cm)"
        height = profile_section.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()[normalize-space()]"
        ).re(r"^([\d\.]+)\'([\d\.]+)\"")
        if len(height) == 2:
            profile["height"] = to_meter(float(height[0]), float(height[1]))

        # Reach (optional)
        # Format: "74.0\" (188cm)"
        reach = profile_section.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()[normalize-space()]"
        ).re(r"^([\d\.]+)\"")
        if len(reach) == 1:
            profile["reach"] = to_meter(0, float(reach[0]))

        # Place of birth (optional)
        place_of_birth = profile_section.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if place_of_birth is not None and place_of_birth != "N/A":
            profile["place_of_birth"] = []
            for p in place_of_birth.split(","):
                profile["place_of_birth"].append(p.strip())

        # Fighting out of (optional)
        # TODO: Clarify the difference place_of_birth vs out_of
        out_of = profile_section.xpath(
            "./ul/li/strong[text()='Fighting out of:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if out_of is not None and out_of != "N/A":
            profile["out_of"] = []
            for o in out_of.split(","):
                profile["out_of"].append(o.strip())

        # College (optional)
        college = profile_section.xpath(
            "./ul/li/strong[text()='College:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if college is not None and college != "N/A":
            profile["college"] = college

        # Foundation styles (optional)
        styles = profile_section.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if styles is not None and styles != "N/A":
            profile["foundation_styles"] = []
            for s in styles.split(","):
                profile["foundation_styles"].append(s.strip())

        # Head Coach (optional)
        head_coach = profile_section.xpath(
            "./ul/li/strong[text()='Head Coach:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if head_coach is not None and normalize_string(head_coach) != "n/a":
            profile["head_coach"] = head_coach

        # Other Coaches (optional)
        other_coaches = profile_section.xpath(
            "./ul/li/strong[text()='Other Coaches:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if other_coaches is not None and normalize_string(other_coaches) != "n/a":
            profile["other_coaches"] = []
            for c in other_coaches.split(","):
                profile["other_coaches"].append(c.strip())

        # Set profile to the output dict
        ret["profile"] = profile

        ###########################################################
        #
        # Scrape pro bout records
        #
        ###########################################################
        pro_record_sections = response.xpath(
            "//section[@class='fighterFightResults']/ul[@id='proResults']/li"
        )
        if len(pro_record_sections) > 0:
            ret["pro_records"] = []
            for pro_record_section in pro_record_sections:
                # Stores a single bout data
                item = {}

                # NOTE: Skip ineligible bouts
                non_mma = pro_record_section.xpath(
                    "./div[@class='result']/div[@class='opponent']/div[@class='record nonMma']/text()[normalize-space()]"
                ).get()
                if non_mma is not None and non_mma.startswith("Record Ineligible"):
                    continue

                # Sport of the bout (must)
                sport = pro_record_section.xpath("./@data-sport").get()
                if sport is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the sport of the bout"
                    )
                    continue
                normed_sport = normalize_sport(sport)
                if normed_sport is None:
                    self.logger.error(f"Unexpected sport value was found: {sport}")
                    continue
                if normed_sport in SPORTS_TO_SKIP:
                    continue
                item["sport"] = normed_sport

                # Status of the bout (must)
                status = pro_record_section.xpath("./@data-status").get()
                if status is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the status of the bout"
                    )
                    continue
                normed_status = normalize_status(status)
                if normed_status is None:
                    self.logger.error(f"Unexpected status value was found: {status}")
                    continue
                if normed_status in STATUS_TO_SKIP:
                    continue
                item["status"] = normed_status

                # Opponent fighter (must)
                opponent_section = pro_record_section.xpath(
                    "./div[@class='result']/div[@class='opponent']"
                )
                if len(opponent_section) == 0:
                    self.logger.error(
                        "Unexpected page structure: could not find any opponent data"
                    )
                    continue
                item["opponent"] = {}

                # Opponent's name (at least name must be provided)
                a = opponent_section.xpath("./div[@class='name']/a")
                has_opponent_url = False if len(a) == 0 else True
                if has_opponent_url:
                    url = a.xpath("./@href").get()
                    name = a.xpath("./text()[normalize-space()]").get()
                    if url is not None:
                        item["opponent"]["url"] = url
                    if name is not None:
                        item["opponent"]["name"] = name
                else:
                    name = opponent_section.xpath(
                        "./div[@class='name']/span/text()[normalize-space()]"
                    ).get()
                    if name is None:
                        self.logger.error(
                            "Unexpected page structure: could not find opponent's name"
                        )
                        continue
                    item["opponent"]["name"] = name

                # Record before the fight (optional)
                # NOTE: available when the bout is not tagged as "nonMma"
                # and its status is not "cancelled"
                if non_mma is None and normed_status != STATUS_CANCELLED:
                    section = opponent_section.xpath("./div[@class='record']")
                    fighter_record = section.xpath(
                        "./span[@title='Fighter Record Before Fight']/text()[normalize-space()]"
                    ).re(r"(\d+)-(\d+)-(\d+)")
                    if len(fighter_record) == 3:
                        item["record_before"] = {
                            "w": int(fighter_record[0].strip()),
                            "l": int(fighter_record[1].strip()),
                            "d": int(fighter_record[2].strip()),
                        }

                    # NOTE: Opponent record is available
                    # when the opponent name has a link
                    if has_opponent_url:
                        opponent_record = section.xpath(
                            "./span[@title='Opponent Record Before Fight']/text()[normalize-space()]"
                        ).re(r"(\d+)-(\d+)-(\d+)")
                        if len(opponent_record) == 3:
                            item["opponent"]["record_before"] = {
                                "w": int(opponent_record[0].strip()),
                                "l": int(opponent_record[1].strip()),
                                "d": int(opponent_record[2].strip()),
                            }

                # Bout summary (optional)
                # NOTE: For now, scrape only mma bouts (not tagged as "nonMma")
                # with status win or loss
                if non_mma is None and normed_status in [STATUS_WIN, STATUS_LOSS]:
                    lead_section = pro_record_section.xpath(
                        "./div[@class='result']/div[@class='summary']/div[@class='lead']"
                    )
                    if len(lead_section) == 0:
                        self.logger.error(
                            "Unexpected page structure: could not find summary lead section"
                        )
                    else:
                        lead = lead_section.xpath("./a/text()[normalize-space()]").get()
                        if lead is None:
                            lead = lead_section.xpath(
                                "./text()[normalize-space()]"
                            ).get()
                        if lead is None:
                            self.logger.error(
                                "Unexpected page structure: could not find summary lead text"
                            )
                        else:
                            l = list(
                                filter(
                                    lambda x: x != "",
                                    map(lambda x: x.strip(), lead.split("·")),
                                )
                            )
                            n = len(l)
                            if not (1 <= n <= 4):
                                self.logger.error(
                                    f"Unexpected format of summary lead text: {lead}"
                                )
                            else:
                                if n != 1:
                                    item["details"] = {}
                                    if n == 2:
                                        # (Win|Loss), Finish
                                        item["details"]["ended_by"] = {
                                            "type": infer(l[1]),
                                            "detail": l[1],
                                        }
                                    elif n == 3:
                                        # (Win|Loss), Finish, Round
                                        # (Win|Loss), Decision, (Majority|Unanimous|Split)
                                        t = infer(l[1])
                                        if t == "decision":
                                            item["details"]["ended_by"] = {
                                                "type": t,
                                                "detail": l[2],
                                            }
                                        else:
                                            item["details"]["ended_by"] = {
                                                "type": t,
                                                "detail": l[1],
                                            }
                                            r = parse_round(l[2])
                                            if r is not None:
                                                item["details"]["ended_at"] = {
                                                    "round": r
                                                }
                                    elif n == 4:
                                        # (Win|Loss), Finish, Time, Round
                                        item["details"]["ended_by"] = {
                                            "type": infer(l[1]),
                                            "detail": l[1],
                                        }
                                        r, t = parse_round(l[3]), parse_time(l[2])
                                        if r is not None or t is not None:
                                            item["details"]["ended_at"] = {}
                                            if r is not None:
                                                item["details"]["ended_at"]["round"] = r
                                            if t is not None:
                                                item["details"]["ended_at"]["time"] = t

                # Bout details
                # NOTE: For now, scrape only mma bouts (not tagged as "nonMma")
                # with status win or loss
                if non_mma is None and normed_status in [STATUS_WIN, STATUS_LOSS]:
                    label_sections = pro_record_section.xpath(
                        "./div[@class='details tall']/div[@class='div']/span[@class='label']"
                    )
                    for label_section in label_sections:
                        label = label_section.xpath("./text()[normalize-space()]").get()
                        if label is None:
                            continue
                        label = label.strip()
                        if label == "Billing:":
                            # "Main Event", "Main Card", "Preliminary Card"
                            billing = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if billing:
                                item["billing"] = billing.strip()
                        elif label == "Duration:":
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if txt:
                                duration = parse_duration(txt)
                                if duration:
                                    item["duration"] = duration
                                else:
                                    self.logger.error(
                                        f"Unexpected format of duration section: {txt}"
                                    )
                        elif label == "Referee:":
                            referee = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if referee:
                                item["referee"] = referee.strip()
                        elif label == "Weight:":
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if txt:
                                weight = parse_weight(txt)
                                if weight:
                                    item["weight"] = weight
                                else:
                                    self.logger.error(
                                        f"Unexpected format of weight section: {txt}"
                                    )
                ret["pro_records"].append(item)
        return ret


def normalize_string(s: str, lower: bool = True) -> str:
    temp = " ".join(s.split())
    if lower:
        temp = temp.lower()
    return temp


def normalize_status(status: str) -> Union[str, None]:
    normed = normalize_string(status)
    if normed in VALUES_STATUS_WIN:
        return STATUS_WIN
    if normed in VALUES_STATUS_LOSS:
        return STATUS_LOSS
    if normed in VALUES_STATUS_DRAW:
        return STATUS_DRAW
    if normed in VALUES_STATUS_CANCELLED:
        return STATUS_CANCELLED
    if normed in VALUES_STATUS_NO_CONTEST:
        return STATUS_NO_CONTEST
    if normed in VALUES_STATUS_UPCOMING:
        return STATUS_UPCOMING
    if normed in VALUES_STATUS_UNKNOWN:
        return STATUS_UNKNOWN
    return None


def normalize_sport(sport: str) -> Union[str, None]:
    normed = normalize_string(sport)
    if normed in VALUES_SPORT_MMA:
        return SPORT_MMA
    if normed in VALUES_SPORT_KNUCKLE_MMA:
        return SPORT_KNUCKLE_MMA
    if normed in VALUES_SPORT_BOX:
        return SPORT_BOX
    if normed in VALUES_SPORT_KNUCKLE_BOX:
        return SPORT_KNUCKLE_BOX
    if normed in VALUES_SPORT_KICK:
        return SPORT_KICK
    if normed in VALUES_SPORT_MUAY:
        return SPORT_MUAY
    if normed in VALUES_SPORT_KARATE:
        return SPORT_KARATE
    if normed in VALUES_SPORT_SANDA:
        return SPORT_SANDA
    if normed in VALUES_SPORT_LETHWEI:
        return SPORT_LETHWEI
    if normed in VALUES_SPORT_GRAPPLE:
        return SPORT_GRAPPLE
    if normed in VALUES_SPORT_SHOOT:
        return SPORT_SHOOT
    if normed in VALUES_SPORT_WRESTLE:
        return SPORT_WRESTLE
    if normed in VALUES_SPORT_SAMBO:
        return SPORT_SAMBO
    if normed in VALUES_SPORT_VALE:
        return SPORT_VALE
    if normed in VALUES_SPORT_JUDO:
        return SPORT_JUDO
    if normed in VALUES_SPORT_CUSTOM:
        return SPORT_CUSTOM
    return None


def normalize_weight_class(weight_class: str) -> Union[str, None]:
    normed = normalize_string(weight_class)
    if normed == "atomweight":
        return WEIGHT_CLASS_ATOM
    if normed == "strawweight":
        return WEIGHT_CLASS_STRAW
    if normed == "flyweight":
        return WEIGHT_CLASS_FLY
    if normed == "bantamweight":
        return WEIGHT_CLASS_BANTAM
    if normed == "featherweight":
        return WEIGHT_CLASS_FEATHER
    if normed == "lightweight":
        return WEIGHT_CLASS_LIGHT
    if normed == "welterweight":
        return WEIGHT_CLASS_WELTER
    if normed == "middleweight":
        return WEIGHT_CLASS_MIDDLE
    if normed == "light heavyweight":
        return WEIGHT_CLASS_LIGHT_HEAVY
    if normed == "heavyweight":
        return WEIGHT_CLASS_HEAVY
    if normed == "super heavyweight":
        return WEIGHT_CLASS_SUPER_HEAVY
    return None


def to_weight_class(value: float, unit: str = "kg", margin: float = 0.02) -> str:
    if unit not in ["kg", "kgs", "lbs", "lb"]:
        raise ValueError(f"Unsupported unit: {unit}")
    if margin < 0 or 1 < margin:
        raise ValueError(f"margin must be in [0, 1]")
    kg = value
    if unit not in ["kg", "kgs"]:
        kg = to_kg(value)
    scale = 1 + margin
    if kg <= WEIGHT_LIMIT_ATOM * scale:
        return WEIGHT_CLASS_ATOM
    if kg <= WEIGHT_LIMIT_STRAW * scale:
        return WEIGHT_CLASS_STRAW
    if kg <= WEIGHT_LIMIT_FLY * scale:
        return WEIGHT_CLASS_FLY
    if kg <= WEIGHT_LIMIT_BANTAM * scale:
        return WEIGHT_CLASS_BANTAM
    if kg <= WEIGHT_LIMIT_FEATHER * scale:
        return WEIGHT_CLASS_FEATHER
    if kg <= WEIGHT_LIMIT_LIGHT * scale:
        return WEIGHT_CLASS_LIGHT
    if kg <= WEIGHT_LIMIT_WELTER * scale:
        return WEIGHT_CLASS_WELTER
    if kg <= WEIGHT_LIMIT_MIDDLE * scale:
        return WEIGHT_CLASS_MIDDLE
    if kg <= WEIGHT_LIMIT_LIGHT_HEAVY * scale:
        return WEIGHT_CLASS_LIGHT_HEAVY
    if kg <= WEIGHT_LIMIT_HEAVY * scale:
        return WEIGHT_CLASS_HEAVY
    return WEIGHT_CLASS_SUPER_HEAVY


def parse_weight(txt: str) -> Union[Dict[str, float], None]:
    normed = txt.lower().strip()
    weight_class = None
    ret = {}
    once = True

    # Heavyweight
    # 110 (kg|kgs|lb|lbs)
    if once:
        matched = re.match(r"^(.*weight|[\d\.]+ (?:kg|kgs|lb|lbs))$", normed)
        if matched:
            weight_class = matched.group(1)
            once = False

    # 110 (kg|kgs|lb|lbs) (49.9 (kg|kgs|lb|lbs))
    if once:
        matched = re.match(r"^([\d\.]+ (?:kg|kgs|lb|lbs)) \(.*\)$", normed)
        if matched:
            weight_class = matched.group(1)
            once = False

    # Heavyweight · 120 (kg|kgs|lb|lbs) (264.6 (kg|kgs|lb|lbs))
    if once:
        matched = re.match(
            r"^(.*weight|[\d\.]+ (?:kg|kgs|lb|lbs)) · ([\d\.]+) (kg|kgs|lb|lbs) \(.*\)$",
            normed,
        )
        if matched:
            weight_class = matched.group(1)
            ret["limit"] = (
                to_kg(float(matched.group(2)))
                if matched.group(3).startswith("lb")
                else float(matched.group(2))
            )
            once = False

    # Open Weight · Weigh-In 436.5 (kg|kgs|lb|lbs) (198.0 (kg|kgs|lb|lbs))
    if once:
        matched = re.match(
            r"^(.*weight|[\d\.]+ (?:kg|kgs|lb|lbs)) · weigh-in ([\d\.]+) (kg|kgs|lb|lbs) \(.*\)$",
            normed,
        )
        if matched:
            weight_class = matched.group(1)
            ret["weigh_in"] = (
                to_kg(float(matched.group(2)))
                if matched.group(3).startswith("lb")
                else float(matched.group(2))
            )
            once = False

    # Light Heavyweight · 205 (kg|kgs|lb|lbs) (93.0 (kg|kgs|lb|lbs)) · Weigh-In 201.0 (kg|kgs|lb|lbs) (91.2 (kg|kgs|lb|lbs))
    if once:
        matched = re.match(
            r"^(.*weight|[\d\.]+ (?:kg|kgs|lb|lbs)) · ([\d\.]+) (kg|kgs|lb|lbs) \(.*\) · weigh-in ([\d\.]+) (kg|kgs|lb|lbs) \(.*\)$",
            normed,
        )
        if matched:
            weight_class = matched.group(1)
            ret["limit"] = (
                to_kg(float(matched.group(2)))
                if matched.group(3).startswith("lb")
                else float(matched.group(2))
            )
            ret["weigh_in"] = (
                to_kg(float(matched.group(4)))
                if matched.group(5).startswith("lb")
                else float(matched.group(4))
            )
            once = False

    # Normalize weight class
    if weight_class:
        normed_weight_class = normalize_weight_class(weight_class)
        if normed_weight_class:
            ret["class"] = normed_weight_class
            return ret
        matched = re.match(r"^([\d\.]+) (kg|kgs|lb|lbs)$", weight_class)
        if matched:
            # Infer weight class
            ret["class"] = to_weight_class(
                float(matched.group(1)), unit=matched.group(2)
            )
            return ret
        if weight_class.startswith("open") or weight_class.startswith("catch"):
            if "weigh-in" in ret:
                # Infer weight class from weigh-in weight
                ret["class"] = to_weight_class(ret["weigh_in"], unit="kg")
                return ret
            if "limit" in ret:
                # Infer weight class from limit weight
                ret["class"] = to_weight_class(ret["limit"], unit="kg")
                return ret
            if weight_class.startswith("open"):
                ret["class"] = "open"
            elif weight_class.startswith("catch"):
                ret["class"] = "catch"
    return None if ret == {} else ret


def parse_time(txt: str) -> Union[Dict[str, int], None]:
    normed = txt.strip()
    matched = re.match(r"^(\d+):(\d+)$", normed)
    if matched:
        return {"m": int(matched.group(1)), "s": int(matched.group(2))}
    return None


def parse_round(txt: str) -> Union[int, None]:
    normed = txt.lower().strip()
    matched = re.match(r"^r([1-9])$", normed)
    if matched:
        return int(matched.group(1))
    return None


def parse_duration(txt: str) -> Union[List[int], None]:
    normed = txt.lower().strip()
    matched = re.match(r"^(\d+) x (\d+) min", normed)
    if matched:
        return [int(matched.group(2))] * int(matched.group(1))
    matched = re.match(r"^(\d+) min one round", normed)
    if matched:
        return [int(matched.group(1))]
    matched = re.match(r"^(\d+) min round plus overtime", normed)
    if matched:
        return [int(matched.group(1))]
    matched = re.match(r"^(\d+)-(\d+)-(\d+)", normed)
    if matched:
        return [int(matched.group(1)), int(matched.group(2)), int(matched.group(3))]
    matched = re.match(r"^(\d+)-(\d+)", normed)
    if matched:
        return [int(matched.group(1)), int(matched.group(2))]
    matched = re.match(r"^(\d+) \+ (\d+)", normed)
    if matched:
        return [int(matched.group(1)), int(matched.group(2))]
    matched = re.match(r"^(\d+) \+ (\d+) \+ (\d+)", normed)
    if matched:
        return [int(matched.group(1)), int(matched.group(2)), int(matched.group(3))]
    return None


def to_meter(feet: float, inch: float) -> float:
    return feet * 0.3048 + inch * 0.0254


def to_kg(lb: float) -> float:
    return lb * 0.453592


def infer(bout_ended_by: str) -> str:
    normed = bout_ended_by.strip().lower()
    if normed == "decision":
        return "decision"
    if (
        normed == "ko/tko"
        or normed == "knee"
        or "kick" in normed
        or "punch" in normed
        or "elbow" in normed
        or "stoppage" in normed
        or "cut" in normed
        or "retirement" in normed
        or "pound" in normed
        or "strike" in normed
        or "towel" in normed
        or "slam" in normed
        or "fist" in normed
    ):
        return "ko/tko"
    return "submisson"
