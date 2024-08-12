from scrapy.settings import BaseSettings


def set_custom_feed(spider_name: str, settings: BaseSettings):
    settings.set(
        "FEEDS",
        {
            f"output_data/{spider_name}.json": {
                "format": "json",
                "indent": 4,
                "overwrite": True,
            }
        },
    )
