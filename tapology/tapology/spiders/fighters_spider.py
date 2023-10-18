import scrapy
from scrapy.http import Request, TextResponse
from collections.abc import Generator


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

        # Fighter url
        if response.url is None:
            return
        ret["url"] = response.url

        # Fighter name
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

        # Parse details section
        details_sel = response.xpath("//div[@class='details details_two_columns']")

        # Pro MMA record
        pro_mma_rec = details_sel.xpath(
            "./ul/li/strong[text()='Pro MMA Record:']/following-sibling::span[1]/text()"
        ).re(r"(\d+)-(\d+)-(\d+)(?:,\s(\d+)\sNC)?")
        if len(pro_mma_rec) == 4:
            ret["pro_mma_rec"] = {
                "w": int(pro_mma_rec[0]),
                "l": int(pro_mma_rec[1]),
                "d": int(pro_mma_rec[2]),
                "nc": 0 if pro_mma_rec[3] == "" else int(pro_mma_rec[3]),
            }

        # Date of birth
        fighter_date_of_birth = details_sel.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()"
        ).re(r"(\d{4})\.(\d{2}).(\d{2})")
        if len(fighter_date_of_birth) == 3:
            ret["date_of_birth"] = {
                "y": int(fighter_date_of_birth[0]),
                "m": int(fighter_date_of_birth[1]),
                "d": int(fighter_date_of_birth[2]),
            }

        # Weight class
        fighter_weight_class = details_sel.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()"
        ).get()
        assert fighter_weight_class is not None
        fighter_weight_class = fighter_weight_class.strip()
        assert fighter_weight_class != "N/A"
        ret["weight_class"] = fighter_weight_class

        # Affiliation
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

        # Height
        # Format: "5\'9\" (175cm)"
        fighter_height = details_sel.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\'([\d\.]+)\"")
        if len(fighter_height) == 2:
            ret["height"] = (
                float(fighter_height[0]) * 0.3048 + float(fighter_height[1]) * 0.0254
            )

        # Reach
        # Format: "74.0\" (188cm)"
        fighter_reach = details_sel.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\"")
        if len(fighter_reach) == 1:
            ret["reach"] = float(fighter_reach[0]) * 0.0254

        # Career disclosed earnings
        # Format: "$193,000 USD", "$0 USD"
        career_earnings = details_sel.xpath(
            "./ul/li/strong[text()='Career Disclosed Earnings:']/following-sibling::span[1]/text()"
        ).re(r"\$([\d,]+)\sUSD")
        if len(career_earnings) == 1:
            ret["career_earnings"] = int(career_earnings[0].replace(",", ""))

        # Born
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

        # Foundations
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

        # Pro MMA stats
        pro_mma_stat_sels = response.xpath(
            "//ul[@class='fighterRecordStats']/li/div[@class='label']"
        )
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
        pro_record_sels = details_sel.xpath(
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

                # Genre of the bout
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

                # Bout result
                # NOTE: Skip upcoming bouts
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
                elif bout_result == "unknown":
                    item["result"] = "unknown"
                else:  # "upcoming"
                    continue

                # Opponent fighter
                opponent_sel = pro_record_sel.xpath(
                    "./div[@class='result']/div[@class='opponent']"
                )
                assert len(opponent_sel) == 1

                # Opponent name
                opponent_link_sel = opponent_sel.xpath("./div[@class='name']/a")
                has_opponent_link = False if len(opponent_link_sel) == 0 else True
                if has_opponent_link:
                    opponent_link = opponent_link_sel.xpath("./@href").get()
                    opponent_name = opponent_link_sel.xpath("./text()").get()
                    assert opponent_link is not None and opponent_name is not None
                    item["opponent"] = {
                        "name": opponent_name.strip(),
                        "url": opponent_link.strip(),
                    }
                else:
                    # NOTE: Opponent name is included in <span></span> tags if
                    # it does not have a link
                    opponent_name = opponent_sel.xpath(
                        "./div[@class='name']/span/text()"
                    ).get()
                    assert opponent_name is not None
                    item["opponent"] = {"name": opponent_name.strip()}

                # Record before the fight
                # NOTE: only available when the bout is official mma bout
                # and was not cancelled
                non_mma_sel = opponent_sel.xpath("./div[@class='record nonMma']")
                is_official_mma_bout = True if len(non_mma_sel) == 0 else False
                if is_official_mma_bout and bout_result != "cancelled":
                    record_sel = opponent_sel.xpath("./div[@class='record']")
                    fighter_record = record_sel.xpath(
                        "./span[@title='Fighter Record Before Fight']/text()"
                    ).re(r"(\d+)-(\d+)-(\d+)")
                    assert len(fighter_record) == 3
                    item["record_before_fight"] = {
                        "w": int(fighter_record[0].strip()),
                        "l": int(fighter_record[1].strip()),
                        "d": int(fighter_record[2].strip()),
                    }
                    # NOTE: Opponent record is provided
                    # when a link to the opponent page is provided
                    if has_opponent_link:
                        opponent_record = record_sel.xpath(
                            "./span[@title='Opponent Record Before Fight']/text()"
                        ).re(r"(\d+)-(\d+)-(\d+)")
                        item["opponent"]["record_before_fight"] = {
                            "w": int(opponent_record[0].strip()),
                            "l": int(opponent_record[1].strip()),
                            "d": int(opponent_record[2].strip()),
                        }
                        assert len(opponent_record) == 3
                ret["pro_records"].append(item)

        return ret
