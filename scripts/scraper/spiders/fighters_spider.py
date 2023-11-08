import scrapy
import re
from scrapy.http import Request, TextResponse
from collections.abc import Generator
from typing import List, Union, Dict
from .constants import *


class FightersSpider(scrapy.Spider):
    name = "fighters"
    start_urls = ["https://www.tapology.com/search"]

    def __init__(
        self,
        min_mma_bouts: int = 1,
        ignore_am_mma_fighters: bool = False,
        ignore_non_mma_fighters: bool = True,
        *args,
        **kwargs,
    ):
        super(FightersSpider, self).__init__(*args, **kwargs)
        self.min_mma_bouts = min_mma_bouts
        self.ignore_am_mma_fighters = ignore_am_mma_fighters
        self.ignore_non_mma_fighters = ignore_non_mma_fighters

    def parse(self, response: TextResponse):
        urls = response.xpath(
            "//div[@class='siteSearchFightersByWeightClass']/dd/a/@href"
        ).getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_fighter_list)

    def parse_fighter_list(self, response: TextResponse):
        fighters = response.xpath("//table[@class='siteSearchResults']/tr")[1:]
        for fighter in fighters:
            career_record = fighter.xpath("./td[7]/text()[normalize-space()]").get()
            if career_record is None:
                self.logger.error(
                    "Unexpected page structure: could not find mma career record column on the fighters' list"
                )
                continue
            matched = re.match(
                r"^(?:(Am) )?(\d+)-(\d+)-(\d+)(?:, \d+ NC)?$", career_record
            )
            if matched is None:
                self.logger.error(f"Unexpected mma record format: {career_record}")
                continue
            if self.ignore_am_mma_fighters and matched.group(1) == "Am":
                continue
            total = sum(
                [int(matched.group(2)), int(matched.group(3)), int(matched.group(4))]
            )
            if total < self.min_mma_bouts:
                continue
            url = fighter.xpath("./td[1]/a/@href").get()
            if url is not None:
                yield response.follow(url, callback=self.parse_fighter)

        # Move to the next page
        next_url = response.xpath(
            "//span[@class='moreLink']/nav[@class='pagination']/span[@class='next']/a/@href"
        ).get()
        if next_url is not None:
            yield response.follow(next_url, callback=self.parse_fighter_list)

    def parse_fighter(self, response: TextResponse):
        ret = {}

        # Fighter url (must)
        ret["url"] = response.url

        # Fighter ID (must)
        ret["id"] = parse_id_from_url(response.url)

        # Fighter name (must)
        name = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h1[not(@*)]/text()[normalize-space()]"
        ).get()
        if name is None:
            self.logger.error(
                "Unexpected page structure: could not find the fighter's name"
            )
            return
        ret["name"] = normalize_text(name)

        # Parse header section (must)
        header_section = response.xpath("//div[@class='fighterUpcomingHeader']")
        if len(header_section) == 0:
            self.logger.error(
                "Unexpected page structure: could not find the header section"
            )
            return

        # Nationality (optional)
        nationality = header_section.xpath("./h2[@id='flag']/a/@href").re_first(
            r"country\-(.*)$"
        )
        if nationality is not None:
            ret["nationality"] = normalize_text(nationality)

        # Nickname (optional)
        nickname = header_section.xpath(
            "./h4[@class='preTitle nickname']/text()[normalize-space()]"
        ).get()
        if nickname is not None:
            ret["nickname"] = normalize_text(nickname)[1:-1]

        # Parse profile section (must)
        profile_section = response.xpath("//div[@class='details details_two_columns']")
        if len(profile_section) == 0:
            self.logger.error(
                "Unexpected page structure: could not find the profile section"
            )
            return

        # Date of birth (optional)
        date_of_birth = profile_section.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if date_of_birth is not None:
            date_of_birth = normalize_text(date_of_birth)
            if date_of_birth not in VALUES_NOT_AVAILABLE:
                ret["date_of_birth"] = parse_date(date_of_birth)

        # Weight class (optional)
        weight_class = profile_section.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if weight_class:
            normed = normalize_weight_class(weight_class)
            if normed is not None:
                ret["weight_class"] = normed
            else:
                self.logger.error(f"Unexpected weight class: {weight_class}")

        # Affiliation (optional)
        affili_section = profile_section.xpath(
            "./ul/li/strong[text()='Affiliation:']/following-sibling::span[1]/a"
        )
        if len(affili_section) == 1:
            url = affili_section.xpath("./@href").get()
            if url is not None:
                url = response.urljoin(url)
                name = affili_section.xpath("./text()[normalize-space()]").get()
                if name is not None:
                    ret["affiliation"] = {
                        "url": url,
                        "id": parse_id_from_url(url),
                        "name": normalize_text(name),
                    }

        # Height (optional)
        # NOTE: e.g. "5\'9\" (175cm)"
        height = profile_section.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()[normalize-space()]"
        ).re(r"([\d\.]+)\'([\d\.]+)\"")
        if len(height) == 2:
            ret["height"] = to_meter(float(height[0]), float(height[1]))

        # Reach (optional)
        # NOTE: e.g. "74.0\" (188cm)"
        reach = profile_section.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()[normalize-space()]"
        ).re(r"([\d\.]+)\"")
        if len(reach) == 1:
            ret["reach"] = to_meter(0, float(reach[0]))

        # Place of birth (optional)
        place_of_birth = profile_section.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if place_of_birth is not None:
            place_of_birth = normalize_text(place_of_birth)
            if place_of_birth not in VALUES_NOT_AVAILABLE:
                ret["place_of_birth"] = []
                for p in place_of_birth.split(","):
                    ret["place_of_birth"].append(p.strip())

        # Fighting out of (optional)
        out_of = profile_section.xpath(
            "./ul/li/strong[text()='Fighting out of:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if out_of is not None:
            out_of = normalize_text(out_of)
            if out_of not in VALUES_NOT_AVAILABLE:
                ret["out_of"] = []
                for o in out_of.split(","):
                    ret["out_of"].append(o.strip())

        # College (optional)
        college = profile_section.xpath(
            "./ul/li/strong[text()='College:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if college is not None:
            college = normalize_text(college)
            if college not in VALUES_NOT_AVAILABLE:
                ret["college"] = college

        # Foundation styles (optional)
        styles = profile_section.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if styles is not None:
            styles = normalize_text(styles)
            if styles not in VALUES_NOT_AVAILABLE:
                ret["foundation_styles"] = []
                for s in styles.split(","):
                    ret["foundation_styles"].append(s.strip())

        # Head Coach (optional)
        head_coach = profile_section.xpath(
            "./ul/li/strong[text()='Head Coach:']/following-sibling::span[1]/text()[normalize-space()]"
        ).get()
        if head_coach is not None:
            head_coach = normalize_text(head_coach)
            if head_coach not in VALUES_NOT_AVAILABLE:
                ret["head_coach"] = head_coach

        # Parse bout results
        ret["results"] = []
        for division in ["pro", "am"]:
            result_sections = response.xpath(
                f"//section[@class='fighterFightResults']/ul[@id='{division}Results']/li"
            )
            if len(result_sections) == 0:
                continue
            for result_section in result_sections:
                # Stores data of a bout
                item = {"division": division}

                # Check if this is a non mma bout
                txt = result_section.xpath(
                    "./div[@class='result']/div[@class='opponent']/div[@class='record nonMma']/text()[normalize-space()]"
                ).get()
                is_non_mma_bout = False
                if txt is not None:
                    is_non_mma_bout = True
                    txt = normalize_text(txt)
                    if txt.startswith("record ineligible"):
                        # NOTE: Ignore inegligible bouts
                        continue

                # Sport of the bout (must)
                sport = result_section.xpath("./@data-sport").get()
                if sport is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the sport of the bout"
                    )
                    continue
                normed_sport = normalize_sport(sport)
                if normed_sport is None:
                    self.logger.error(f"Unexpected sport value: {sport}")
                    continue
                if normed_sport == SPORT_CUSTOM:
                    # NOTE: Ignore records with custom rule
                    continue
                item["sport"] = normed_sport

                # Status of the bout (must)
                status = result_section.xpath("./@data-status").get()
                if status is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the status of the bout"
                    )
                    continue
                normed_status = normalize_status(status)
                if normed_status is None:
                    self.logger.error(f"Unexpected status value: {status}")
                    continue
                if normed_status in [
                    STATUS_CANCELLED,
                    STATUS_UPCOMING,
                    STATUS_UNKNOWN,
                    STATUS_NO_CONTEST,
                ]:
                    # NOTE: Ignore records with status = cancelled, upcoming, unknown, no-contest bouts
                    continue
                item["status"] = normed_status

                # Date of the bout (must)
                date = result_section.xpath(
                    "./div[@class='result']/div[@class='date']/text()[normalize-space()]"
                ).get()
                if date is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the date of the bout"
                    )
                    continue
                date_normed = parse_date(date)
                if date_normed is None:
                    self.logger.error(f"Unexpected format of date: {date}")
                    continue
                item["date"] = date_normed

                # Opponent fighter of the bout (must)
                opponent_section = result_section.xpath(
                    "./div[@class='result']/div[@class='opponent']"
                )
                if len(opponent_section) == 0:
                    self.logger.error(
                        "Unexpected page structure: could not find any opponent data"
                    )
                    continue
                item["opponent"] = {}

                # Name & link of the opponent fighter
                # NOTE: at least name must be provided
                a = opponent_section.xpath("./div[@class='name']/a")
                has_opponent_url = False if len(a) == 0 else True
                if has_opponent_url:
                    url = a.xpath("./@href").get()
                    name = a.xpath("./text()[normalize-space()]").get()
                    if url is not None:
                        url = response.urljoin(url)
                        item["opponent"]["url"] = url
                        item["opponent"]["id"] = parse_id_from_url(url)
                    if name is not None:
                        item["opponent"]["name"] = normalize_text(name)
                else:
                    name = opponent_section.xpath(
                        "./div[@class='name']/span/text()[normalize-space()]"
                    ).get()
                    if name is None:
                        self.logger.error(
                            "Unexpected page structure: could not find opponent's name"
                        )
                        continue
                    item["opponent"]["name"] = normalize_text(name)

                # Promotion of the fight (optional)
                # NOTE: available then the bout is not tagged as "nonMma"
                # and its status is not "cancelled" or "unknown"
                if not is_non_mma_bout and normed_status not in [
                    STATUS_CANCELLED,
                    STATUS_UNKNOWN,
                ]:
                    section = result_section.xpath(
                        "./div[@class='result']/div[@class='summary']/div[@class='notes']/a"
                    )
                    if len(section) == 1:
                        title = section.xpath("./@title").get()
                        url = section.xpath("./@href").get()
                        if title == "Promotion Page" and url is not None:
                            url = response.urljoin(url)
                            item["promotion"] = {
                                "url": url,
                                "id": parse_id_from_url(url),
                            }
                    if "promotion" not in item:
                        url = result_section.xpath(
                            "./div[@class='details tall']/div[@class='logo']/div[@class='promotionLogo']/a/@href"
                        ).get()
                        if url is not None:
                            url = response.urljoin(url)
                            item["promotion"] = {
                                "url": url,
                                "id": parse_id_from_url(url),
                            }

                # Career record before the bout (optional)
                # NOTE: available when the bout is not tagged as "nonMma"
                # and its status is not "cancelled" or "unknown"
                if not is_non_mma_bout is None and normed_status not in [
                    STATUS_CANCELLED,
                    STATUS_UNKNOWN,
                ]:
                    section = opponent_section.xpath("./div[@class='record']")
                    txt = section.xpath(
                        "./span[@title='Fighter Record Before Fight']/text()[normalize-space()]"
                    ).get()
                    if txt is not None:
                        fighter_record = parse_record(txt)
                        if fighter_record is not None:
                            item["record"] = fighter_record
                        else:
                            self.logger.error(
                                f"Unexpected format of fighter record: {txt}"
                            )

                    # NOTE: Opponent record is available
                    # when the opponent has a link to his page
                    if has_opponent_url:
                        txt = section.xpath(
                            "./span[@title='Opponent Record Before Fight']/text()[normalize-space()]"
                        ).get()
                        if txt is not None:
                            opponent_record = parse_record(txt)
                            if opponent_record is not None:
                                item["opponent"]["record"] = opponent_record
                            else:
                                self.logger.error(
                                    f"Unexpected format of opponent record: {txt}"
                                )

                # Details of the bout (optional)
                # NOTE: Handle only mma bouts (not tagged as "nonMma")
                # with status win, loss, or draw
                if is_non_mma_bout is None and normed_status in [
                    STATUS_WIN,
                    STATUS_LOSS,
                    STATUS_DRAW,
                ]:
                    # Parse summary lead of the record
                    lead_section = result_section.xpath(
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
                                    map(
                                        lambda x: x.strip(),
                                        normalize_text(lead).split("·"),
                                    ),
                                )
                            )
                            n = len(l)
                            if not (1 <= n <= 4):
                                self.logger.error(
                                    f"Unexpected format of summary lead text: {lead}"
                                )
                            else:
                                if n != 1:
                                    if n == 2:
                                        # (win|loss|draw), (decision|finish)
                                        if l[1] == "decision":
                                            item["ended_by"] = {
                                                "type": "decision",
                                            }
                                        else:
                                            item["ended_by"] = {
                                                "type": infer(l[1]),
                                                "detail": l[1],
                                            }
                                    elif n == 3:
                                        # (win|loss), finish, round
                                        # (win|loss|draw), decision, (majority|unanimous|split)
                                        t = infer(l[1])
                                        if t == "decision":
                                            item["ended_by"] = {
                                                "type": t,
                                                "detail": l[2],
                                            }
                                        else:
                                            item["ended_by"] = {
                                                "type": t,
                                                "detail": l[1],
                                            }
                                            r = parse_round(l[2])
                                            if r is None:
                                                self.logger.error(
                                                    f"Unexpected format of round: {l[2]}"
                                                )
                                            else:
                                                item["ended_at"] = {"round": r}
                                    elif n == 4:
                                        # (win|loss), finish, time, round
                                        item["ended_by"] = {
                                            "type": infer(l[1]),
                                            "detail": l[1],
                                        }
                                        r, t = parse_round(l[3]), parse_time(l[2])
                                        if r is not None or t is not None:
                                            item["ended_at"] = {}
                                            if r is None:
                                                self.logger.error(
                                                    f"Unexpected format of round: {l[3]}"
                                                )
                                            else:
                                                item["ended_at"]["round"] = r
                                            if t is None:
                                                self.logger.error(
                                                    f"Unexpected format of time: {l[2]}"
                                                )
                                            else:
                                                item["ended_at"]["time"] = t

                    # Parse more data about the bout
                    label_sections = result_section.xpath(
                        "./div[@class='details tall']/div[@class='div']/span[@class='label']"
                    )
                    for label_section in label_sections:
                        label = label_section.xpath("./text()[normalize-space()]").get()
                        if label is None:
                            continue
                        label = normalize_text(label)
                        if label == "billing:":
                            # Billing of the bout
                            # e.g "main event", "co-main event", "prelim", etc.
                            billing = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if billing is not None:
                                item["billing"] = normalize_text(billing)
                        elif label == "duration:":
                            # Duration of the bout
                            # The number of rounds, the duration per round
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if txt is not None:
                                duration = parse_duration(txt)
                                if duration is not None:
                                    item["duration"] = duration
                                else:
                                    self.logger.error(
                                        f"Unexpected format of duration: {txt}"
                                    )
                        elif label == "referee:":
                            # Name of the referee
                            referee = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if referee is not None:
                                item["referee"] = normalize_text(referee)
                        elif label == "weight:":
                            # Contracted weight limit & measured weight at weigh-in
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if txt is not None:
                                weight = parse_weight(txt)
                                if weight is not None:
                                    item["weight"] = weight
                                else:
                                    self.logger.error(
                                        f"Unexpected format of weight: {txt}"
                                    )
                        elif label == "odds:":
                            # Odds of the fighter at the bout
                            # NOTE: american odds style; e.g +100, -500
                            odds = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).re_first(r"([\+\-][\d\.]+)")
                            if odds is not None:
                                item["odds"] = float(odds)
                        elif label == "title bout:":
                            # Title info of the bout
                            # NOTE: available when this is a title match
                            # or a part of a tornament
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()[normalize-space()]"
                            ).get()
                            if txt is not None:
                                info = parse_title_info(txt)
                                if info is not None:
                                    item["title_info"] = info
                                else:
                                    self.logger.error(
                                        f"Unexpected format of title info: {txt}"
                                    )
                ret["results"].append(item)
        return ret


def normalize_text(s: str, lower: bool = True) -> str:
    s = " ".join(s.split())
    s = s.replace("\n", "").replace("\t", "")
    if lower:
        s = s.lower()
    return s


def normalize_status(status: str) -> Union[str, None]:
    normed = normalize_text(status)
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
    normed = normalize_text(sport)
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
    if normed in VALUES_SPORT_COMBAT_JIU_JITSU:
        return SPORT_COMBAT_JIU_JITSU
    if normed in VALUES_SPORT_CUSTOM:
        return SPORT_CUSTOM
    return None


def normalize_weight_class(weight_class: str) -> Union[str, None]:
    normed = normalize_text(weight_class)
    if normed in VALUES_WEIGHT_CLASS_ATOM:
        return WEIGHT_CLASS_ATOM
    if normed in VALUES_WEIGHT_CLASS_STRAW:
        return WEIGHT_CLASS_STRAW
    if normed in VALUES_WEIGHT_CLASS_FLY:
        return WEIGHT_CLASS_FLY
    if normed in VALUES_WEIGHT_CLASS_BANTAM:
        return WEIGHT_CLASS_BANTAM
    if normed in VALUES_WEIGHT_CLASS_FEATHER:
        return WEIGHT_CLASS_FEATHER
    if normed in VALUES_WEIGHT_CLASS_LIGHT:
        return WEIGHT_CLASS_LIGHT
    if normed in VALUES_WEIGHT_CLASS_SUPER_LIGHT:
        return WEIGHT_CLASS_SUPER_LIGHT
    if normed in VALUES_WEIGHT_CLASS_WELTER:
        return WEIGHT_CLASS_WELTER
    if normed in VALUES_WEIGHT_CLASS_SUPER_WELTER:
        return WEIGHT_CLASS_SUPER_WELTER
    if normed in VALUES_WEIGHT_CLASS_MIDDLE:
        return WEIGHT_CLASS_MIDDLE
    if normed in VALUES_WEIGHT_CLASS_SUPER_MIDDLE:
        return WEIGHT_CLASS_SUPER_MIDDLE
    if normed in VALUES_WEIGHT_CLASS_LIGHT_HEAVY:
        return WEIGHT_CLASS_LIGHT_HEAVY
    if normed in VALUES_WEIGHT_CLASS_HEAVY:
        return WEIGHT_CLASS_HEAVY
    if normed in VALUES_WEIGHT_CLASS_CRUISER:
        return WEIGHT_CLASS_CRUISER
    if normed in VALUES_WEIGHT_CLASS_SUPER_HEAVY:
        return WEIGHT_CLASS_SUPER_HEAVY
    return None


def to_weight_class(value: float, unit: str = "kg", margin: float = 0.02) -> str:
    if unit not in ["kg", "kgs", "lbs", "lb"]:
        raise ValueError(f"Unsupported unit: {unit}")
    if margin < 0 or 1 < margin:
        raise ValueError("Margin must be [0, 1]")
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
    if kg <= WEIGHT_LIMIT_SUPER_LIGHT * scale:
        return WEIGHT_CLASS_SUPER_LIGHT
    if kg <= WEIGHT_LIMIT_WELTER * scale:
        return WEIGHT_CLASS_WELTER
    if kg <= WEIGHT_LIMIT_SUPER_WELTER * scale:
        return WEIGHT_CLASS_SUPER_WELTER
    if kg <= WEIGHT_LIMIT_MIDDLE * scale:
        return WEIGHT_CLASS_MIDDLE
    if kg <= WEIGHT_LIMIT_SUPER_MIDDLE:
        return WEIGHT_CLASS_SUPER_MIDDLE
    if kg <= WEIGHT_LIMIT_LIGHT_HEAVY * scale:
        return WEIGHT_CLASS_LIGHT_HEAVY
    if kg <= WEIGHT_LIMIT_CRUISER * scale:
        return WEIGHT_CLASS_CRUISER
    if kg <= WEIGHT_LIMIT_HEAVY * scale:
        return WEIGHT_CLASS_HEAVY
    return WEIGHT_CLASS_SUPER_HEAVY


def parse_weight(txt: str) -> Union[Dict[str, float], None]:
    normed = normalize_text(txt)
    weight_class = None
    ret = {}
    once = True

    # Heavyweight
    # 110 kg|kgs|lb|lbs
    # 110 kg|kgs|lb|lbs (49.9 kg|kgs|lb|lbs)
    if once:
        matched = re.match(
            r"^(.*weight|[\d\.]+ (?:kgs?|lbs?))(?: \([\d\.]+ (?:kgs?|lbs?)\))?$", normed
        )
        if matched is not None:
            weight_class = matched.group(1)
            once = False

    # Heavyweight · 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
    # Heavyweight · Weigh-In 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
    # Flyweight · 125 lbs (56.7 kg)
    if once:
        matched = re.match(
            r"^(.*weight|[\d\.]+ (?:kgs?|lbs?))(?: \([\d\.]+ (?:kgs?|lbs?)\))? · (weigh-in )?([\d\.]+) (kgs?|lbs?) \([\d\.]+ (?:kgs?|lbs?)\)$",
            normed,
        )
        if matched is not None:
            weight_class = matched.group(1)
            w = float(matched.group(3))
            if matched.group(4).startswith("lb"):
                w = to_kg(w)
            if matched.group(2) is None:
                ret["limit"] = w
            else:
                ret["weigh_in"] = w
            once = False

    # Heavyweight · 205 kg|kgs|lb|lbs (93.0 kg|kgs|lb|lbs) · Weigh-In 201.0 kg|kgs|lb|lbs (91.2 kg|kgs|lb|lbs)
    if once:
        matched = re.match(
            r"^(.*weight|[\d\.]+ (?:kgs?|lbs?))(?: \([\d\.]+ (?:kgs?|lbs?)\))? · ([\d\.]+) (kgs?|lbs?) \([\d\.]+ (?:kgs?|lbs?)\) · weigh-in ([\d\.]+) (kgs?|lbs?) \([\d\.]+ (?:kgs?|lbs?)\)$",
            normed,
        )
        if matched is not None:
            weight_class = matched.group(1)
            limit = float(matched.group(2))
            if matched.group(3).startswith("lb"):
                limit = to_kg(limit)
            ret["limit"] = limit
            weigh_in = float(matched.group(4))
            if matched.group(5).startswith("lb"):
                weigh_in = to_kg(weigh_in)
            ret["weigh_in"] = weigh_in
            once = False

    # Normalize weight class
    if weight_class is not None:
        normed_weight_class = normalize_weight_class(weight_class)
        if normed_weight_class is not None:
            ret["class"] = normed_weight_class
            return ret
        matched = re.match(r"^([\d\.]+) (kgs?|lbs?)$", weight_class)
        if matched is not None:
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


def parse_date(txt: str) -> Union[str, None]:
    normed = normalize_text(txt)
    matched = re.match(r"^(\d+)\.(\d+)\.(\d+)$", normed)
    if matched is not None:
        return f"{matched.group(1):04}-{matched.group(2):02}-{matched.group(3):02}"
    return None


def parse_record(txt: str) -> Union[Dict[str, int], None]:
    normed = normalize_text(txt)
    matched = re.match(r"^(\d+)-(\d+)-(\d+)", normed)
    if matched is not None:
        return {
            "w": int(matched.group(1)),
            "l": int(matched.group(2)),
            "d": int(matched.group(3)),
        }
    return None


def parse_time(txt: str) -> Union[Dict[str, int], None]:
    normed = normalize_text(txt)
    matched = re.match(r"^(\d+):(\d+)$", normed)
    if matched:
        return {"m": int(matched.group(1)), "s": int(matched.group(2))}
    return None


def parse_round(txt: str) -> Union[int, None]:
    normed = normalize_text(txt)
    matched = re.match(r"^r([1-9])$", normed)
    if matched:
        return int(matched.group(1))
    return None


def parse_duration(txt: str) -> Union[List[int], None]:
    normed = normalize_text(txt)

    # 5 min
    # 2 x 5 min
    matched = re.match(r"^(\d+)(?: x (\d+))? min", normed)
    if matched is not None:
        if matched.group(2) is None:
            return [int(matched.group(1))]
        return [int(matched.group(2)) for _ in range(int(matched.group(1)))]

    # 5-5
    # 5-5-5
    # 5 + 5
    # 5 + 5 + 5
    matched = re.match(r"^(\d+)(?:\-| \+ )(\d+)(?:(?:\-| \+ )(\d+))?", normed)
    if matched is not None:
        if matched.group(3) is None:
            return [int(matched.group(1)), int(matched.group(2))]
        return [int(matched.group(1)), int(matched.group(2)), int(matched.group(3))]

    # 1 Round, No Limit
    if normed == "1 round, no limit":
        return [-1]
    return None


def parse_title_info(txt: str) -> Union[Dict[str, str], None]:
    ret = {}

    # champion|challenger|vacant · championship
    # championship
    l = list(map(lambda s: s.strip(), normalize_text(txt).split("·")))
    if len(l) == 1:
        return {"championship": l[0]}
    if len(l) == 2:
        return {"championship": l[1], "as": l[0]}
    return None


def parse_id_from_url(url: str) -> str:
    return url.split("/")[-1]


def to_meter(feet: float, inch: float) -> float:
    return feet * 0.3048 + inch * 0.0254


def to_kg(lb: float) -> float:
    return lb * 0.453592


def infer(bout_ended_by: str) -> str:
    normed = normalize_text(bout_ended_by)
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
