import json
from scrapy import Spider
from scrapy.http import HtmlResponse
from scrapy.settings import BaseSettings
from scrapy.exceptions import CloseSpider
from ..items import RallyEventResult
from utilities import set_custom_feed
from urllib.parse import urlparse, parse_qs
from datetime import datetime


class RallyResultsSpider(Spider):
    name = "rally-results"
    allowed_domains = ["api.wrc.com"]
    start_urls = [
        "https://api.wrc.com/content/result/calendar?season=28&championship=wrc"
    ]

    def db_upsert_properties(self, item_adapter):
        db_unique_id = {"rally_id": item_adapter.get("rally_id")}
        item_dict_for_update = {
            key: value
            for key, value in item_adapter.asdict().items()
            if key != "rally_id"
        }

        return db_unique_id, item_dict_for_update

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        set_custom_feed(cls.name, settings)

    def parse(self, response: HtmlResponse):
        query_params = parse_qs(urlparse(response.url).query)
        season_id = query_params.get("season", [None])[0]

        try:
            results = json.loads(response.text).get("values")
        except Exception as e:
            print(f"JSON PARSE ERROR: {e}")
            raise CloseSpider("BAD RESPONSE")

        for result_values in results:
            try:
                yield RallyEventResult.convert_json_to_event_result(
                    result_values, season_id
                )
            except Exception as e:
                print(f"NEWS PARSE ERROR: {e}")
                continue
