import scrapy
import re
from scrapy.http import Request, TextResponse
from collections.abc import Generator
from typing import Tuple, Union


class FightersSpider(scrapy.Spider):
    name = "fighters"
    start_urls = ["https://www.tapology.com/search"]

    def parse(self, response: TextResponse) -> Generator[Request, None, None]:
        fighter_list_links = response.xpath(
            "//div[@class='siteSearchFightersByWeightClass']/dd/a/@href"
        ).getall()
        for link in fighter_list_links:
            yield response.follow(link, callback=self.parse_fighter_list)

    def parse_fighter_list(
        self, response: TextResponse
    ) -> Generator[Request, None, None]:
        rows = response.xpath("//table[@class='siteSearchResults']/tr")[1:]
        # Schema:
        # 1: fighter name & link
        # 2: space
        # 3: height
        # 4: space
        # 5: weight class
        # 6: space
        # 7: record
        # 8: space
        # 9: nation flag (image)
        for row in rows:
            # Filter out fighters whose pro mma bout count is <= 2
            pro_mma_record = row.xpath("./td[7]/text()").re(r"^(\d+)-(\d+)-(\d+)$")
            if len(pro_mma_record) == 3:
                n = sum(map(lambda x: int(x), pro_mma_record))
                if n > 2:
                    # Get figher page link
                    link = row.xpath("./td[1]/a/@href").get()
                    if link is not None:
                        yield response.follow(link, callback=self.parse_fighter)
        # Move to next page if there it is
        next_page = response.xpath(
            "//span[@class='moreLink']/nav[@class='pagination']/span[@class='next']/a/@href"
        ).get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_fighter_list)

    def parse_fighter(self, response: TextResponse):
        ret = {}

        # Fighter url (must)
        if response.url is None:
            return
        ret["url"] = response.url

        # Fighter name (must)
        fighter_name = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h1[not(@*)]/text()"
        ).get()
        assert fighter_name is not None
        ret["name"] = fighter_name.strip()

        # Fighter nickname
        fighter_nickname = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h4[@class='preTitle nickname']/text()"
        ).re_first(r"\"(.*)\"")
        if fighter_nickname is not None:
            ret["nickname"] = fighter_nickname.strip()

        # Details section (must)
        details_sel = response.xpath("//div[@class='details details_two_columns']")
        if len(details_sel) == 0:
            return

        # Date of birth (optional)
        date_of_birth = details_sel.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()"
        ).re(r"(\d{4})\.(\d{2})\.(\d{2})")
        if len(date_of_birth) == 3:
            ret["date_of_birth"] = {
                "y": int(date_of_birth[0]),
                "m": int(date_of_birth[1]),
                "d": int(date_of_birth[2]),
            }

        # Weight class (optional)
        weight_class = details_sel.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()"
        ).get()
        if weight_class is not None:
            ret["weight_class"] = weight_class.strip()

        # Affiliation (optional)
        affili_sel = details_sel.xpath(
            "./ul/li/strong[text()='Affiliation:']/following-sibling::span[1]/a"
        )
        if len(affili_sel) == 1:
            affili_url = affili_sel.xpath("./@href").get()
            if affili_url is not None:
                affili_name = affili_sel.xpath("./text()").get()
                if affili_name is not None:
                    ret["affiliation"] = {
                        "url": affili_url.strip(),
                        "name": affili_name.strip(),
                    }

        # Height (optional)
        # Format: "5\'9\" (175cm)"
        height = details_sel.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\'([\d\.]+)\"")
        if len(height) == 2:
            feet, inch = float(height[0]), float(height[1])
            ret["height"] = to_meter(feet, inch)

        # Reach (optional)
        # Format: "74.0\" (188cm)"
        reach = details_sel.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\"")
        if len(reach) == 1:
            inch = float(reach[0])
            ret["reach"] = to_meter(0, inch)

        # Place of birth
        place_of_birth = details_sel.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()"
        ).get()
        if place_of_birth is not None:
            place_of_birth = place_of_birth.strip()
            if place_of_birth != "N/A":
                ret["place_of_birth"] = []
                for p in place_of_birth.split(","):
                    ret["place_of_birth"].append(p.strip())

        # Fighting out of
        out_of = details_sel.xpath(
            "./ul/li/strong[text()='Fighting out of:']/following-sibling::span[1]/text()"
        ).get()
        if out_of is not None:
            out_of = out_of.strip()
            if out_of != "N/A":
                ret["out_of"] = []
                for o in out_of.split(","):
                    ret["out_of"].append(o.strip())

        # College the fighter graduated from
        college = details_sel.xpath(
            "./ul/li/strong[text()='College:']/following-sibling::span[1]/text()"
        ).get()
        if college is not None:
            college = college.strip()
            if college != "N/A":
                ret["college"] = college

        # Foundation styles
        foundation_styles = details_sel.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()"
        ).get()
        if foundation_styles is not None:
            foundation_styles = foundation_styles.strip()
            if foundation_styles != "N/A":
                ret["foundation_styles"] = []
                for s in foundation_styles.split(","):
                    ret["foundation_styles"].append(s.strip())

        # Head Coach
        head_coach = details_sel.xpath(
            "./ul/li/strong[text()='Head Coach:']/following-sibling::span[1]/text()"
        ).get()
        if head_coach is not None:
            head_coach = head_coach.strip()
            if head_coach != "N/A":
                ret["head_coach"] = head_coach

        # Other Coaches
        other_coaches = details_sel.xpath(
            "./ul/li/strong[text()='Other Coaches:']/following-sibling::span[1]/text()"
        ).get()
        if other_coaches is not None:
            other_coaches = other_coaches.strip()
            if other_coaches != "N/A":
                ret["other_coaches"] = []
                for c in other_coaches.split(","):
                    ret["other_coaches"].append(c.strip())

        # Pro records
        pro_record_sels = response.xpath(
            "//section[@class='fighterFightResults']/ul[@id='proResults']/li"
        )
        if len(pro_record_sels) > 0:
            ret["pro_records"] = []
            for pro_record_sel in pro_record_sels:
                item = {}

                # Skip ineligible mma bouts
                txt = pro_record_sel.xpath(
                    "./div[@class='result']/div[@class='opponent']/div[@class='record nonMma']/text()"
                ).get()
                if txt is not None:
                    if txt.strip() == "Record Ineligible MMA":
                        continue

                # Genre of the bout (must)
                # Skip custom rule bouts
                bout_sport = pro_record_sel.xpath("./@data-sport").get()
                bout_sport = bout_sport.strip()
                assert bout_sport is not None and bout_sport in [
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
                ]
                if bout_sport == "custom":
                    continue
                item["sport"] = bout_sport

                # Bout result (must)
                # Skip no-contest, upcoming, result-unknown, and cancelled bouts
                bout_result = pro_record_sel.xpath("./@data-status").get()
                bout_result = bout_result.strip()
                assert bout_result is not None and bout_result in [
                    "loss",
                    "win",
                    "cancelled",
                    "draw",
                    "upcoming",
                    "no contest",
                    "unknown",
                ]
                if bout_result == "win":
                    item["result"] = "w"
                elif bout_result == "loss":
                    item["result"] = "l"
                elif bout_result == "draw":
                    item["result"] = "d"
                else:  # "upcoming" or "unknown" or "cancelled" or "no contest"
                    continue

                # Opponent fighter (must)
                opponent_sel = pro_record_sel.xpath(
                    "./div[@class='result']/div[@class='opponent']"
                )
                if len(opponent_sel) != 1:
                    continue
                item["opponent"] = {}

                # Opponent name (at least name must be provided)
                sel = opponent_sel.xpath("./div[@class='name']/a")
                has_opponent_link = False if len(sel) == 0 else True
                if has_opponent_link:
                    link = sel.xpath("./@href").get()
                    name = sel.xpath("./text()").get()
                    if link:
                        item["opponent"]["url"] = link.strip()
                    if name:
                        item["opponent"]["name"] = name.strip()
                else:
                    name = opponent_sel.xpath("./div[@class='name']/span/text()").get()
                    if name:
                        item["opponent"]["name"] = name.strip()

                # Record before the fight
                # NOTE: only available when the bout is an official mma bout and was not cancelled
                is_official_mma_bout = (
                    True
                    if len(opponent_sel.xpath("./div[@class='record nonMma']")) == 0
                    else False
                )
                if is_official_mma_bout and bout_result != "cancelled":
                    record_sel = opponent_sel.xpath("./div[@class='record']")
                    fighter_record = record_sel.xpath(
                        "./span[@title='Fighter Record Before Fight']/text()"
                    ).re(r"(\d+)-(\d+)-(\d+)")
                    if len(fighter_record) == 3:
                        item["record_before_fight"] = {
                            "w": int(fighter_record[0].strip()),
                            "l": int(fighter_record[1].strip()),
                            "d": int(fighter_record[2].strip()),
                        }

                    # NOTE: Opponent record is provided
                    # when a link to the opponent is provided
                    if has_opponent_link:
                        opponent_record = record_sel.xpath(
                            "./span[@title='Opponent Record Before Fight']/text()"
                        ).re(r"(\d+)-(\d+)-(\d+)")
                        if len(opponent_record) == 3:
                            item["opponent"]["record_before_fight"] = {
                                "w": int(opponent_record[0].strip()),
                                "l": int(opponent_record[1].strip()),
                                "d": int(opponent_record[2].strip()),
                            }

                # Bout summary
                if bout_result in ["win", "loss"]:
                    summary_sel = pro_record_sel.xpath(
                        "./div[@class='result']/div[@class='summary']/div[@class='lead']"
                    )
                    assert summary_sel is not None
                    summary = summary_sel.xpath("./a/text()").get()
                    if summary is None:
                        # When the section has no links
                        summary = summary_sel.xpath("./text()").get()
                        assert summary is not None
                    li = list(
                        filter(
                            lambda x: x != "",
                            map(lambda x: x.strip(), summary.split("·")),
                        )
                    )
                    n = len(li)
                    assert 1 <= len(li) <= 4
                    if n == 1:
                        # (Win|Loss)
                        continue
                    elif n == 2:
                        # (Win|Loss), finish
                        item["by"] = infer(li[1])
                        item["detail"] = li[1]
                    elif n == 3:
                        # (Win|Loss), finish, round
                        # (Win|Loss), Decision, (Majority|Unanimous|Split)
                        item["by"] = infer(li[1])
                        if item["by"] == "decision":
                            item["detail"] = li[2]
                        else:
                            item["detail"] = li[1]
                            item["round"] = parse_round(li[2])
                    else:  # n == 4
                        # (Win|Loss), finish, time, round
                        item["by"] = infer(li[1])
                        item["detail"] = li[1]
                        item["time"] = parse_time(li[2])
                        item["round"] = parse_round(li[3])

                # Bout details
                label_sels = pro_record_sel.xpath(
                    "./div[@class='details tall']/div[@class='div']/span[@class='label']"
                )
                for label_sel in label_sels:
                    txt = label_sel.xpath("./text()").get()
                    assert txt is not None
                    txt = txt.strip()
                    if txt == "Billing:":
                        bill = label_sel.xpath(
                            "./following-sibling::span[1]/text()"
                        ).get()
                        assert bill is not None
                        item["billing"] = bill.strip()
                    elif txt == "Duration:":
                        duration = label_sel.xpath(
                            "./following-sibling::span[1]/text()"
                        ).re(r"(\d+)\sx\s(\d+)")
                        if len(duration) == 2:
                            item["duration"] = duration
                    elif txt == "Referee:":
                        referee = label_sel.xpath(
                            "./following-sibling::span[1]/text()"
                        ).get()
                        assert referee is not None
                        item["referee"] = referee.strip()
                    elif txt == "Weight:":
                        # Lightweight · 154 lbs (70.0 kg)
                        # Lightweight · 155 lbs (70.3 kg) · Weigh-In 155.0 lbs (70.3 kgs)
                        # 57 kg · 57 kg (125.7 lbs)
                        # 57 kg · 57 kg (125.0 lbs) · Weigh-In 124.7 lbs (56.6 kgs)
                        pass

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
    ):
        return "ko/tko"
    return "submisson"
