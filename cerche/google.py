from typing import *
import googlesearch
import requests
from cerche.base import SearchABCRequestHandler
from cerche.custom_logging import print

_DELAY_SEARCH = 1.0  # Making this too low will get you IP banned

class GoogleSearchRequestHandler(SearchABCRequestHandler):
    google_search_url = "https://customsearch.googleapis.com/customsearch/v1"

    def search(
        self,
        q: str,
        n: int,
    ) -> Generator[str, None, None]:
        if not self.server.use_official_google_api:
            return googlesearch.search(q, num=n, stop=None, pause=_DELAY_SEARCH)
        else:
            """
            https://developers.google.com/custom-search/json-api/v1/reference/cse/list
            """
            if self.server.use_description_only:
                raise NotImplementedError(
                    "Google Search does not support description only mode yet"
                )
            base_url = (
                f"{self.google_search_url}?key={self.server.google_search_key}"
                + f"&cx={self.server.google_search_cx}"
            )
            url = f"{base_url}&q={q}&num={n}"
            # if any additional query parameters in self.server.kwargs:
            if self.server.kwargs and "google_search_params" in self.server.kwargs:
                url += "&" + self.server.kwargs["google_search_params"]
            # make the API request
            response = requests.get(url)
            response.raise_for_status()
            json_response = response.json()
            print("self.server.kwargs", self.server.kwargs)
            print(
                '"google_search_params" in self.server.kwargs',
                "google_search_params" in self.server.kwargs,
            )
            print("url", url)
            if "items" not in json_response or len(json_response["items"]) == 0:
                # add in url intitle="information""
                url = f"{base_url}&q=intitle:{q}&num={n}"
                response = requests.get(url)
                response.raise_for_status()
                json_response = response.json()
            data = []
            if "items" not in json_response:
                return data
            for item in json_response["items"]:
                data.append(item["link"])
            return data
