import json
import scrapy
from scrapy.http import Response
from scrapy.exceptions import CloseSpider
from scrapy.settings import BaseSettings
from ..items import Team
from utilities import set_custom_feed
from urllib.parse import urlparse, parse_qs


class TeamsSpider(scrapy.Spider):
    name = "teams"
    allowed_domains = ["api.wrc.com"]
    start_urls = [
        "https://api.wrc.com/content/teams?class=WRC",
        "https://api.wrc.com/content/teams?class=WRC2",
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=247&type=manufacturer&championship=wrc",
        "https://api.wrc.com/content/result/championshipresult?seasonId=28&championshipId=253&type=team&championship=wrc",
    ]

    def db_upsert_properties(self, item_adapter):
        db_unique_id = {
            # "team_id": item_adapter.get("team_id"),
            "name": item_adapter.get("name"),
        }
        item_dict_for_update = {
            key: value
            for key, value in item_adapter.asdict().items()
            if key not in ["name"]
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
                    yield Team.convert_json_to_team_points(value, param)
                else:
                    yield Team.convert_json_to_team(value, param)
            except Exception as e:
                print(f"TEAM PARSE ERROR: {e}")
                continue

        # try:
        #     teams = json.loads(response.text)["content"]
        # except Exception as e:
        #     print(f"JSON PARSE ERROR: {e}")
        #     raise CloseSpider("BAD RESPONSE")

        # for team in teams:
        #     try:
        #         yield Team.convert_json_to_team(team, team_class)
        #     except Exception as e:
        #         print(f"TEAM PARSE ERROR: {e}")
        #         continue
