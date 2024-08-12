import argparse
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os

ordered_spiders = [
    "calendar",
    "teams",
    "drivers",
    "news",
    "rally-results",
]

def main(spider: str):
    settings = get_project_settings()

    print(f"Starting to crawl spider: '{spider}'")

    process = CrawlerProcess(settings)
    process.crawl(spider)

    process.start()
    print(f"Finished crawling spider: '{spider}'")

if __name__ == "__main__":
    load_dotenv(os.getenv("ENV_FILE_PATH", None))
    print(f"DB: {os.getenv("MONGO_URI")}")

    parser = argparse.ArgumentParser("WRC Scraper", description="Run wrc spider")
    parser.add_argument("-s", "--spider", type=str, help="name of the spider")

    args = parser.parse_args()

    if args.spider is None:
        raise Exception("YOU MUST PROVIDE A SPIDER. '-s <spider>")

    main(args.spider)
