import json
import scrapy
from scrapy.http import Response
from scrapy.exceptions import CloseSpider
from scrapy.settings import BaseSettings
from ..items import News
from utilities import set_custom_feed
from urllib.parse import urlparse, parse_qs


class NewsSpider(scrapy.Spider):
    name = "news"
    allowed_domains = ["api.wrc.com"]
    start_urls = [
        "https://api.wrc.com/content/filters/wrc-all-latest-news?page=1&language=en&size=100&origin=vcms",  # ALL
        "https://api.wrc.com/content/filters/newsAndArticles?language=en-US&size=100&class=wrc2&page=1&platform=web",  # WRC2
        "https://api.wrc.com/content/filters/newsAndArticles?language=en-US&size=100&class=wrc3&page=1&platform=web",  # WRC3
    ]

    def db_upsert_properties(self, item_adapter):
        db_unique_id = {"news_id": item_adapter.get("news_id")}
        item_dict_for_update = {
            key: value
            for key, value in item_adapter.asdict().items()
            if key != "news_id"
        }

        return db_unique_id, item_dict_for_update

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        set_custom_feed(cls.name, settings)

    def parse(self, response: Response):
        query_params = parse_qs(urlparse(response.url).query)
        category = query_params.get("class", ["all"])[0]

        try:
            news = json.loads(response.text)["content"]
        except Exception as e:
            print(f"JSON PARSE ERROR: {e}")
            raise CloseSpider("BAD RESPONSE")

        for news_item in news:
            try:
                yield News.convert_json_to_news(news_item, category)
            except Exception as e:
                print(f"NEWS PARSE ERROR: {e}")
                continue
