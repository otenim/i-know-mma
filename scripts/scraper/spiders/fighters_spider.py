import scrapy
import re
import datetime
from scrapy.http import TextResponse
from typing import List, Union, Dict
from .constants import *
from .errors import *


class FightersSpider(scrapy.Spider):
    name = "fighters"
    start_urls = ["https://www.tapology.com/search"]

    def __init__(
        self,
        min_mma_matches: int = 1,
        ignore_am_mma_fighters: bool = False,
        *args,
        **kwargs,
    ):
        super(FightersSpider, self).__init__(*args, **kwargs)
        if min_mma_matches < 0:
            raise ValueError(f"min_mma_matches expects >= 0 but {min_mma_matches}")
        self.min_mma_matches = min_mma_matches
        self.ignore_am_mma_fighters = ignore_am_mma_fighters

    def parse(self, response: TextResponse):
        urls = response.xpath(
            "//div[@class='siteSearchFightersByWeightClass']/dd/a/@href"
        ).getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_fighter_list)

    def parse_fighter_list(self, response: TextResponse):
        fighters = response.xpath("//table[@class='siteSearchResults']/tr")[1:]
        for fighter in fighters:
            career_record = fighter.xpath("./td[7]/text()").get()
            if career_record is None:
                self.logger.error(
                    "Unexpected page structure: could not find mma career record column on the fighters' list"
                )
                continue
            career_record = normalize_text(career_record)
            matched = re.match(
                r"^(?:(am) )?(\d+)-(\d+)-(\d+)(?:, \d+ nc)?$", career_record
            )
            if matched is None:
                self.logger.error(f"Unexpected mma record format: {career_record}")
                continue
            if self.ignore_am_mma_fighters and matched.group(1) == "am":
                continue
            total = sum(
                [int(matched.group(2)), int(matched.group(3)), int(matched.group(4))]
            )
            if total < self.min_mma_matches:
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

        # Fighter ID (must)
        ret["id"] = get_id_from_url(response.url)

        # Fighter name (must)
        name = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h1[not(@*)]/text()"
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
            "./h4[@class='preTitle nickname']/text()"
        ).re_first(r"\"(.*)\"")
        if nickname is not None:
            ret["nickname"] = normalize_text(nickname)

        # Parse profile section (must)
        profile_section = response.xpath("//div[@class='details details_two_columns']")
        if len(profile_section) == 0:
            self.logger.error(
                "Unexpected page structure: could not find the profile section"
            )
            return

        # Date of birth (optional)
        date_of_birth = profile_section.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()"
        ).get()
        if date_of_birth is not None:
            date_of_birth = normalize_text(date_of_birth)
            if date_of_birth not in VALUES_NOT_AVAILABLE:
                ret["date_of_birth"] = parse_date(date_of_birth)

        # Weight class (optional)
        weight_class = profile_section.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()"
        ).get()
        if weight_class is not None:
            normed = normalize_weight_class(weight_class)
            if normed is not None:
                ret["weight_class"] = normed
            else:
                self.logger.error(f"Unexpected weight class: {weight_class}")

        # Career disclosed earnings (optional)
        career_earnings = profile_section.xpath(
            "./ul/li/strong[text()='Career Disclosed Earnings:']/following-sibling::span[1]/text()"
        ).re_first(r"^\$(.*) USD")
        if career_earnings is not None:
            ret["career_earnings"] = int(career_earnings.replace(",", ""))

        # Affiliation (optional)
        affili_section = profile_section.xpath(
            "./ul/li/strong[text()='Affiliation:']/following-sibling::span[1]/a"
        )
        if len(affili_section) == 1:
            url = affili_section.xpath("./@href").get()
            if url is not None:
                ret["affiliation"] = get_id_from_url(url)

        # Height (optional)
        # e.g. "5\'9\" (175cm)"
        height = profile_section.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\'([\d\.]+)\"")
        if len(height) == 2:
            ret["height"] = to_meter(float(height[0]), float(height[1]))

        # Reach (optional)
        # e.g. "74.0\" (188cm)"
        reach = profile_section.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\"")
        if len(reach) == 1:
            ret["reach"] = to_meter(0, float(reach[0]))

        # College (optional)
        college = profile_section.xpath(
            "./ul/li/strong[text()='College:']/following-sibling::span[1]/text()"
        ).get()
        if college is not None:
            college = normalize_text(college)
            if college not in VALUES_NOT_AVAILABLE:
                ret["college"] = college

        # Foundation styles (optional)
        styles = profile_section.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()"
        ).get()
        if styles is not None:
            styles = normalize_text(styles)
            if styles not in VALUES_NOT_AVAILABLE:
                ret["foundation_styles"] = []
                for s in styles.split(","):
                    ret["foundation_styles"].append(s.strip())

        # Place of born (optional)
        born = profile_section.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()"
        ).get()
        if born is not None:
            born = normalize_text(born)
            if born not in VALUES_NOT_AVAILABLE:
                ret["born"] = []
                for p in born.split(","):
                    ret["born"].append(p.strip())

        # Fighting out of (optional)
        out_of = profile_section.xpath(
            "./ul/li/strong[text()='Fighting out of:']/following-sibling::span[1]/text()"
        ).get()
        if out_of is not None:
            out_of = normalize_text(out_of)
            if out_of not in VALUES_NOT_AVAILABLE:
                ret["out_of"] = []
                for o in out_of.split(","):
                    ret["out_of"].append(o.strip())

        # Head Coach (optional)
        head_coach = profile_section.xpath(
            "./ul/li/strong[text()='Head Coach:']/following-sibling::span[1]/text()"
        ).get()
        if head_coach is not None:
            head_coach = normalize_text(head_coach)
            if head_coach not in VALUES_NOT_AVAILABLE:
                ret["head_coach"] = head_coach

        # Parse results
        ret["results"] = []
        for division in [DIVISION_PRO, DIVISION_AM]:
            result_sections = response.xpath(
                f"//section[@class='fighterFightResults']/ul[@id='{division}Results']/li"
            )
            if len(result_sections) == 0:
                continue
            for result_section in result_sections:
                # Stores data of the match
                item = {"division": division}

                # Ignore inegligible matches
                txt = result_section.xpath(
                    "./div[@class='result']/div[@class='opponent']/div[@class='record nonMma']/text()"
                ).get()
                if txt is not None:
                    txt = normalize_text(txt)
                    if txt.startswith("record ineligible"):
                        continue

                # Sport of the match (must)
                sport = result_section.xpath("./@data-sport").get()
                if sport is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the sport of the match"
                    )
                    continue
                normed_sport = normalize_sport(sport)
                if normed_sport is None:
                    self.logger.error(f"Unexpected sport value: {sport}")
                    continue
                item["sport"] = normed_sport

                # Status of the match (must)
                status = result_section.xpath("./@data-status").get()
                if status is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the status of the match"
                    )
                    continue
                normed_status = normalize_status(status)
                if normed_status is None:
                    self.logger.error(f"Unexpected status value: {status}")
                    continue
                # Ignore matches with status = cancelled, upcoming, unknown, no-contest
                if normed_status in [
                    STATUS_CANCELLED,
                    STATUS_UPCOMING,
                    STATUS_UNKNOWN,
                ]:
                    continue
                item["status"] = normed_status

                # Date of the match (must)
                date = result_section.xpath(
                    "./div[@class='result']/div[@class='date']/text()"
                ).get()
                if date is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the date of the match"
                    )
                    continue
                date_normed = parse_date(date)
                if date_normed is None:
                    self.logger.error(f"Unexpected format of date: {date}")
                    continue
                item["date"] = date_normed

                # Age at the match (optional)
                if "date_of_birth" in ret:
                    item["age"] = calc_age(item["date"], ret["date_of_birth"])

                # Opponent section (must)
                opponent_section = result_section.xpath(
                    "./div[@class='result']/div[@class='opponent']/div[@class='name']/a"
                )
                if len(opponent_section) == 0:
                    continue
                item["opponent"] = {}

                # Name & url of the opponent (must)
                opponent_url = opponent_section.xpath("./@href").get()
                if opponent_url is None:
                    continue
                item["opponent"] = get_id_from_url(opponent_url)

                # Promotion of the match (optional)
                promo_url = result_section.xpath(
                    "./div[@class='details tall']/div[@class='logo']/div[@class='promotionLogo']/a/@href"
                ).get()
                if promo_url is not None:
                    promo_url = response.urljoin(promo_url)
                    item["promotion"] = get_id_from_url(promo_url)
                if "promotion" not in item:
                    promo_link_section = result_section.xpath(
                        "./div[@class='result']/div[@class='summary']/div[@class='notes']/a"
                    )
                    if len(promo_link_section) == 1:
                        title = promo_link_section.xpath("./@title").get()
                        promo_url = promo_link_section.xpath("./@href").get()
                        if title is not None:
                            title = normalize_text(title)
                            if title == "promotion page" and promo_url is not None:
                                item["promotion"] = get_id_from_url(promo_url)

                # Details of the result (optional)
                if normed_status in [
                    STATUS_WIN,
                    STATUS_LOSS,
                    STATUS_DRAW,
                    STATUS_NO_CONTEST,
                ]:
                    # Parse summary of the result
                    summary_section = result_section.xpath(
                        "./div[@class='result']/div[@class='summary']/div[@class='lead']"
                    )
                    if len(summary_section) == 0:
                        self.logger.error(
                            "Unexpected page structure: could not find summary section"
                        )
                    else:
                        txt = summary_section.xpath(
                            "./a/text()[normalize-space()]"
                        ).get()
                        if txt is None:
                            txt = summary_section.xpath(
                                "./text()[normalize-space()]"
                            ).get()
                        if txt is None:
                            self.logger.error(
                                "Unexpected page structure: could not find summary text"
                            )
                        else:
                            parsed = parse_match_summary(txt)
                            if parsed is None:
                                self.logger.error(
                                    f"Unexpected format of summary: {txt}"
                                )
                            else:
                                item["summary"] = parsed

                    # More info (optional)
                    label_sections = result_section.xpath(
                        "./div[@class='details tall']/div[@class='div']/span[@class='label']"
                    )
                    for label_section in label_sections:
                        label = label_section.xpath("./text()").get()
                        if label is None:
                            continue
                        label = normalize_text(label)
                        if label == "billing:":
                            # Billing
                            # e.g "main event", "co-main event", "prelim", etc.
                            billing = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if billing is not None:
                                normed = normalize_billing(billing)
                                if normed is not None:
                                    item["billing"] = normed
                                else:
                                    self.logger.error(
                                        f"Unexpected value of billing: {billing}"
                                    )
                        elif label == "duration:":
                            # Format of the duration
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if txt is not None:
                                format = normalize_round_format(txt)
                                if format is not None:
                                    item["format"] = format
                                else:
                                    self.logger.error(
                                        f"Unexpected format of duration: {txt}"
                                    )
                        elif label == "referee:":
                            # Name of the referee
                            referee = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if referee is not None:
                                item["referee"] = normalize_text(referee)
                        elif label == "weight:":
                            # Contracted weight limit & measured weight at weigh-in
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if txt is not None:
                                weight = parse_weight_summary(txt)
                                if weight is not None:
                                    item["weight"] = weight
                                else:
                                    self.logger.error(
                                        f"Unexpected format of weight: {txt}"
                                    )
                        elif label == "odds:":
                            # Odds of the fighter
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if txt is not None:
                                odds = parse_odds(txt)
                                if odds is not None:
                                    item["odds"] = odds
                                else:
                                    self.logger.error(
                                        f"Unexpected format of odds: {txt}"
                                    )
                        elif label == "title bout:":
                            # Title info
                            txt = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if txt is not None:
                                title_info = parse_title_info(txt)
                                if title_info is not None:
                                    item["title_info"] = title_info
                                else:
                                    self.logger.error(
                                        f"Unexpected format of title info: {txt}"
                                    )
                ret["results"].append(item)

            # Ignore fighters with no match results
            if len(ret["results"]) == 0:
                return
        return ret


def normalize_text(text: str, lower: bool = True) -> str:
    text = " ".join(text.split())
    text = text.replace("\n", "").replace("\t", "")
    if lower:
        text = text.lower()
    return text


def normalize_status(status: str) -> str:
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
    raise InvalidStatusValueError(status)


def normalize_sport(sport: str) -> str:
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
    raise InvalidSportValueError(sport)


def normalize_weight_class(weight_class: str) -> str:
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
    raise InvalidWeightClassValueError(weight_class)


def normalize_billing(billing: str) -> str:
    normed = normalize_text(billing)
    if normed in VALUES_BILLING_MAIN:
        return BILLING_MAIN
    if normed in VALUES_BILLING_CO_MAIN:
        return BILLING_CO_MAIN
    if normed in VALUES_BILLING_MAIN_CARD:
        return BILLING_MAIN_CARD
    if normed in VALUES_BILLING_PRELIM_CARD:
        return BILLING_PRELIM_CARD
    if normed in VALUES_BILLING_POSTLIM_CARD:
        return BILLING_POSTLIM_CARD
    raise InvalidBillingValueError(billing)


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
    matched = re.match(r"^(\d+) min unlim rounds", normed)
    if matched is not None:
        format = matched.group(1) + "-*"
        return format

    # 1 Round, No Limit
    matched = re.match(r"^1 round, no limit", normed)
    if matched is not None:
        return "*"
    raise InvalidRoundFormatValueError(round_format)


def parse_round_time(round_time: str) -> Dict[str, int]:
    normed = normalize_text(round_time)
    matched = re.match(r"^(\d+):(\d+)$", normed)
    if matched is not None:
        return {"m": int(matched.group(1)), "s": int(matched.group(2))}
    raise InvalidRoundTimePatternError(round_time)


def parse_round(round: str) -> int:
    normed = normalize_text(round)
    matched = re.match(r"^r(\d+)$", normed)
    if matched is not None:
        return int(matched.group(1))
    raise InvalidRoundPatternError(round)


def parse_match_summary(match_summary: str) -> Dict:
    normed = normalize_text(match_summary)
    normed_split = list(
        filter(lambda x: x != "", list(map(lambda x: x.strip(), normed.split("·"))))
    )
    normed = " · ".join(normed_split)
    n = len(normed_split)
    try:
        if n == 4:
            # Win|Loss · Head Kick & Punches · 0:40 · R1
            # No Contest · Accidental Kick to the Groin · 0:09 · R1
            matched = re.match(
                r"^(win|loss|no contest) · ([^·]+) · (\d+:\d+) · (r\d+)$", normed
            )
            if matched is not None:
                return {
                    "status": normalize_status(matched.group(1)),
                    "time": parse_round_time(matched.group(3)),
                    "round": parse_round(matched.group(4)),
                    "method": infer_method(matched.group(2)),
                    "by": matched.group(2),
                }
            # Draw · Accidental Thumb to Amoussou's Eye · 4:14 · R1
            # Draw · Draw · 5:00 · R2
            # Draw · Majority · 3:00 · R3
            matched = re.match(r"^draw · ([^·]+) · (\d+:\d+) · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": STATUS_DRAW,
                    "time": parse_round_time(matched.group(2)),
                    "round": parse_round(matched.group(3)),
                    "method": METHOD_DECISION,
                    "by": infer_decision_type(matched.group(1)),
                }
        elif n == 3:
            # Win|Loss|Draw · Decision · Unanimous|Majority|Split
            matched = re.match(
                r"^(win|loss|draw) · decision · (.+)$",
                normed,
            )
            if matched is not None:
                return {
                    "status": normalize_status(matched.group(1)),
                    "method": METHOD_DECISION,
                    "by": infer_decision_type(matched.group(2)),
                }
            # Win|Loss · Flying Knee & Punches · R1
            matched = re.match(r"^(win|loss) · ([^·]+) · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": normalize_status(matched.group(1)),
                    "round": parse_round(matched.group(3)),
                    "method": infer_method(matched.group(2)),
                    "by": matched.group(2),
                }
            # Draw · Washington Elbowed in Back of Head · R1
            matched = re.match(r"^draw · ([^·]+) · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": STATUS_DRAW,
                    "round": parse_round(matched.group(2)),
                    "method": METHOD_DECISION,
                    "by": infer_decision_type(matched.group(1)),
                }
            # No Contest · 3:15 · R1
            matched = re.match(r"^no contest · (\d+:\d+) · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": STATUS_NO_CONTEST,
                    "time": parse_round_time(matched.group(1)),
                    "round": parse_round(matched.group(2)),
                }
            # No Contest · Accidental Illegal Knee · R1
            matched = re.match(r"^no contest · ([^·]+) · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": STATUS_NO_CONTEST,
                    "round": parse_round(matched.group(2)),
                    "by": matched.group(1),
                }
        elif n == 2:
            # Win|Loss|Draw · Decision
            matched = re.match(r"^(win|loss|draw) · decision$", normed)
            if matched is not None:
                return {
                    "status": normalize_status(matched.group(1)),
                    "method": METHOD_DECISION,
                    "by": DECISION_TYPE_UNKNOWN,
                }
            # Win|Loss · KO/TKO
            matched = re.match(r"^(win|loss) · (.+)$", normed)
            if matched is not None:
                return {
                    "status": normalize_status(matched.group(1)),
                    "method": infer_method(matched.group(2)),
                    "by": matched.group(2),
                }
            # Draw · Unanimous
            if normed == "draw · unanimous":
                return {
                    "status": STATUS_DRAW,
                    "method": METHOD_DECISION,
                    "by": DECISION_TYPE_UNANIMOUS,
                }
            # No Contest · R3
            matched = re.match(r"^no contest · (r\d+)$", normed)
            if matched is not None:
                return {
                    "status": STATUS_NO_CONTEST,
                    "round": parse_round(matched.group(1)),
                }
            # No Contest · Accidental Illegal Elbow
            matched = re.match(r"^no contest · (.+)$", normed)
            if matched is not None:
                return {"status": STATUS_NO_CONTEST, "by": matched.group(1)}
        elif n == 1:
            # Win|Loss|Draw|No Contest
            return {"status": normalize_status(normed)}
    except (
        InvalidRoundTimePatternError,
        InvalidRoundPatternError,
        InvalidStatusValueError,
    ) as e:
        raise InvalidMatchSummaryPatternError(match_summary)
    raise InvalidMatchSummaryPatternError(match_summary)


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
    raise InvalidTitleInfoPatternError(title_info)


def parse_odds(odds: str) -> float:
    normed = normalize_text(odds)

    # +210 · Moderate Underdog
    # 0 · Close
    matched = re.match(r"^([\+\-])?([\d\.]+)", normed)
    if matched is not None:
        value = float(matched.group(2))
        sign = matched.group(1)
        if sign is "-":
            value *= -1
        return (value / 100) + 1.0
    raise InvalidOddsPatternError(odds)


def parse_weight_summary(weight_summary: str) -> Dict[str, float]:
    normed = normalize_text(weight_summary)
    normed_split = list(map(lambda x: x.strip(), normed.split("·")))
    ret = {}

    # Heavyweight
    # 110 kg|kgs|lb|lbs
    # 110 kg|kgs|lb|lbs (49.9 kg|kgs|lb|lbs)
    matched = re.match(r"^(.*weight|([\d\.]+) (kgs?|lbs?))", normed_split[0])
    if matched is None:
        raise InvalidWeightSummaryPatternError(weight_summary)
    if matched.group(2) is not None and matched.group(3) is not None:
        value, unit = float(matched.group(2)), matched.group(3)
        ret["class"] = to_weight_class(value, unit=unit)
        ret["limit"] = to_kg(value, unit=unit)
    else:
        try:
            weight_class = normalize_weight_class(matched.group(1))
        except InvalidWeightClassValueError as e:
            pass
        else:
            ret["class"] = weight_class
    for s in split[1:]:
        # 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        # Weigh-In 120 kg|kgs|lb|lbs (264.6 kg|kgs|lb|lbs)
        matched = re.match(r"^(weigh-in )?([\d\.]+) (kgs?|lbs?)", s)
        if matched is None:
            return None
        if matched.group(2) is None or matched.group(3) is None:
            return None
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
        return None
    return ret


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


def calc_minutes(format: str) -> int:
    ans = 0
    for s in format.split("-"):
        if s != "ot":
            ans += int(s)
    return ans


def calc_rounds(format: str) -> int:
    return len(list(filter(lambda x: x != "ot", format.split("-"))))


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


def to_weight_limit(weight_class: str) -> Union[None, float]:
    if weight_class not in WEIGHT_CLASSES:
        raise ValueError(f"invalid weight class: {weight_class}")
    if weight_class == WEIGHT_CLASS_ATOM:
        return WEIGHT_LIMIT_ATOM
    if weight_class == WEIGHT_CLASS_STRAW:
        return WEIGHT_LIMIT_STRAW
    if weight_class == WEIGHT_CLASS_FLY:
        return WEIGHT_LIMIT_FLY
    if weight_class == WEIGHT_CLASS_BANTAM:
        return WEIGHT_LIMIT_BANTAM
    if weight_class == WEIGHT_CLASS_FEATHER:
        return WEIGHT_LIMIT_FEATHER
    if weight_class == WEIGHT_CLASS_LIGHT:
        return WEIGHT_LIMIT_LIGHT
    if weight_class == WEIGHT_CLASS_SUPER_LIGHT:
        return WEIGHT_LIMIT_SUPER_LIGHT
    if weight_class == WEIGHT_CLASS_WELTER:
        return WEIGHT_LIMIT_WELTER
    if weight_class == WEIGHT_CLASS_SUPER_WELTER:
        return WEIGHT_LIMIT_SUPER_WELTER
    if weight_class == WEIGHT_CLASS_MIDDLE:
        return WEIGHT_LIMIT_MIDDLE
    if weight_class == WEIGHT_CLASS_SUPER_MIDDLE:
        return WEIGHT_LIMIT_SUPER_MIDDLE
    if weight_class == WEIGHT_CLASS_LIGHT_HEAVY:
        return WEIGHT_LIMIT_LIGHT_HEAVY
    if weight_class == WEIGHT_CLASS_CRUISER:
        return WEIGHT_LIMIT_CRUISER
    if weight_class == WEIGHT_CLASS_HEAVY:
        return WEIGHT_LIMIT_HEAVY
    return WEIGHT_LIMIT_SUPER_HEAVY


def to_meter(feet: float, inch: float) -> float:
    return feet * 0.3048 + inch * 0.0254


def to_kg(value: float, unit: str = "lb") -> float:
    if unit not in ["kg", "kgs", "lb", "lbs"]:
        raise ValueError(f"Unsupported unit: {unit}")
    if unit.startswith("lb"):
        return value * 0.453592
    return value


def get_id_from_url(url: str) -> str:
    return url.split("/")[-1]


def infer_method(by: str) -> str:
    normed = normalize_text(by)
    if normed == "decision":
        return METHOD_DECISION
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
        return METHOD_KO_TKO
    return METHOD_SUBMISSION


def infer_decision_type(decision: str) -> str:
    normed = normalize_text(decision)
    if "unanimous" in normed:
        return DECISION_TYPE_UNANIMOUS
    if "majority" in normed:
        return DECISION_TYPE_MAJORITY
    if "split" in normed or "spilt" in normed or "spit" in normed:
        return DECISION_TYPE_SPLIT
    if "technical" in normed or "illegal" in normed or "accidental" in normed:
        return DECISION_TYPE_TECHNICAL
    if "injury" in normed or "medical" in normed or "doctor" in normed:
        return DECISION_TYPE_INJURY
    if "time limit" in normed:
        return DECISION_TYPE_TIMELIMIT
    if "points" in normed:
        return DECISION_TYPE_POINTS
    return DECISION_TYPE_UNKNOWN
