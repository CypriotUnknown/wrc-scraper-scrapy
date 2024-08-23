import json
import os
from itemadapter import ItemAdapter
from typing import Optional
from pymongo import collection, UpdateOne
import redis
from scrapy.exceptions import CloseSpider, DropItem
from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy.item import Item
from scrapy import Spider
from utilities.db import MONGO_CLIENT
from datetime import datetime, UTC
from .items import News


class MongoDBPipeline:
    def __init__(self, mongo_db: str):
        self.mongo_db = mongo_db
        self.collection: Optional[collection.Collection] = None
        self.items_to_persist: list[UpdateOne] = []

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "MongoDBPipeline":
        """
        Factory method to initialize the pipeline with settings from the crawler.
        :param crawler: The Scrapy Crawler object.
        :return: An instance of MongoDBPipeline.
        """
        settings: Settings = crawler.settings
        return cls(mongo_db=settings.get("MONGO_DB"))

    def open_spider(self, spider: Spider) -> None:
        """
        Initialize the MongoDB connection when the spider opens.
        :param spider: The spider instance.
        """

        self.collection = MONGO_CLIENT.get_database(self.mongo_db).get_collection(
            spider.name
        )
        if self.collection is not None:
            return

        raise CloseSpider("MONGO COLLECTION IS NULL !")

    def close_spider(self, spider: Spider) -> None:
        #     """
        #     Close the MongoDB connection when the spider closes.
        #     :param spider: The spider instance.
        #     """
        #     if self.client:
        #         self.client.close()
        if self.collection is None:
            raise CloseSpider("MONGO COLLECTION IS NULL !")
            # raise DropItem("Database connection is not initialized.")

        write_result = self.collection.bulk_write(self.items_to_persist)
        self.items_to_persist.clear()
        print(f"WRITE_RESULT: {write_result}")

    def process_item(self, item: Item, spider: Spider) -> Item:
        """
        Process each item and store it in the MongoDB collection.
        :param item: The item scraped by the spider.
        :param spider: The spider instance.
        :return: The processed item.
        :raises DropItem: If the item is invalid or cannot be stored.
        """

        item_adapter = ItemAdapter(item)

        updated_at = {"updated_at": datetime.now(UTC)}

        (db_unique_id, item_dict_for_update) = spider.db_upsert_properties(item_adapter)

        update = {
            "$set": {**item_dict_for_update, **updated_at},
            "$setOnInsert": {
                "created_at": datetime.now(UTC),
            },
        }

        upser_operation = UpdateOne(db_unique_id, update, upsert=True)

        self.items_to_persist.append(upser_operation)

        # self.collection.update_one(db_unique_id, update, upsert=True)
        spider.logger.debug(f"Item inserted into MongoDB: {item}")
        return item


class RedisPublishPipeline:
    def open_spider(self, spider):
        # Initialize Redis connection
        self.redis_client = None

        config_file_path = os.getenv("CONFIG_PATH", "redis-conf.json")
        if os.path.exists(config_file_path):
            with open(config_file_path, "r") as file:
                file_json = json.load(file)
                redis_host = file_json.get("host")
                redis_port = file_json.get("port")
                channel_pattern = file_json.get("channel_pattern")

                if (
                    redis_host is not None
                    and redis_port is not None
                    and channel_pattern is not None
                ):
                    self.channel_pattern = (
                        channel_pattern
                        if channel_pattern[-1] != "."
                        else channel_pattern.removesuffix(".")
                    )

                    self.redis_client = redis.Redis(
                        redis_host,
                        port=redis_port,
                        decode_responses=True,
                        username=file_json.get("username"),
                        password=file_json.get("password"),
                    )
                    self.items: list[Item] = []  # List to hold all scraped items
                    self.notification_flag: str | None = None

    def close_spider(self, spider):
        if self.redis_client is not None:
            dict_to_send = {
                "articles": self.items,
                "notificationFlag": self.notification_flag,
            }

            items_json = json.dumps(dict_to_send, indent=4)
            category_channel = "motorsports"

            channel_name = ".".join(
                [
                    self.channel_pattern,
                    f"wrc-{spider.name}",
                    category_channel,
                    "articles",
                ]
            )

            self.redis_client.publish(channel_name, items_json)
            print(f"published to Redis @ '{channel_name}'")

    def process_item(self, item: News | None, spider):
        if item is None:
            print("ITEM IS NULL")
            raise DropItem(item)

        article = item.convert_to_discord_article()

        if article is None:
            print("ARTICLE IS NULL")
            raise DropItem(item)

        if article.title is None:
            print("ITEM TITLE IS NULL")
            raise DropItem(item)

        self.notification_flag = (
            "lastArticleDate" if article.timestamp is not None else "lastArticleTitle"
        )

        # Add each item to the list
        if self.redis_client is not None:
            self.items.append(article.to_dict())
        return item
