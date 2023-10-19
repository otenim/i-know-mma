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
            # Filter out fighters whose record is "0-0-0" or starts with "Am"
            record = row.xpath("./td[7]/text()").get()
            if record is not None:
                record = record.strip()
                if record == "0-0-0" or record.startswith("Am"):
                    continue
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

        # Fighter nickname (optional)
        fighter_nickname = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h4[@class='preTitle nickname']/text()"
        ).re_first(r"\"(.*)\"")
        ret["nickname"] = None
        if fighter_nickname is not None:
            ret["nickname"] = fighter_nickname.strip()

        # Parse details section
        details_sel = response.xpath("//div[@class='details details_two_columns']")
        assert len(details_sel) == 1

        # Pro MMA record (optional)
        pro_mma_record = details_sel.xpath(
            "./ul/li/strong[text()='Pro MMA Record:']/following-sibling::span[1]/text()"
        ).re(r"(\d+)-(\d+)-(\d+)(?:,\s(\d+)\sNC)?")
        ret["pro_mma_record"] = None
        if len(pro_mma_record) == 4:
            ret["pro_mma_record"] = (
                int(pro_mma_record[0]),
                int(pro_mma_record[1]),
                int(pro_mma_record[2]),
                0 if pro_mma_record[3] == "" else int(pro_mma_record[3]),
            )

        # Date of birth (optional)
        date_of_birth = details_sel.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()"
        ).re(r"(\d{4})\.(\d{2}).(\d{2})")
        ret["date_of_birth"] = None
        if len(date_of_birth) == 3:
            ret["date_of_birth"] = (
                int(date_of_birth[0]),
                int(date_of_birth[1]),
                int(date_of_birth[2]),
            )

        # Weight class (must)
        weight_class = details_sel.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()"
        ).get()
        assert weight_class is not None
        weight_class = weight_class.strip()
        assert weight_class != "N/A"
        ret["weight_class"] = weight_class

        # Affiliation (optional)
        affili_sel = details_sel.xpath(
            "./ul/li/strong[text()='Affiliation:']/following-sibling::span[1]/a"
        )
        ret["affiliation"] = None
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
        fighter_height = details_sel.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\'([\d\.]+)\"")
        ret["height"] = None
        if len(fighter_height) == 2:
            ret["height"] = (
                float(fighter_height[0]) * 0.3048 + float(fighter_height[1]) * 0.0254
            )

        # Reach (optional)
        # Format: "74.0\" (188cm)"
        fighter_reach = details_sel.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\"")
        ret["reach"] = None
        if len(fighter_reach) == 1:
            ret["reach"] = float(fighter_reach[0]) * 0.0254

        # Career disclosed earnings
        # Format: "$193,000 USD", "$0 USD"
        career_earnings = details_sel.xpath(
            "./ul/li/strong[text()='Career Disclosed Earnings:']/following-sibling::span[1]/text()"
        ).re(r"\$([\d,]+)\sUSD")
        ret["career_earnings"] = None
        if len(career_earnings) == 1:
            ret["career_earnings"] = int(career_earnings[0].replace(",", ""))

        # Place of birth
        place_of_birth = details_sel.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()"
        ).get()
        ret["place_of_birth"] = None
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
        ret["out_of"] = None
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
        ret["college"] = None
        if college is not None:
            college = college.strip()
            if college != "N/A":
                ret["college"] = college

        # Foundations
        foundation_styles = details_sel.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()"
        ).get()
        ret["foundation_styles"] = None
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
        ret["head_coach"] = None
        if head_coach is not None:
            head_coach = head_coach.strip()
            if head_coach != "N/A":
                ret["head_coach"] = head_coach

        # Other Coaches
        other_coaches = details_sel.xpath(
            "./ul/li/strong[text()='Other Coaches:']/following-sibling::span[1]/text()"
        ).get()
        ret["other_coaches"] = None
        if other_coaches is not None:
            other_coaches = other_coaches.strip()
            if other_coaches != "N/A":
                ret["other_coaches"] = []
                for c in other_coaches.split(","):
                    ret["other_coaches"].append(c.strip())

        # Pro MMA stats
        pro_mma_stat_sels = response.xpath(
            "//ul[@class='fighterRecordStats']/li/div[@class='label']"
        )
        ret["pro_mma_stats"] = None
        if len(pro_mma_stat_sels) > 0:
            ret["pro_mma_stats"] = {}
            for stat_sel in pro_mma_stat_sels:
                # Label (KO/TKO, Submission, Decision, Disqualification)
                label = stat_sel.xpath(
                    "./div[starts-with(@class,'primary')]/text()"
                ).get()
                assert label is not None
                label = label.strip()

                # Count (win or loss)
                count = stat_sel.xpath("./div[@class='secondary']/text()").re(
                    r"(\d+)\s(?:wins|win),\s(\d+)\s(?:losses|loss)"
                )
                assert len(count) == 2
                ret["pro_mma_stats"][label.lower()] = {
                    "w": int(count[0].strip()),
                    "l": int(count[1].strip()),
                }

        # Pro records
        pro_record_sels = response.xpath(
            "//section[@class='fighterFightResults']/ul[@id='proResults']/li"
        )
        ret["pro_records"] = None
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
                bout_genre = pro_record_sel.xpath("./@data-sport").get()
                assert bout_genre is not None and bout_genre in [
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
                item["genre"] = bout_genre.strip()

                # Bout result (must)
                # NOTE: Skip upcoming & result-unknown bouts
                bout_result = pro_record_sel.xpath("./@data-status").get()
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
                elif bout_result == "no contest":
                    item["result"] = "nc"
                elif bout_result == "cancelled":
                    item["result"] = "cancelled"
                else:  # "upcoming" or "unknown"
                    continue

                # Opponent fighter (must)
                opponent_sel = pro_record_sel.xpath(
                    "./div[@class='result']/div[@class='opponent']"
                )
                assert len(opponent_sel) == 1

                # Opponent name (at least name must be provided)
                item["opponent"] = {"name": None, "url": None}
                opponent_link_sel = opponent_sel.xpath("./div[@class='name']/a")
                has_opponent_link = False if len(opponent_link_sel) == 0 else True
                if has_opponent_link:
                    opponent_link = opponent_link_sel.xpath("./@href").get()
                    opponent_name = opponent_link_sel.xpath("./text()").get()
                    assert opponent_link is not None and opponent_name is not None
                    item["opponent"]["name"] = opponent_name.strip()
                    item["opponent"]["url"] = opponent_link.strip()
                else:
                    # NOTE: Opponent name is included in <span></span> tags if
                    # it does not have a link
                    opponent_name = opponent_sel.xpath(
                        "./div[@class='name']/span/text()"
                    ).get()
                    assert opponent_name is not None
                    item["opponent"]["name"] = opponent_name.strip()

                # Record before the fight
                # NOTE: only available when the bout is official mma bout
                # and was not cancelled
                item["record"] = None
                item["opponent"]["record"] = None
                non_mma_sel = opponent_sel.xpath("./div[@class='record nonMma']")
                is_official_mma_bout = True if len(non_mma_sel) == 0 else False
                if is_official_mma_bout and bout_result != "cancelled":
                    record_sel = opponent_sel.xpath("./div[@class='record']")
                    fighter_record = record_sel.xpath(
                        "./span[@title='Fighter Record Before Fight']/text()"
                    ).re(r"(\d+)-(\d+)-(\d+)")
                    assert len(fighter_record) == 3
                    item["record"] = (
                        int(fighter_record[0].strip()),
                        int(fighter_record[1].strip()),
                        int(fighter_record[2].strip()),
                    )

                    # NOTE: Opponent record is provided
                    # when a link to the opponent page is provided
                    if has_opponent_link:
                        opponent_record = record_sel.xpath(
                            "./span[@title='Opponent Record Before Fight']/text()"
                        ).re(r"(\d+)-(\d+)-(\d+)")
                        assert len(opponent_record) == 3
                        item["opponent"]["record"] = (
                            int(opponent_record[0].strip()),
                            int(opponent_record[1].strip()),
                            int(opponent_record[2].strip()),
                        )

                if bout_result in ["win", "loss"]:
                    # Fight summary
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
                    item["by"] = item["detail"] = item["time"] = item["round"] = None
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
