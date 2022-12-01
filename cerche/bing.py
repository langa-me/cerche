from typing import *
import requests
from cerche.base import SearchABCRequestHandler
from cerche.custom_logging import print

def filter_special_chars(title):
    title = title.replace("&quot", "")
    title = title.replace("&amp", "")
    title = title.replace("&gt", "")
    title = title.replace("&lt", "")
    title = title.replace("&#39", "")
    title = title.replace("\u2018", "")  # unicode single quote
    title = title.replace("\u2019", "")  # unicode single quote
    title = title.replace("\u201c", "")  # unicode left double quote
    title = title.replace("\u201d", "")  # unicode right double quote
    title = title.replace("\u8220", "")  # unicode left double quote
    title = title.replace("\u8221", "")  # unicode right double quote
    title = title.replace("\u8222", "")  # unicode double low-9 quotation mark
    title = title.replace("\u2022", "")  # unicode bullet
    title = title.replace("\u2013", "")  # unicode dash
    title = title.replace("\u00b7", "")  # unicode middle dot
    title = title.replace("\u00d7", "")  # multiplication sign
    return title


class BingSearchRequestHandler(SearchABCRequestHandler):
    bing_search_url = "https://api.bing.microsoft.com/v7.0/search"

    def search(
        self,
        q: str,
        n: int,
    ) -> Generator[str, None, None]:
        types = ["News", "Entities", "Places", "Webpages"]
        promote = ["News"]

        print(f"n={n} responseFilter={types}")
        headers = {"Ocp-Apim-Subscription-Key": self.server.subscription_key}
        params = {
            "q": q,
            "textDecorations": False,
            "textFormat": "HTML",
            "responseFilter": types,
            "promote": promote,
            "answerCount": 5,
        }
        response = requests.get(
            BingSearchRequestHandler.bing_search_url, headers=headers, params=params
        )
        response.raise_for_status()
        search_results = response.json()

        items = []
        if "news" in search_results and "value" in search_results["news"]:
            print(f'bing adding {len(search_results["news"]["value"])} news')
            items = items + search_results["news"]["value"]

        if "webPages" in search_results and "value" in search_results["webPages"]:
            print(f'bing adding {len(search_results["webPages"]["value"])} webPages')
            items = items + search_results["webPages"]["value"]

        if "entities" in search_results and "value" in search_results["entities"]:
            print(f'bing adding {len(search_results["entities"]["value"])} entities')
            items = items + search_results["entities"]["value"]

        if "places" in search_results and "value" in search_results["places"]:
            print(f'bing adding {len(search_results["places"]["value"])} places')
            items = items + search_results["places"]["value"]

        urls = []
        contents = []
        news_count = 0

        for item in items:
            if "url" not in item:
                continue
            else:
                url = item["url"]

            title = item["name"]

            # Remove Bing formatting characters from title
            title = filter_special_chars(title)

            if title is None or title == "":
                print("No title to skipping")
                continue

            if self.server.use_description_only:
                content = title + ". "
                if "snippet" in item:
                    snippet = filter_special_chars(item["snippet"])
                    content += snippet
                    print(f"Adding webpage summary with title {title} for url {url}")
                    contents.append({"title": title, "url": url, "content": content})

                elif "description" in item:
                    if news_count < 3:
                        text = filter_special_chars(item["description"])
                        content += text
                        news_count += 1
                        contents.append(
                            {"title": title, "url": url, "content": content}
                        )
                else:
                    print(f"Could not find descripton for item {item}")
            else:
                if url not in urls:
                    urls.append(url)

        if len(urls) == 0 and not self.server.use_description_only:
            print(f"Warning: No Bing URLs found for query {q}")

        if self.server.use_description_only:
            return contents
        else:
            return urls
