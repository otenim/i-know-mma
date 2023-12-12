import scrapy
import re
from scrapy.http import TextResponse, Request
from collections.abc import Generator
from . import consts
from .errors import NormalizeError, ParseError
from .utils import (
    normalize_text,
    normalize_sport,
    normalize_status,
    normalize_date,
    normalize_weight_class,
    normalize_billing,
    normalize_round_format,
    parse_last_weigh_in,
    parse_match_summary,
    parse_record,
    parse_weight_summary,
    parse_odds,
    parse_title_info,
    to_meter,
    calc_age,
)


class FightersSpider(scrapy.Spider):
    name = "fighters"
    start_urls = ["https://www.tapology.com/search"]

    def __init__(
        self,
        min_mma_matches: int = 1,
        ignore_am_mma_fighters: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super(FightersSpider, self).__init__(*args, **kwargs)
        if min_mma_matches < 0:
            raise ValueError(f"min_mma_matches expects >= 0 but {min_mma_matches}")
        self.min_mma_matches = min_mma_matches
        self.ignore_am_mma_fighters = ignore_am_mma_fighters

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

    def parse_fighter(self, response: TextResponse) -> dict | None:
        ret = {}

        # Fighter ID (must)
        ret["url"] = response.url

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

        # Pro mma record (optional)
        career_record = profile_section.xpath(
            "./ul/li/strong[text()='Pro MMA Record:']/following-sibling::span[1]/text()"
        ).get()
        if career_record is not None:
            try:
                ret["career_record"] = parse_record(career_record)
            except ParseError as e:
                self.logger.error(e)

        # Date of birth (optional)
        date_of_birth = profile_section.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()"
        ).get()
        if date_of_birth is not None:
            date_of_birth = normalize_text(date_of_birth)
            if date_of_birth not in consts.VALUES_NOT_AVAILABLE:
                try:
                    ret["date_of_birth"] = normalize_date(date_of_birth)
                except NormalizeError as e:
                    self.logger.error(e)

        # Weight class (optional)
        weight_class = profile_section.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()"
        ).get()
        if weight_class is not None:
            try:
                ret["weight_class"] = normalize_weight_class(weight_class)
            except NormalizeError as e:
                self.logger.error(e)

        # Last weigh-in (optional)
        last_weigh_in = profile_section.xpath(
            "./ul/li/strong[text()='| Last Weigh-In:']/following-sibling::span[1]/text()"
        ).get()
        if last_weigh_in is not None:
            try:
                parsed = parse_last_weigh_in(last_weigh_in)
                if parsed is not None:
                    ret["last_weigh_in"] = parsed
            except ParseError as e:
                self.logger.error(e)

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
                ret["affiliation"] = response.urljoin(url)

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
            if college not in consts.VALUES_NOT_AVAILABLE:
                ret["college"] = college

        # Foundation styles (optional)
        styles = profile_section.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()"
        ).get()
        if styles is not None:
            styles = normalize_text(styles)
            if styles not in consts.VALUES_NOT_AVAILABLE:
                ret["foundation_styles"] = []
                for s in styles.split(","):
                    ret["foundation_styles"].append(s.strip())

        # Place of born (optional)
        born = profile_section.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()"
        ).get()
        if born is not None:
            born = normalize_text(born)
            if born not in consts.VALUES_NOT_AVAILABLE:
                ret["born"] = []
                for p in born.split(","):
                    ret["born"].append(p.strip())

        # Fighting out of (optional)
        out_of = profile_section.xpath(
            "./ul/li/strong[text()='Fighting out of:']/following-sibling::span[1]/text()"
        ).get()
        if out_of is not None:
            out_of = normalize_text(out_of)
            if out_of not in consts.VALUES_NOT_AVAILABLE:
                ret["out_of"] = []
                for o in out_of.split(","):
                    ret["out_of"].append(o.strip())

        # Head Coach (optional)
        head_coach = profile_section.xpath(
            "./ul/li/strong[text()='Head Coach:']/following-sibling::span[1]/text()"
        ).get()
        if head_coach is not None:
            head_coach = normalize_text(head_coach)
            if head_coach not in consts.VALUES_NOT_AVAILABLE:
                ret["head_coach"] = head_coach

        # Parse results
        ret["results"] = []
        for division in [consts.DIVISION_PRO, consts.DIVISION_AM]:
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
                try:
                    item["sport"] = normalize_sport(sport)
                except NormalizeError as e:
                    self.logger.error(e)
                    continue

                # Status of the match (must)
                status = result_section.xpath("./@data-status").get()
                if status is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the status of the match"
                    )
                    continue
                try:
                    item["status"] = normalize_status(status)
                except NormalizeError as e:
                    self.logger.error(e)
                    continue

                # Ignore matches with status = cancelled, upcoming, unknown
                if item["status"] in [
                    consts.STATUS_CANCELLED,
                    consts.STATUS_UPCOMING,
                    consts.STATUS_UNKNOWN,
                ]:
                    continue

                # Date of the match (must)
                date = result_section.xpath(
                    "./div[@class='result']/div[@class='date']/text()"
                ).get()
                if date is None:
                    self.logger.error(
                        "Unexpected page structure: could not identify the date of the match"
                    )
                    continue
                try:
                    item["date"] = normalize_date(date)
                except NormalizeError as e:
                    self.logger.error(e)
                    continue

                # Calc age at the match (optional)
                if "date_of_birth" in ret:
                    item["age"] = calc_age(item["date"], ret["date_of_birth"])

                # Opponent section (must)
                opponent_section = result_section.xpath(
                    "./div[@class='result']/div[@class='opponent']"
                )
                if len(opponent_section) == 0:
                    self.logger.error(
                        "Unexpected page structure: could not find opponent section"
                    )
                    continue
                item["opponent"] = {}

                # Name & url of the opponent (must)
                opponent_url = opponent_section.xpath(
                    "./div[@class='name']/a/@href"
                ).get()
                if opponent_url is None:
                    continue
                item["opponent"] = response.urljoin(opponent_url)

                # Record of the fighter (optional)
                record = opponent_section.xpath(
                    "./div[@class='record']/span[@title='Fighter Record Before Fight']/text()"
                ).get()
                if record is not None:
                    try:
                        item["record"] = parse_record(record)
                    except ParseError as e:
                        self.logger.error(e)

                # Promotion of the match (optional)
                promo_url = result_section.xpath(
                    "./div[@class='details tall']/div[@class='logo']/div[@class='promotionLogo']/a/@href"
                ).get()
                if promo_url is not None:
                    item["promotion"] = response.urljoin(promo_url)
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
                                item["promotion"] = response.urljoin(promo_url)

                # Event of the match (optional)
                event_url = result_section.xpath(
                    "./div[@class='result']/div[@class='summary']/div[@class='notes']/a[@title='Event Page']/@href"
                ).get()
                if event_url is not None:
                    item["event"] = response.urljoin(event_url)

                # Details of the result (optional)
                if item["status"] in [
                    consts.STATUS_WIN,
                    consts.STATUS_LOSS,
                    consts.STATUS_DRAW,
                    consts.STATUS_NC,
                ]:
                    # Summary of the match (must)
                    match_summary_section = result_section.xpath(
                        "./div[@class='result']/div[@class='summary']/div[@class='lead']"
                    )
                    if len(match_summary_section) == 0:
                        self.logger.error(
                            "Unexpected page structure: could not find summary section"
                        )
                        continue
                    match_summary = match_summary_section.xpath("./a/text()").get()
                    if match_summary is None:
                        # No link
                        match_summary = match_summary_section.xpath("./text()").get()
                    if match_summary is None:
                        self.logger.error(
                            "Unexpected page structure: could not find match summary text"
                        )
                        continue
                    try:
                        summary = parse_match_summary(
                            item["sport"], item["status"], match_summary
                        )
                        for k, v in summary.items():
                            if k != "status":
                                item[k] = v
                    except ParseError as e:
                        self.logger.error(e)

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
                            # Billing of the match
                            billing = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if billing is not None:
                                try:
                                    item["billing"] = normalize_billing(billing)
                                except NormalizeError as e:
                                    self.logger.error(e)
                        elif label == "duration:":
                            # Round format of the match
                            round_format = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if round_format is not None:
                                try:
                                    item["round_format"] = normalize_round_format(
                                        round_format
                                    )
                                except NormalizeError as e:
                                    self.logger.error(e)
                        elif label == "referee:":
                            # Referee of the match
                            referee = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if referee is not None:
                                item["referee"] = normalize_text(referee)
                        elif label == "weight:":
                            # Weight infomation of the match
                            weight_summary = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if weight_summary is not None:
                                try:
                                    item["weight"] = parse_weight_summary(
                                        weight_summary
                                    )
                                except ParseError as e:
                                    pattern = normalize_text(e.text)
                                    if (
                                        "open" in pattern
                                        or "catch" in pattern
                                        or "numeric" in pattern
                                    ):
                                        pass
                                    else:
                                        self.logger.error(e)
                        elif label == "odds:":
                            # Odds of the fighter
                            odds = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if odds is not None:
                                try:
                                    item["odds"] = parse_odds(odds)
                                except ParseError as e:
                                    self.logger.error(e)
                        elif label == "title bout:":
                            # Title infomation
                            title_info = label_section.xpath(
                                "./following-sibling::span[1]/text()"
                            ).get()
                            if title_info is not None:
                                try:
                                    item["title_info"] = parse_title_info(title_info)
                                except ParseError as e:
                                    self.logger.error(e)
                ret["results"].append(item)

            # Ignore fighters with no match results
            if len(ret["results"]) == 0:
                return
        return ret
