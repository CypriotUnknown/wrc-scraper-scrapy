# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import scrapy.exceptions
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ArticleMedia:
    url: Optional[str] = None


@dataclass
class ArticleAuthor:
    name: Optional[str] = None
    icon_url: Optional[str] = None
    url: Optional[str] = None


@dataclass
class ArticleFooter:
    text: Optional[str] = None
    icon_url: Optional[str] = None


@dataclass
class ArticleField:
    name: str
    value: str
    inline: Optional[bool] = None


@dataclass
class Article:
    title: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[str] = None
    image: Optional[ArticleMedia] = None
    author: Optional[ArticleAuthor] = None
    description: Optional[str] = None
    video: Optional[ArticleMedia] = None
    thumbnail: Optional[ArticleMedia] = None
    footer: Optional[ArticleFooter] = None
    fields: Optional[list[ArticleField]] = None

    def to_dict(self):
        return asdict(self)


class Country(scrapy.Item):
    name = scrapy.Field()
    flag = scrapy.Field()


class RallyEventResult(scrapy.Item):
    rally_id = scrapy.Field()
    season_id = scrapy.Field()
    winner = scrapy.Field()

    def convert_json_to_event_result(values, season_id):
        try:
            rally_id = int(values[5])
            season_id = int(season_id)
        except:
            return None

        driver_id = values[9] if values[9] not in [None, ""] else None
        co_driver_id = values[12] if values[12] not in [None, ""] else None
        team_name = values[17] if values[17] not in [None, ""] else None
        manufacturer = values[18] if values[18] not in [None, ""] else None

        rally_not_complete = (
            driver_id is None
            or co_driver_id is None
            or team_name is None
            or manufacturer is None
        )

        return RallyEventResult(
            rally_id=rally_id,
            season_id=season_id,
            winner=(
                {
                    "driver_id": driver_id if driver_id not in [None, ""] else None,
                    "co_driver_id": (
                        co_driver_id if co_driver_id not in [None, ""] else None
                    ),
                    "team_name": (
                        team_name.lower() if team_name not in [None, ""] else None
                    ),
                    "manufacturer": (
                        manufacturer.lower() if manufacturer not in [None, ""] else None
                    ),
                }
                if rally_not_complete == False
                else None
            ),
        )


class RallyEvent(scrapy.Item):
    uid = scrapy.Field()
    event_id = scrapy.Field()
    rally_id = scrapy.Field()
    season_id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    country = scrapy.Field(serializer=Country)
    start_date = scrapy.Field()
    end_date = scrapy.Field()
    description = scrapy.Field()
    image = scrapy.Field()
    round_number = scrapy.Field()
    event_class = scrapy.Field()
    stages = scrapy.Field()

    def convert_json_to_stage_results(
        results_json, event_id: str | None, rally_id: int | None
    ):
        stages = []

        for stage_json in results_json:
            try:
                stage_slug = stage_json[1].lower()
                stage_name = stage_json[7].lower()
                event_id = int(event_id)
                if rally_id is None:
                    raise ValueError("rally_id is null")
            except Exception as e:
                print(f"CONVERT ERROR: {e}")
                return None

            stage_type = stage_json[2].lower()
            stage_status = stage_json[5].lower()
            day = stage_json[6].lower() if len(stage_json[6]) > 0 else None
            distance = float(stage_json[8]) if len(stage_json[8]) > 0 else None

            stages.append(
                {
                    "slug": stage_slug,
                    "name": stage_name,
                    "type": stage_type,
                    "status": stage_status,
                    "day": day,
                    "distance": distance,
                    "shakedown": stage_slug == "shd",
                    "power_stage": stage_type == "powerstage",
                }
            )

        return RallyEvent(
            event_id=event_id,
            rally_id=rally_id,
            stages=stages,
        )

    def convert_json_to_event(event_json, event_class):
        try:
            uid = event_json.get("uid").lower()
            url = f"https://www.wrc.com/c/event/{uid}"
            event_id = int(event_json.get("eventId"))
            rally_id = int(event_json.get("rallyId"))
        except:
            return None

        start_date_timestamp = event_json.get("startDate")

        start_date = (
            datetime.fromtimestamp(start_date_timestamp / 1000, timezone.utc)
            if start_date_timestamp is not None
            else None
        )

        end_date_timestamp = event_json.get("endDate")

        end_date = (
            datetime.fromtimestamp(end_date_timestamp / 1000, timezone.utc)
            if end_date_timestamp is not None
            else None
        )

        description = event_json.get("description")
        images = event_json.get("images")
        image = images[0].get("url") if images is not None else None
        title = event_json.get("title")
        round_number = event_json.get("round")

        country = event_json.get("country")
        country_name = country.get("name")
        flag_url = country.get("flag")[0].get("url")

        season_id = event_json.get("season").get("seasonId")

        return RallyEvent(
            uid=uid,
            event_id=event_id,
            url=url,
            start_date=start_date,
            end_date=end_date,
            description=description.lower() if description is not None else None,
            image=image,
            title=title.lower() if title is not None else None,
            round_number=round_number,
            event_class=event_class,
            country=Country(
                name=country_name.lower() if country_name is not None else None,
                flag=flag_url,
            ),
            season_id=season_id,
            rally_id=rally_id,
        )


class Driver(scrapy.Item):
    driver_id = scrapy.Field()
    first_name = scrapy.Field()
    last_name = scrapy.Field()
    car = scrapy.Field()
    country = scrapy.Field(serializer=Country)
    is_copilot = scrapy.Field()
    team = scrapy.Field()
    image = scrapy.Field()
    championship = scrapy.Field()
    points = scrapy.Field()

    @staticmethod
    def convert_json_to_driver_points(values, season_id):
        print(f"POINTS: {values[2]}")
        try:
            driver_id = values[5]
            points = float(values[2])
            season_id = int(season_id)
        except Exception as e:
            print(f"POINTS ERROR: {e}")
            return None

        return Driver(
            driver_id=driver_id, points={"season_id": season_id, "points": points}
        )

    @staticmethod
    def convert_json_to_driver(driver_json, driver_class):
        try:
            name_components = driver_json["name"].lower().split()
            driver_id = driver_json["key"].lower()
        except:
            return None

        car_name = driver_json.get("car")
        country = driver_json.get("country")
        country_name = country.get("name")
        flag_url = country.get("flag")[0].get("url")
        driver_type = driver_json.get("type")
        is_copilot = (
            driver_type.lower() != "driver" if driver_type is not None else None
        )
        team_name = driver_json.get("team")
        championship = driver_class.lower() if driver_class is not None else None

        championship = (
            "junior" if championship not in ["wrc", "wrc2", "wrc3"] else championship
        )

        return Driver(
            first_name=name_components[0],
            last_name=name_components[-1],
            driver_id=driver_id,
            car=car_name.lower() if car_name is not None else None,
            country=Country(
                name=country_name.lower() if country_name is not None else None,
                flag=flag_url,
            ),
            is_copilot=is_copilot,
            team=team_name.lower() if team_name is not None else None,
            image=driver_json["images"][0]["url"],
            championship=championship,
        )


class Team(scrapy.Item):
    team_id = scrapy.Field()
    name = scrapy.Field()
    established = scrapy.Field()
    principle = scrapy.Field()
    country = scrapy.Field(serializer=Country)
    image = scrapy.Field()
    championship = scrapy.Field()
    points = scrapy.Field()

    @staticmethod
    def convert_json_to_team_points(values, season_id):
        try:
            name = values[7].lower().replace("wrt", "world rally team")
            points = int(values[2])
        except:
            return None

        return Team(name=name, points={"season_id": season_id, "points": points})

    @staticmethod
    def convert_json_to_team(team_json, team_class):
        try:
            team_id = team_json.get("articleId").lower()
        except:
            return None

        team_name = team_json.get("name")
        country = team_json.get("country")
        country_name = country.get("name")
        flag_url = country.get("flag")[0].get("url")
        championship = team_class.lower() if team_class is not None else None
        championship = (
            "junior" if championship not in ["wrc", "wrc2", "wrc3"] else championship
        )

        established_str = team_json.get("established")
        principle = team_json.get("principle")

        return Team(
            name=team_name.lower() if team_name is not None else None,
            team_id=team_id,
            country=Country(
                name=country_name.lower() if country_name is not None else None,
                flag=flag_url,
            ),
            image=team_json["images"][0]["url"],
            championship=championship,
            established=int(established_str) if established_str.isdigit() else None,
            principle=principle.lower() if principle is not None else None,
        )


class News(scrapy.Item):
    news_id = scrapy.Field()
    date = scrapy.Field()
    description = scrapy.Field()
    image = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    category = scrapy.Field()

    @staticmethod
    def convert_json_to_news(news_json, category: str | None):
        try:
            news_id = news_json.get("uid").lower()
            url = f"https://www.wrc.com/a/news/{news_id}"
        except:
            return None

        date_string = news_json.get("createdAt")
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        date = (
            datetime.strptime(date_string, date_format)
            if date_string is not None
            else None
        )
        description = news_json.get("description")
        images = news_json.get("images")
        image = images[0].get("url") if images is not None else None
        title = news_json.get("title")

        return News(
            news_id=news_id,
            url=url,
            date=date,
            description=description.lower() if description is not None else None,
            image=image,
            title=title.lower() if title is not None else None,
            category=category.lower() if category is not None else None,
        )

    def convert_to_discord_article(self):
        if self["category"] is None or self["category"] != "all":
            return None

        self["category"] = self["category"].upper()

        return Article(
            title=self["title"],
            url=self["url"],
            timestamp=self["date"].isoformat() if self["date"] is not None else None,
            image=ArticleMedia(self["image"]) if self["image"] is not None else None,
            description=self["description"],
            footer=(
                ArticleFooter(text=f"Category: {self["category"]}")
            ),
        )
