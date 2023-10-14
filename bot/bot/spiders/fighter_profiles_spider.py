from typing import Any, Iterable
import scrapy
from scrapy.http import Request, Response


class FighterProfilesSpider(scrapy.Spider):
    name = "fighter_profiles"
    start_urls = ["https://www.tapology.com/search"]

    def parse(self, response: Response):
        urls = response.xpath(
            "//div[@class='siteSearchFightersByWeightClass']//@href"
        ).getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_fighter_list)

    def parse_fighter_list(self, response: Response):
        fighter_urls = response.xpath("//table[@class='siteSearchResults']//@href")
        for url in fighter_urls:
            yield response.follow(url, callback=self.parse_fighter_profile)

    def parse_fighter_profile(self, response: Response):
        return {
            "name": response.xpath(
                "//div[@class='fighterUpcomingHeader']/h1[not(@*)]/text()"
            ).get()
        }
