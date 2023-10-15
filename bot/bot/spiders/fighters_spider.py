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

        # Age & Date of birth
        age_and_birth = details.xpath(
            "./ul/li/strong[text()='Age:']/parent::li[count(span)=2]/span/text()"
        ).getall()
        if len(age_and_birth) == 2:
            age = int(age_and_birth[0].strip())
            birth = age_and_birth[1].strip()
            split = birth.split(".")
            if len(split) == 3:
                y = int(split[0].strip())
                m = int(split[1].strip())
                d = int(split[2].strip())
                ret["age"] = age
                ret["birth"] = (y, m, d)

        # Return fighter record
        return ret
