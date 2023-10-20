import scrapy
import re
from scrapy.http import Request, TextResponse
from collections.abc import Generator
from typing import Tuple, Union


class FightersSpider(scrapy.Spider):
    name = "fighters"
    start_urls = ["https://www.tapology.com/search"]

    def parse(self, response: TextResponse) -> Generator[Request, None, None]:
        fighters_by_weight_class = response.xpath(
            "//div[@class='siteSearchFightersByWeightClass']/dd/a/@href"
        ).getall()
        if len(fighters_by_weight_class) == 0:
            self.logger.critical(
                "No weight classes were found. Make sure if this is an expected behavior"
            )
        else:
            self.logger.info(
                f"{len(fighters_by_weight_class)} different weight classes were found"
            )
        for link in fighters_by_weight_class:
            yield response.follow(link, callback=self.parse_fighter_list)

    def parse_fighter_list(
        self, response: TextResponse
    ) -> Generator[Request, None, None]:
        fighters = response.xpath("//table[@class='siteSearchResults']/tr")[1:]
        count = 0
        for fighter in fighters:
            mma_rec = fighter.xpath("./td[7]/text()").get()
            if not mma_rec:
                self.logger.error("No mma record was found")
                continue
            mma_rec = mma_rec.strip()
            matched = re.match(r"^(?:(Am)\s)?(\d+)-(\d+)-(\d+)(?:,\s\d+ NC)?$", mma_rec)
            if not matched:
                self.logger.error(f"Unexpected mma record format was found: {mma_rec}")
                continue
            if matched.group(1) == "Am":
                # Skip amateur fighters
                continue
            n = int(matched.group(2)) + int(matched.group(3)) + int(matched.group(4))
            if n <= 2:
                # Skip pro fighters who has too little game experience (<= 2 pro mma matches)
                continue
            link = fighter.xpath("./td[1]/a/@href").get()
            if link:
                yield response.follow(link, callback=self.parse_fighter)
            else:
                self.logger.error("No link was found to this fighter's page")
            count += 1
        self.logger.info(f"Crawled {count} different fighters' pages")

        # Move to next page
        next_page = response.xpath(
            "//span[@class='moreLink']/nav[@class='pagination']/span[@class='next']/a/@href"
        ).get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_fighter_list)

    def parse_fighter(self, response: TextResponse):
        ret = {}

        # Fighter url (must)
        ret["url"] = response.url

        # Fighter name (must)
        name = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h1[not(@*)]/text()"
        ).get()
        if not name:
            self.logger.error("Fighter's name was not found")
            return
        ret["name"] = name.strip()

        # Stores profile data of the fighter
        profile = {}

        # Fighter nickname
        fighter_nickname = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h4[@class='preTitle nickname']/text()"
        ).re_first(r"\"(.*)\"")
        if fighter_nickname:
            profile["nickname"] = fighter_nickname.strip()

        # Details section (must)
        details_section = response.xpath("//div[@class='details details_two_columns']")
        if len(details_section) == 0:
            self.logger.error("Details section was not found")
            return

        # Date of birth (optional)
        date_of_birth = details_section.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()"
        ).re(r"(\d{4})\.(\d{2})\.(\d{2})")
        if len(date_of_birth) == 3:
            profile["date_of_birth"] = {
                "y": int(date_of_birth[0]),
                "m": int(date_of_birth[1]),
                "d": int(date_of_birth[2]),
            }

        # Weight class (optional)
        weight_class = details_section.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()"
        ).get()
        if weight_class:
            profile["weight_class"] = weight_class.strip()

        # Affiliation (optional)
        affili_section = details_section.xpath(
            "./ul/li/strong[text()='Affiliation:']/following-sibling::span[1]/a"
        )
        if len(affili_section) == 1:
            url = affili_section.xpath("./@href").get()
            if url:
                name = affili_section.xpath("./text()").get()
                if name:
                    profile["affiliation"] = {
                        "url": url.strip(),
                        "name": name.strip(),
                    }

        # Height (optional)
        # Format: "5\'9\" (175cm)"
        height = details_section.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\'([\d\.]+)\"")
        if len(height) == 2:
            profile["height"] = to_meter(float(height[0]), float(height[1]))

        # Reach (optional)
        # Format: "74.0\" (188cm)"
        reach = details_section.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\"")
        if len(reach) == 1:
            profile["reach"] = to_meter(0, float(reach[0]))

        # Place of birth
        place_of_birth = details_section.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()"
        ).get()
        if place_of_birth:
            place_of_birth = place_of_birth.strip()
            if place_of_birth != "N/A":
                profile["place_of_birth"] = []
                for p in place_of_birth.split(","):
                    profile["place_of_birth"].append(p.strip())

        # Fighting out of
        out_of = details_section.xpath(
            "./ul/li/strong[text()='Fighting out of:']/following-sibling::span[1]/text()"
        ).get()
        if out_of:
            out_of = out_of.strip()
            if out_of != "N/A":
                profile["out_of"] = []
                for o in out_of.split(","):
                    profile["out_of"].append(o.strip())

        # College the fighter graduated from
        college = details_section.xpath(
            "./ul/li/strong[text()='College:']/following-sibling::span[1]/text()"
        ).get()
        if college:
            college = college.strip()
            if college != "N/A":
                profile["college"] = college

        # Foundation styles
        foundation_styles = details_section.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()"
        ).get()
        if foundation_styles:
            foundation_styles = foundation_styles.strip()
            if foundation_styles != "N/A":
                profile["foundation_styles"] = []
                for s in foundation_styles.split(","):
                    profile["foundation_styles"].append(s.strip())

        # Head Coach
        head_coach = details_section.xpath(
            "./ul/li/strong[text()='Head Coach:']/following-sibling::span[1]/text()"
        ).get()
        if head_coach:
            head_coach = head_coach.strip()
            if head_coach != "N/A":
                profile["head_coach"] = head_coach

        # Other Coaches
        other_coaches = details_section.xpath(
            "./ul/li/strong[text()='Other Coaches:']/following-sibling::span[1]/text()"
        ).get()
        if other_coaches:
            other_coaches = other_coaches.strip()
            if other_coaches != "N/A":
                profile["other_coaches"] = []
                for c in other_coaches.split(","):
                    profile["other_coaches"].append(c.strip())

        # Set profile to the output dict
        ret["profile"] = profile

        # Pro records
        pro_rec_sections = response.xpath(
            "//section[@class='fighterFightResults']/ul[@id='proResults']/li"
        )
        if len(pro_rec_sections) > 0:
            ret["pro_records"] = []
            for pro_rec_section in pro_rec_sections:
                # Stores each record
                item = {}

                # NOTE: Skip ineligible mma bouts
                txt = pro_rec_section.xpath(
                    "./div[@class='result']/div[@class='opponent']/div[@class='record nonMma']/text()"
                ).get()
                if txt and txt.strip() == "Record Ineligible MMA":
                    continue

                # Sport of the bout (must)
                sport = pro_rec_section.xpath("./@data-sport").get()
                if not sport:
                    self.logger.error("Could not identify the sport of the bout")
                    continue
                sport = sport.strip()
                if sport not in [
                    "mma",
                    "knuckle_mma",
                    "boxing",
                    "boxing_cage",
                    "knuckle",
                    "kickboxing",
                    "muay",
                    "karate",
                    "sanda",
                    "lethwei",
                    "grappling",
                    "shootboxing",
                    "wrestling",
                    "custom",
                ]:
                    self.logger.warning(f"Unrecognized sport was detected: {sport}")
                if sport == "custom":
                    # NOTE: Skip custom-ruled bout records
                    continue
                item["sport"] = sport

                # Bout status (must)
                status = pro_rec_section.xpath("./@data-status").get()
                if not status:
                    self.logger.error("Bout status is not provided")
                    continue
                status = status.strip()
                if status not in [
                    "loss",
                    "win",
                    "cancelled",
                    "draw",
                    "upcoming",
                    "no contest",
                    "unknown",
                ]:
                    self.logger.warning(f"Unrecognized status was detected: {status}")
                if status == "win":
                    item["status"] = "w"
                elif status == "loss":
                    item["status"] = "l"
                elif status == "draw":
                    item["status"] = "d"
                else:
                    # NOTE: Skip cancelled, no-contest, status-unknown, and cancelled bout records
                    continue

                # Opponent fighter (must)
                opponent_section = pro_rec_section.xpath(
                    "./div[@class='result']/div[@class='opponent']"
                )
                if len(opponent_section) == 0:
                    self.logger.error("No opponent data is provided")
                    continue
                item["opponent"] = {}

                # Opponent name (at least name must be provided)
                section = opponent_section.xpath("./div[@class='name']/a")
                has_opponent_link = False if len(section) == 0 else True
                if has_opponent_link:
                    link = section.xpath("./@href").get()
                    name = section.xpath("./text()").get()
                    if link:
                        item["opponent"]["url"] = link.strip()
                    if name:
                        item["opponent"]["name"] = name.strip()
                else:
                    name = opponent_section.xpath(
                        "./div[@class='name']/span/text()"
                    ).get()
                    if name:
                        item["opponent"]["name"] = name.strip()

                # Record before the fight
                # NOTE: available when the bout is an official mma bout
                is_official_mma_bout = (
                    True
                    if len(opponent_section.xpath("./div[@class='record nonMma']")) == 0
                    else False
                )
                if is_official_mma_bout and item["status"] != "cancelled":
                    section = opponent_section.xpath("./div[@class='record']")
                    fighter_record = section.xpath(
                        "./span[@title='Fighter Record Before Fight']/text()"
                    ).re(r"(\d+)-(\d+)-(\d+)")
                    if len(fighter_record) == 3:
                        item["record_before_fight"] = {
                            "w": int(fighter_record[0].strip()),
                            "l": int(fighter_record[1].strip()),
                            "d": int(fighter_record[2].strip()),
                        }

                    # NOTE: Opponent record is provided
                    # when there is a link to the opponent
                    if has_opponent_link:
                        opponent_record = section.xpath(
                            "./span[@title='Opponent Record Before Fight']/text()"
                        ).re(r"(\d+)-(\d+)-(\d+)")
                        if len(opponent_record) == 3:
                            item["opponent"]["record_before_fight"] = {
                                "w": int(opponent_record[0].strip()),
                                "l": int(opponent_record[1].strip()),
                                "d": int(opponent_record[2].strip()),
                            }

                # Bout summary
                if item["status"] in ["w", "l"]:
                    summary_lead_section = pro_rec_section.xpath(
                        "./div[@class='result']/div[@class='summary']/div[@class='lead']"
                    )
                    if len(summary_lead_section) == 0:
                        self.logger.error("No summary lead section is provided")
                        continue
                    txt = summary_lead_section.xpath("./a/text()").get()
                    if not txt:
                        # No links to the summary lead
                        txt = summary_lead_section.xpath("./text()").get()
                        if not txt:
                            self.logger.error("No summary lead text is provided")
                    li = list(
                        filter(
                            lambda x: x != "",
                            map(lambda x: x.strip(), txt.split("·")),
                        )
                    )
                    n = len(li)
                    if not (1 <= n <= 4):
                        self.logger.error(f"Unexpected summary lead format: {txt}")
                        continue

                    # Parse summary lead
                    item["details"] = {}
                    if n == 1:
                        # (Win|Loss)
                        continue
                    elif n == 2:
                        # (Win|Loss), finish
                        item["details"]["ended_by"] = {
                            "type": infer(li[1]),
                            "detail": li[1],
                        }
                    elif n == 3:
                        # (Win|Loss), finish, round
                        # (Win|Loss), Decision, (Majority|Unanimous|Split)
                        t = infer(li[1])
                        if t == "decision":
                            item["details"]["ended_by"] = {"type": t, "detail": li[2]}
                        else:
                            item["details"]["ended_by"] = {
                                "type": t,
                                "detail": li[1],
                            }
                            item["details"]["ended_at"] = {"round": parse_round(li[2])}
                    else:
                        # (Win|Loss), finish, time, round
                        item["details"]["ended_by"] = {
                            "type": infer(li[1]),
                            "detail": li[1],
                        }
                        item["details"]["ended_at"] = {
                            "round": parse_round(li[3]),
                            "time": parse_time(li[2]),
                        }

                # Bout details
                # label_sels = pro_rec_section.xpath(
                #     "./div[@class='details tall']/div[@class='div']/span[@class='label']"
                # )
                # for label_sel in label_sels:
                #     txt = label_sel.xpath("./text()").get()
                #     assert txt is not None
                #     txt = txt.strip()
                #     if txt == "Billing:":
                #         bill = label_sel.xpath(
                #             "./following-sibling::span[1]/text()"
                #         ).get()
                #         assert bill is not None
                #         item["billing"] = bill.strip()
                #     elif txt == "Duration:":
                #         duration = label_sel.xpath(
                #             "./following-sibling::span[1]/text()"
                #         ).re(r"(\d+)\sx\s(\d+)")
                #         if len(duration) == 2:
                #             item["duration"] = duration
                #     elif txt == "Referee:":
                #         referee = label_sel.xpath(
                #             "./following-sibling::span[1]/text()"
                #         ).get()
                #         assert referee is not None
                #         item["referee"] = referee.strip()
                #     elif txt == "Weight:":
                #         # Lightweight · 154 lbs (70.0 kg)
                #         # Lightweight · 155 lbs (70.3 kg) · Weigh-In 155.0 lbs (70.3 kgs)
                #         # 57 kg · 57 kg (125.7 lbs)
                #         # 57 kg · 57 kg (125.0 lbs) · Weigh-In 124.7 lbs (56.6 kgs)
                #         pass

                ret["pro_records"].append(item)
        return ret


def parse_time(time: str) -> Union[Tuple[int, int], None]:
    out = re.match(r"^(\d+):(\d+)$", time.strip())
    if out is None:
        return None
    return (int(out.group(1)), int(out.group(2)))


def parse_round(round: str) -> Union[int, None]:
    out = re.match(r"^R([1-9])$", round.strip())
    if out is None:
        return None
    return int(out.group(1))


def to_meter(feet: float, inch: float) -> float:
    return feet * 0.3048 + inch * 0.0254


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
