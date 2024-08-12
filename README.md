# WRC scraper

This is a crawler written in Python with Scrapy. It can scrape rally events, team, drivers, news and results. The data will be stored in a Mongo DB.

## Required Environment Variables

- **`MONGO_URI`**: The URI connection string for MongoDB. This is required to connect to the MongoDB database.

## Optional Environment Variables

- **`PLAYWRIGHT_API_SERVER_URI`**: The URI connection string for Playwright API Server. This is required if Javascript rendering will be used. Playwright API Server repo: https://github.com/CypriotUnknown/Playwright-Server.git

- **`ENV_FILE_PATH`**: The path to environment variables file. When using the app in a Docker container, you can declare this path as a Docker Secret path.

## Available spiders

- calendar
- teams
- drivers
- news
- rally-results

Spider name must be passed as an argument (-s or --spider):

```python
python3 main.py -s news
```