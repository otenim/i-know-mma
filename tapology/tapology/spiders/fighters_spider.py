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
        name = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h1[not(@*)]/text()"
        ).get()
        assert name is not None
        ret["name"] = name.strip()

        # Fighter nickname
        nickname = response.xpath(
            "//div[@class='fighterUpcomingHeader']/h4[@class='preTitle nickname']/text()"
        ).re_first(r"\"(.*)\"")
        if nickname is not None:
            ret["nickname"] = nickname.strip()

        # Parse details section
        details = response.xpath("//div[@class='details details_two_columns']")

        # Pro MMA record
        pro_mma_record = details.xpath(
            "./ul/li/strong[text()='Pro MMA Record:']/following-sibling::span[1]/text()"
        ).re(r"(\d+)-(\d+)-(\d+)(?:,\s(\d+)\sNC)?")
        if len(pro_mma_record) == 4:
            ret["pro_mma_record"] = {
                "w": int(pro_mma_record[0]),
                "l": int(pro_mma_record[1]),
                "d": int(pro_mma_record[2]),
                "nc": 0 if pro_mma_record[3] == "" else int(pro_mma_record[3]),
            }

        # Date of birth
        birth = details.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/following-sibling::span[1]/text()"
        ).re(r"(\d{4})\.(\d{2}).(\d{2})")
        if len(birth) == 3:
            ret["birth"] = {"y": int(birth[0]), "m": int(birth[1]), "d": int(birth[2])}

        # Weight class
        weight_class = details.xpath(
            "./ul/li/strong[text()='Weight Class:']/following-sibling::span[1]/text()"
        ).get()
        assert weight_class is not None
        weight_class = weight_class.strip()
        assert weight_class != "N/A"
        ret["weight_class"] = weight_class

        # Affiliation
        affili = details.xpath(
            "./ul/li/strong[text()='Affiliation:']/following-sibling::span[1]/a"
        )
        if len(affili) == 1:
            url = affili.xpath("./@href").get()
            if url is not None:
                name = affili.xpath("./text()").get()
                if name is not None:
                    ret["affiliation"] = {
                        "url": url.strip(),
                        "name": name.strip(),
                    }

        # Height
        # e.g: "5\'9\" (175cm)"
        height = details.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\'([\d\.]+)\"")
        if len(height) == 2:
            feet, inch = height
            ret["height"] = float(feet) * 0.3048 + float(inch) * 0.0254

        # Reach
        # e.g: "74.0\" (188cm)"
        reach = details.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()"
        ).re(r"([\d\.]+)\"")
        if len(reach) == 1:
            inch = reach[0]
            ret["reach"] = float(inch) * 0.0254

        # Career disclosed earnings
        # e.g: "$193,000 USD", "$0 USD"
        earns = details.xpath(
            "./ul/li/strong[text()='Career Disclosed Earnings:']/following-sibling::span[1]/text()"
        ).re(r"\$([\d,]+)\sUSD")
        if len(earns) == 1:
            ret["earnings"] = int(earns[0].replace(",", ""))

        # Born
        born = details.xpath(
            "./ul/li/strong[text()='Born:']/following-sibling::span[1]/text()"
        ).get()
        if born is not None:
            born = born.strip()
            if born != "N/A":
                v = []
                for b in born.split(","):
                    v.append(b.strip())
                ret["born"] = v

        # Fighting out of
        out_of = details.xpath(
            "./ul/li/strong[text()='Fighting out of:']/following-sibling::span[1]/text()"
        ).get()
        if out_of is not None:
            out_of = out_of.strip()
            if out_of != "N/A":
                v = []
                for o in out_of.split(","):
                    v.append(o.strip())
                ret["out_of"] = v

        # College
        college = details.xpath(
            "./ul/li/strong[text()='College:']/following-sibling::span[1]/text()"
        ).get()
        if college is not None:
            college = college.strip()
            if college != "N/A":
                ret["college"] = college

        # Foundations
        foundations = details.xpath(
            "./ul/li/strong[text()='Foundation Style:']/following-sibling::span[1]/text()"
        ).get()
        if foundations is not None:
            foundations = foundations.strip()
            if foundations != "N/A":
                v = []
                for b in foundations.split(","):
                    v.append(b.strip())
                ret["foundations"] = v

        # Head Coach
        head_coach = details.xpath(
            "./ul/li/strong[text()='Head Coach:']/following-sibling::span[1]/text()"
        ).get()
        if head_coach is not None:
            head_coach = head_coach.strip()
            if head_coach != "N/A":
                ret["head_coach"] = head_coach

        # Other Coaches
        other_coaches = details.xpath(
            "./ul/li/strong[text()='Other Coaches:']/following-sibling::span[1]/text()"
        ).get()
        if other_coaches is not None:
            other_coaches = other_coaches.strip()
            if other_coaches != "N/A":
                v = []
                for c in other_coaches.split(","):
                    v.append(c.strip())
                ret["other_coaches"] = v

        # Pro MMA stats
        stats = response.xpath(
            "//ul[@class='fighterRecordStats']/li/div[@class='label']"
        )
        if len(stats) > 0:
            ret["pro_mma_stats"] = {}
            for s in stats:
                # Label (KO/TKO, Submission, Decision, Disqualification)
                label = s.xpath("./div[starts-with(@class,'primary')]/text()").get()
                assert label is not None
                label = label.strip()

                # Count (win & loss)
                count = s.xpath("./div[@class='secondary']/text()").re(
                    r"(\d+)\s(?:wins|win),\s(\d+)\s(?:losses|loss)"
                )
                assert len(count) == 2
                ret["pro_mma_stats"][label.lower()] = {
                    "w": int(count[0].strip()),
                    "l": int(count[1].strip()),
                }

        # Pro MMA results
        pro_results = details.xpath(
            "//section[@class='fighterFightResults']/ul[@id='proResults']/li"
        )
        assert len(pro_results) > 0
        ret["pro_results"] = []
        for result in pro_results:
            record = {}

            # Skip ineligible mma bouts
            txt = result.xpath(
                "./div[@class='result']/div[@class='opponent']/div[@class='record nonMma']/text()"
            ).get()
            if txt is not None:
                txt = txt.strip()
                if txt == "Record Ineligible MMA":
                    continue

            # Bout type
            bout_type = result.xpath("./@data-sport").get()
            assert bout_type is not None and bout_type in [
                "mma",
                "boxing",
                "knuckle",
                "kickboxing",
                "muay",
                "lethwei",
                "grappling",
                "shootboxing",
                "custom",
            ]
            record["bout_type"] = bout_type.strip()

            # Bout result
            # e.g: loss, win, cancelled, draw, no contest, unknown, upcoming
            # NOTE: Skip upcoming bouts
            bout_result = result.xpath("./@data-status").get()
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
                record["bout_result"] = "w"
            elif bout_result == "loss":
                record["bout_result"] = "l"
            elif bout_result == "draw":
                record["bout_result"] = "d"
            elif bout_result == "no contest":
                record["bout_result"] = "nc"
            elif bout_result == "cancelled":
                record["bout_result"] = "cancelled"
            elif bout_result == "unknown":
                record["bout_result"] = "unknown"
            else:
                continue

            # Opponent
            opponent = result.xpath("./div[@class='result']/div[@class='opponent']")
            assert len(opponent) == 1

            # Opponent name
            name = opponent.xpath("./div[@class='name']/a")
            # Check if the section has a link to the opponent
            has_opponent_link = False if len(name) == 0 else True
            if has_opponent_link:
                opponent_link = name.xpath("./@href").get()
                opponent_name = name.xpath("./text()").get()
                assert opponent_link is not None and opponent_name is not None
                record["opponent"] = {
                    "name": opponent_name.strip(),
                    "url": opponent_link.strip(),
                }
            else:
                # NOTE: Opponent name is included in <span></span> tags if
                # it does not have a link
                opponent_name = opponent.xpath("./div[@class='name']/span/text()").get()
                assert opponent_name is not None
                record["opponent"] = {"name": opponent_name.strip()}

            # Record before the fight
            # NOTE: only available when the bout is official mma bout
            # and was not cancelled
            sels = opponent.xpath("./div[@class='record nonMma']")
            is_official_mma_bout = True if len(sels) == 0 else False
            if is_official_mma_bout and bout_result != "cancelled":
                rec = opponent.xpath("./div[@class='record']")
                fighter_rec = rec.xpath(
                    "./span[@title='Fighter Record Before Fight']/text()"
                ).re(r"(\d+)-(\d+)-(\d+)")
                assert len(fighter_rec) == 3
                record["record"] = {
                    "w": int(fighter_rec[0].strip()),
                    "l": int(fighter_rec[1].strip()),
                    "d": int(fighter_rec[2].strip()),
                }
                # NOTE: Opponent record is provided
                # when a link to the opponent page is provided
                if has_opponent_link:
                    opponent_rec = rec.xpath(
                        "./span[@title='Opponent Record Before Fight']/text()"
                    ).re(r"(\d+)-(\d+)-(\d+)")
                    record["opponent"]["record"] = {
                        "w": int(opponent_rec[0].strip()),
                        "l": int(opponent_rec[1].strip()),
                        "d": int(opponent_rec[2].strip()),
                    }
                    assert len(opponent_rec) == 3

            ret["pro_results"].append(record)

        return ret
