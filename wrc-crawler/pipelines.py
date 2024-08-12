# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from typing import Optional
from pymongo import collection, UpdateOne
from scrapy.exceptions import CloseSpider
from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy.item import Item
from scrapy import Spider
from utilities.db import MONGO_CLIENT
from datetime import datetime, UTC


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
