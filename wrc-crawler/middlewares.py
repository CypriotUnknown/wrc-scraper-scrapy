# middlewares.py

import requests
import os
from scrapy.http import HtmlResponse
from scrapy.exceptions import IgnoreRequest


class PlaywrightMiddleware:

    def process_request(self, request, spider):
        # Construct the API URL with the original request URL as a parameter
        api_url = os.getenv("PLAYWRIGHT_API_SERVER_URI")

        if api_url is None:
            raise IgnoreRequest(
                f"'PLAYWRIGHT_API_SERVER_URI' missing in the environment"
            )

        payload = {
            "url": request.url,
            "optionalActions": [
                # "div[id='onetrust-consent-sdk'] button[id='onetrust-reject-all-handler']"
            ],
        }
        # Send the request to the external API
        response = requests.post(api_url, json=payload)

        # If the API returns a successful response, return an HtmlResponse object
        if response.status_code == 200:
            return HtmlResponse(
                url=request.url,
                body=response.content,
                encoding="utf-8",
                request=request,
            )
        else:
            spider.logger.error(f"Failed to fetch {request.url} through API")
            raise IgnoreRequest(
                f"API returned non-200 status code: {response.status_code}"
            )
