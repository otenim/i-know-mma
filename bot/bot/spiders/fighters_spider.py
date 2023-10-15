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

        # Get fighter id
        if response.url is None:
            return
        fighter_id = response.url.split("/")[-1].split("-")[0]
        if not fighter_id.isnumeric():
            return
        ret["id"] = int(fighter_id)

        # Fill details
        ret["details"] = {}
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
                    ret["details"]["name"] = name
                elif len(split) == 2:
                    # Has double name notations
                    # e.g: "정찬성, Jung Chan Sung"
                    ret["details"]["name"] = split[-1].strip()

        # Nickname
        nickname = details.xpath(
            "./ul/li/strong[text()='Nickname:']/parent::li/span/text()"
        ).get()
        if nickname is not None:
            nickname = nickname.strip()
            if nickname != "N/A":
                ret["details"]["nickname"] = nickname

        # Pro MMA record
        pro_mma_record = details.xpath(
            "./ul/li/strong[text()='Pro MMA Record:']/parent::li/span/text()"
        ).get()
        if pro_mma_record is not None:
            pro_mma_record = pro_mma_record.strip()
            if pro_mma_record != "N/A":
                record = ""
                nc = 0
                split = pro_mma_record.split(",")
                valid = True
                if len(split) == 1:
                    # Does not have NC count
                    # e.g: "31-5-0 (Win-Loss-Draw)"
                    record = pro_mma_record.split(" ")[0]
                elif len(split) == 2:
                    # Has NC count
                    # e.g: "31-5-0, 1 NC (Win-Loss-Draw)"
                    record = split[0]
                    nc = int(split[1].strip().split(" ")[0])
                else:
                    valid = False
                if valid:
                    split = record.strip().split("-")
                    if len(split) == 3:
                        w, l, d = split
                        ret["details"]["pro_mma_record"] = {
                            "W": int(w),
                            "L": int(l),
                            "D": int(d),
                            "NC": nc,
                        }

        # Current streak
        # e.g 1 Loss, 2 Losses, 1 Win, 2 Wins (No draw streaks)
        streak = details.xpath(
            "./ul/li/strong[text()='Current Streak:']/parent::li/span/text()"
        ).get()
        if streak is not None:
            streak = streak.strip()
            split = streak.split(" ")
            if len(split) == 2:
                count = int(split[0].strip())
                result = split[1].strip()
                valid = True
                if result.startswith("W"):
                    result = "W"
                elif result.startswith("L"):
                    result = "L"
                else:
                    valid = False
                if valid:
                    ret["details"]["streak"] = (count, result)

        # Return fighter record
        return ret
