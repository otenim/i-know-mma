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

        # Parse details section
        details = response.xpath("//div[@class='details details_two_columns']")

        # Name
        name = details.xpath(
            "./ul/li/strong[text()='Given Name:']/parent::li/span/text() | ./ul/li/strong[text()='Name:']/parent::li/span/text()"
        ).get()
        if name is not None:
            name = name.strip()
            if name != "N/A":
                split = name.split(",")
                if len(split) == 1:
                    # Has single name notation
                    # e.g: "Conor Anthony McGregor"
                    ret["name"] = name
                elif len(split) == 2:
                    # Has double name notations
                    # e.g: "정찬성, Jung Chan Sung"
                    ret["name"] = split[-1].strip()

        # Nickname
        nickname = details.xpath(
            "./ul/li/strong[text()='Nickname:']/parent::li/span/text()"
        ).get()
        if nickname is not None:
            nickname = nickname.strip()
            if nickname != "N/A":
                ret["nickname"] = nickname

        # Date of birth
        birth = details.xpath(
            "./ul/li/strong[text()='| Date of Birth:']/parent::li/span[not(@*)]/text()"
        ).get()
        if birth is not None:
            birth = birth.strip()
            split = birth.split(".")
            if len(split) == 3:
                y = int(split[0].strip())
                m = int(split[1].strip())
                d = int(split[2].strip())
                ret["birth"] = (y, m, d)

        # Affiliation
        affili = details.xpath(
            "./ul/li/strong[text()='Affiliation:']/parent::li/span/a"
        )
        if len(affili) == 1:
            affili_url = affili.xpath("./@href").get()
            if affili_url is not None:
                affili_url = affili_url.strip()
                affili_id = int(affili_url.split("/")[-1].split("-")[0])
                affili_name = affili.xpath("./text()").get()
                if affili_name is not None:
                    affili_name = affili_name.strip()
                    ret["affiliation"] = {
                        "url": affili_url,
                        "name": affili_name,
                    }

        # Height
        # e.g: "5\'9\" (175cm)"
        height = details.xpath(
            "./ul/li/strong[text()='Height:']/following-sibling::span[1]/text()"
        ).re(r"([0-9\.]+)\'([0-9\.]+)\"")
        if len(height) == 2:
            feet, inch = height
            ret["height"] = float(feet) * 0.3048 + float(inch) * 0.0254

        # Reach
        # e.g: "74.0\" (188cm)"
        reach = details.xpath(
            "./ul/li/strong[text()='| Reach:']/following-sibling::span[1]/text()"
        ).re(r"([0-9\.]+)\"")
        if len(reach) == 1:
            ret["reach"] = float(reach[0]) * 0.0254

        # Career disclosed earnings
        earns = details.xpath(
            "./ul/li/strong[text()='Career Disclosed Earnings:']/parent::li/span/text()"
        ).re(r"\$([0-9,]+)\s*USD")
        if len(earns) == 1:
            ret["earnings"] = int(earns[0].replace(",", ""))

        # Born
        born = details.xpath(
            "./ul/li/strong[text()='Born:']/parent::li/span/text()"
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
            "./ul/li/strong[text()='Fighting out of:']/parent::li/span/text()"
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
            "./ul/li/strong[text()='College:']/parent::li/span/text()"
        ).get()
        if college is not None:
            college = college.strip()
            if college != "N/A":
                ret["college"] = college

        # Backbones
        backbones = details.xpath(
            "./ul/li/strong[text()='Foundation Style:']/parent::li/span/text()"
        ).get()
        if backbones is not None:
            backbones = backbones.strip()
            if backbones != "N/A":
                v = []
                for b in backbones.split(","):
                    v.append(b.strip())
                ret["backbones"] = v

        return ret
