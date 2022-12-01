"""
A search engine API for ParlAI search augmented conversational AI.
"""
import http.server
import re
from typing import *
import fire
import parlai.agents.rag.retrieve_api
from cerche.bing import BingSearchRequestHandler
from cerche.google import GoogleSearchRequestHandler
from cerche.custom_logging import print

_DEFAULT_HOST = "0.0.0.0"
_DEFAULT_PORT = 8080
_REQUESTS_GET_TIMEOUT = 5  # seconds


def _parse_host(host: str) -> Tuple[str, int]:
    """Parse the host string.
    Should be in the format HOSTNAME:PORT.
    Example: 0.0.0.0:8080
    """
    splitted = host.split(":")
    hostname = splitted[0]
    port = splitted[1] if len(splitted) > 1 else _DEFAULT_PORT
    return hostname, int(port)


class SearchABCServer(http.server.ThreadingHTTPServer):
    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        requests_get_timeout: int,
        max_text_bytes: int,
        strip_html_menus: bool,
        use_description_only=False,
        subscription_key=None,
        use_official_google_api: bool = False,
        google_search_key: str = None,
        google_search_cx: str = None,
        use_dataset_urls: str = None,
        **kwargs,
    ):

        self.requests_get_timeout = requests_get_timeout
        self.max_text_bytes = max_text_bytes
        self.strip_html_menus = strip_html_menus
        self.use_description_only = use_description_only
        self.subscription_key = subscription_key
        self.use_official_google_api = use_official_google_api
        self.google_search_key = google_search_key
        self.google_search_cx = google_search_cx
        self.kwargs = kwargs["kwargs"]

        super().__init__(server_address, RequestHandlerClass)


class Application:
    def serve(
        self,
        host: str = _DEFAULT_HOST,
        requests_get_timeout: int = _REQUESTS_GET_TIMEOUT,
        strip_html_menus: bool = False,
        max_text_bytes: int = None,
        search_engine: str = "Google",
        use_description_only: bool = False,
        subscription_key: str = None,
        use_official_google_api: bool = False,
        google_search_key: str = None,
        google_search_cx: str = None,
        use_dataset_urls: str = None,
        **kwargs,
    ) -> NoReturn:
        """Main entry point: Start the server.
        Arguments:
            host (str):
            requests_get_timeout (int):
            strip_html_menus (bool):
            max_text_bytes (int):
            search_engine (str):
            use_description_only (bool):
            subscription_key (str):
            use_official_google_api (bool):
            google_search_key (str):
            google_search_cx (str):
            use_dataset_urls (str):
        HOSTNAME:PORT of the server. HOSTNAME can be an IP.
        Most of the time should be 0.0.0.0. Port 8080 doesn't work on colab.
        Other ports also probably don't work on colab, test it out.
        requests_get_timeout defaults to 5 seconds before each url fetch times out.
        strip_html_menus removes likely HTML menus to clean up text.
        max_text_bytes limits the bytes returned per web page. Set to no max.
            Note, ParlAI current defaults to 512 byte.
        search_engine set to "Google" default or "Bing"
        use_description_only are short but 10X faster since no url gets
            for Bing only
        use_subscription_key required to use Bing only. Can get a free one at:
            https://www.microsoft.com/en-us/bing/apis/bing-entity-search-api
        use_official_google_api is slower but more accurate.
        google_search_key and google_search_cx required to use Google only.
            Can get a free one at:
            https://developers.google.com/custom-search/v1/overview
        google_search_cx is the search engine ID.
        use_dataset_urls will use a list of url from a Huggingface dataset hosted on GCP.
        """
        hostname, port = _parse_host(host)
        host = f"{hostname}:{port}"

        if use_dataset_urls:
            import gcsfs
            from datasets import load_from_disk

            gcs = gcsfs.GCSFileSystem()

            dataset = load_from_disk(use_dataset_urls, fs=gcs)
            df = dataset.to_pandas()
            unique_websites = list(
                set(
                    [
                        re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
                        for url in df["url"]
                    ]
                )
            )
            if len(unique_websites) > 200:
                print("[!] clipping to 200 websites")
                unique_websites = unique_websites[:200]
            print("using", len(unique_websites), "dataset urls")
            websites_as_google_search_params = "&".join(
                [f"siteSearch={website}" for website in unique_websites]
            )
            # add in kwargs google search params
            kwargs["google_search_params"] = (
                kwargs["google_search_params"] + websites_as_google_search_params
                if "google_search_params" in kwargs
                else websites_as_google_search_params
            )

        self.check_and_print_cmdline_args(
            requests_get_timeout,
            strip_html_menus,
            max_text_bytes,
            search_engine,
            use_description_only,
            subscription_key,
            use_official_google_api,
            google_search_key,
            google_search_cx,
            use_dataset_urls,
            kwargs,
        )

        if search_engine == "Bing":
            request_handler = BingSearchRequestHandler
        else:
            request_handler = GoogleSearchRequestHandler

        with SearchABCServer(
            server_address=(hostname, int(port)),
            RequestHandlerClass=request_handler,
            requests_get_timeout=requests_get_timeout,
            strip_html_menus=strip_html_menus,
            max_text_bytes=max_text_bytes,
            use_description_only=use_description_only,
            subscription_key=subscription_key,
            use_official_google_api=use_official_google_api,
            google_search_key=google_search_key,
            google_search_cx=google_search_cx,
            use_dataset_urls=use_dataset_urls,
            kwargs=kwargs,
        ) as server:
            print("Serving forever.")
            print(f"Host: {host}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                print("Shutting down.")
                # Clean-up server (close socket, etc.)
                server.server_close()

    def check_and_print_cmdline_args(
        self,
        requests_get_timeout,
        strip_html_menus,
        max_text_bytes,
        search_engine,
        use_description_only,
        subscription_key,
        use_official_google_api,
        google_search_key,
        google_search_cx,
        use_dataset_urls,
        kwargs,
    ) -> None:

        if search_engine == "Bing":
            if subscription_key is None:
                print("Warning: subscription_key is required for Bing Search Engine")
                print("To get one go to url:")
                print(
                    "https://www.microsoft.com/en-us/bing/apis/bing-entity-search-api"
                )
                exit()
        elif search_engine == "Google":
            if use_description_only:
                print(
                    "Warning: use_description_only is not supported for Google Search Engine"
                )
                exit()
            if subscription_key is not None:
                print(
                    "Warning: subscription_key is not supported for Google Search Engine"
                )
                exit()
            if use_official_google_api:
                if google_search_key is None:
                    print(
                        "Warning: google_search_key is required for Google Search Engine"
                    )
                    print("To get one go to url:")
                    print("https://developers.google.com/custom-search/v1/overview")
                    exit()
                if google_search_cx is None:
                    print(
                        "Warning: google_search_cx is required for Google Search Engine"
                    )
                    print("To get one go to url:")
                    print("https://developers.google.com/custom-search/v1/overview")
                    exit()

        print("Command line args used:")
        print(f"  requests_get_timeout={requests_get_timeout}")
        print(f"  strip_html_menus={strip_html_menus}")
        print(f"  max_text_bytes={max_text_bytes}")
        print(f"  search_engine={search_engine}")
        print(f"  use_description_only={use_description_only}")
        print(f"  subscription_key={subscription_key}")
        print(f"  use_official_google_api={use_official_google_api}")
        print(f"  google_search_key={google_search_key}")
        print(f"  google_search_cx={google_search_cx}")
        print(f"  use_dataset_urls={use_dataset_urls}")
        # overflow elipsis if the kwargs are too big
        clipped_kwargs = [
            f"{k}={v}" if len(f"{k}={v}") < 100 else f"{k}=<{len(v)} bytes>"
            for k, v in kwargs.items()
        ]
        print(f"  kwargs={clipped_kwargs}")

    def test_server(self, query: str, n: int, host: str = _DEFAULT_HOST) -> None:

        """Creates a thin fake client to test a server that is already up.
        Expects a server to have already been started with `python search_server.py serve [options]`.
        Creates a retriever client the same way ParlAi client does it for its chat bot, then
        sends a query to the server.
        """
        host, port = _parse_host(host)

        print(f"Query: `{query}`")
        print(f"n: {n}")

        retriever = parlai.agents.rag.retrieve_api.SearchEngineRetriever(
            dict(
                search_server=f"{host}:{port}",
                skip_retrieval_token=False,
            )
        )
        print("Retrieving one.")
        print(retriever.retrieve([query], n))
        print("Done.")

def main():
    fire.Fire(Application)

if __name__ == "__main__":
    main()
