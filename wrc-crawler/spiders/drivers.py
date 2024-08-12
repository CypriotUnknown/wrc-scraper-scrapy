from scrapy import Spider
from scrapy.http import Response
from scrapy.exceptions import CloseSpider
from utilities import set_custom_feed
import json
from urllib.parse import urlparse, parse_qs
from scrapy.settings import BaseSettings
from ..items import Driver


class DriversSpider(Spider):
    name = "drivers"
    allowed_domains = ["www.wrc.com"]
    start_urls = [
        "https://api.wrc.com/content/driver?class=WRC",
        "https://api.wrc.com/content/driver?class=WRC2",
        "https://api.wrc.com/content/driver?class=WRC3",
        "https://api.wrc.com/content/driver?class=WRC%20JUNIOR",
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=245&type=driver&championship=wrc",  # WRC
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=246&type=codriver&championship=wrc",  # WRC CO-DRIVER
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=258&type=driver&championship=wrc",  # JUNIOR
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=259&type=codriver&championship=wrc",  # JUNIOR CO-DRIVER
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=256&type=driver&championship=wrc",  # WRC3
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=257&type=codriver&championship=wrc",  # WRC3 CO-DRIVER
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=249&type=driver&championship=wrc",  # WRC2
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=250&type=codriver&championship=wrc",  # WRC2 CO-DRIVER
    ]

    def db_upsert_properties(self, item_adapter):
        db_unique_id = {"driver_id": item_adapter.get("driver_id")}
        item_dict_for_update = {
            key: value
            for key, value in item_adapter.asdict().items()
            if key != "driver_id"
        }

        return db_unique_id, item_dict_for_update

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        set_custom_feed(cls.name, settings)

    def parse(self, response: Response):
        is_points_json = response.url.__contains__("/championshipresult?")
        query_params = parse_qs(urlparse(response.url).query)
        param = query_params.get("seasonId" if is_points_json else "class", [None])[0]
        try:
            the_json = json.loads(response.text)
            json_values = None
            if is_points_json:
                json_values = the_json["values"]
            else:
                json_values = the_json["content"]
        except Exception as e:
            print(f"JSON PARSE ERROR: {e}")
            raise CloseSpider("BAD RESPONSE")

        for value in json_values:
            try:
                if is_points_json:
                    yield Driver.convert_json_to_driver_points(value, param)
                else:
                    yield Driver.convert_json_to_driver(value, param)
            except Exception as e:
                print(f"DRIVER PARSE ERROR: {e}")
                continue
