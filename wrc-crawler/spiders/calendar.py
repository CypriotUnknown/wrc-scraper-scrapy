import json
from scrapy import Spider
from scrapy.http import HtmlResponse, Request
from scrapy.settings import BaseSettings
from scrapy.exceptions import CloseSpider
from ..items import RallyEvent
from utilities import set_custom_feed
from urllib.parse import urlparse, parse_qs
from datetime import datetime


class CalendarSpider(Spider):
    name = "calendar"
    allowed_domains = ["wrc.com", "api.wrc.com"]
    _current_year = datetime.now().year

    start_urls = [
        f"https://api.wrc.com/content/filters/calendar?championship=wrc&origin=vcms&year={_current_year}",
        f"https://api.wrc.com/content/filters/calendar?championship=wrc_junior&origin=vcms&year={_current_year}",
    ]

    def db_upsert_properties(self, item_adapter):
        db_unique_id = {
            "rally_id": item_adapter.get("rally_id"),
            "event_id": item_adapter.get("event_id"),
        }
        item_dict_for_update = {
            key: value
            for key, value in item_adapter.asdict().items()
            if key not in ["rally_id", "event_id"]
        }

        return db_unique_id, item_dict_for_update

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        # settings.update({"DOWNLOADER_MIDDLEWARES": playwright_middleware_dict})
        set_custom_feed(cls.name, settings)

    def parse_stages(self, response: HtmlResponse):
        query_params = parse_qs(urlparse(response.url).query)
        event_id = query_params.get("eventId", ["all"])[0]
        rally_id = response.meta.get("rally_id")

        try:
            the_json = json.loads(response.text)
            if type(the_json) is dict:
                results_json = the_json.get("stages").get("values")
                yield RallyEvent.convert_json_to_stage_results(
                    results_json, event_id, rally_id
                )
        except Exception as e:
            print(f"STAGES: {json.loads(response.text)} - {response.url}")
            print(f"STAGES JSON PARSE ERROR: {e}")
            raise CloseSpider("BAD RESPONSE")

    def parse(self, response: HtmlResponse):
        query_params = parse_qs(urlparse(response.url).query)
        category = query_params.get("championship", ["all"])[0]

        try:
            events = json.loads(response.text).get("content")
        except Exception as e:
            print(f"JSON PARSE ERROR: {e}")
            raise CloseSpider("BAD RESPONSE")

        for event in events:
            try:
                yield RallyEvent.convert_json_to_event(event, category)

                event_id = int(event.get("eventId"))
                rally_id = int(event.get("rallyId"))

                yield Request(
                    f"https://api.wrc.com/content/result/liveUpdates?eventId={event_id}",
                    callback=self.parse_stages,
                    meta={"rally_id": rally_id},
                )
            except Exception as e:
                print(f"RALLY EVENT PARSE ERROR: {e}")
                continue
