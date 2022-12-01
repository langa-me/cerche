import html
import http.server
import json
import re
from typing import *
import urllib.parse
import threading
import bs4
import chardet
import html2text
import rich
import rich.markup
import requests
from cerche.custom_logging import print

_STYLE_GOOD = "[green]"
_STYLE_SKIP = ""
_CLOSE_STYLE_GOOD = "[/]" if _STYLE_GOOD else ""
_CLOSE_STYLE_SKIP = "[/]" if _STYLE_SKIP else ""

def _get_and_parse(url: str, timeout: int) -> Dict[str, str]:
    """Download a webpage and parse it."""

    try:
        resp = requests.get(url, timeout=timeout)
    except requests.exceptions.RequestException as e:
        print(f"[!] {e} for url {url}")
        return None
    else:
        resp.encoding = resp.apparent_encoding
        page = resp.text

    ###########################################################################
    # Prepare the title
    ###########################################################################
    output_dict = dict(title="", content="", url=url)
    soup = bs4.BeautifulSoup(page, features="lxml")
    pre_rendered = soup.find("title")
    output_dict["title"] = (
        html.unescape(pre_rendered.renderContents().decode()) if pre_rendered else ""
    )

    output_dict["title"] = output_dict["title"].replace("\n", "").replace("\r", "")

    ###########################################################################
    # Prepare the content
    ###########################################################################
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = True
    text_maker.ignore_tables = True
    text_maker.ignore_images = True
    text_maker.ignore_emphasis = True
    text_maker.single_line = True
    output_dict["content"] = html.unescape(text_maker.handle(page).strip())

    return output_dict


class SearchABCRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        message = threading.currentThread().getName()
        self.wfile.write(message.encode())
        self.wfile.write("\n".encode())
        return

    def do_POST(self):

        """Handle POST requests from the client. (All requests are POST)"""

        #######################################################################
        # Prepare and Parse
        #######################################################################
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        # Figure out the encoding
        if "charset=" in self.headers["Content-Type"]:
            charset = re.match(
                r".*charset=([\w_\-]+)\b.*", self.headers["Content-Type"]
            ).group(1)
        else:
            detector = chardet.UniversalDetector()
            detector.feed(post_data)
            detector.close()
            charset = detector.result["encoding"]

        post_data = post_data.decode(charset)
        parsed = urllib.parse.parse_qs(post_data)

        for v in parsed.values():
            assert len(v) == 1, len(v)
        parsed = {k: v[0] for k, v in parsed.items()}

        #######################################################################
        # Search, get the pages and parse the content of the pages
        #######################################################################
        print(f"\n[bold]Received query:[/] {parsed}")

        n = int(parsed["n"])
        q = parsed["q"]

        # Over query a little bit in case we find useless URLs
        content = []
        dupe_detection_set = set()

        urls = []
        results = self.search(
            q=q,
            n=n,
        )

        if self.server.use_description_only:
            content = results
        else:
            urls = results

        # Only execute loop to fetch each URL if urls returned
        for url in urls:
            if len(content) >= n:
                break

            # Get the content of the pages and parse it
            maybe_content = _get_and_parse(url, self.server.requests_get_timeout)

            # Check that getting the content didn't fail
            reason_empty_response = maybe_content is None
            if not reason_empty_response:
                reason_content_empty = (
                    maybe_content["content"] is None
                    or len(maybe_content["content"]) == 0
                )
                reason_already_seen_content = (
                    maybe_content["content"] in dupe_detection_set
                )
                reason_content_forbidden = maybe_content["content"] == "Forbidden"
            else:
                reason_content_empty = False
                reason_already_seen_content = False
                reason_content_forbidden = False

            reasons = dict(
                reason_empty_response=reason_empty_response,
                reason_content_empty=reason_content_empty,
                reason_already_seen_content=reason_already_seen_content,
                reason_content_forbidden=reason_content_forbidden,
            )

            if not any(reasons.values()):
                ###############################################################
                # Log the entry
                ###############################################################
                title_str = (
                    f"`{rich.markup.escape(maybe_content['title'])}`"
                    if maybe_content["title"]
                    else "<No Title>"
                )
                print(
                    f" {_STYLE_GOOD}>{_CLOSE_STYLE_GOOD} Result: Title: {title_str}\n"
                    f"   {rich.markup.escape(maybe_content['url'])}"
                    # f"Content: {len(maybe_content['content'])}",
                )

                # Strip out all lines starting with "* " usually menu items
                if self.server.strip_html_menus:
                    new_content = ""
                    for line in maybe_content["content"].splitlines():
                        x = re.findall("^[\s]*\\* ", line)
                        if line != "" and (not x or len(line) > 50):
                            new_content += line + "\n"

                    maybe_content["content"] = filter_special_chars(new_content)

                # Truncate text
                maybe_content["content"] = maybe_content["content"][
                    : self.server.max_text_bytes
                ]

                dupe_detection_set.add(maybe_content["content"])
                content.append(maybe_content)
                if len(content) >= n:
                    break

            else:
                ###############################################################
                # Log why it failed
                ###############################################################
                reason_string = ", ".join(
                    {
                        reason_name
                        for reason_name, whether_failed in reasons.items()
                        if whether_failed
                    }
                )
                print(
                    f" {_STYLE_SKIP}x{_CLOSE_STYLE_SKIP} Excluding an URL because `{_STYLE_SKIP}{reason_string}{_CLOSE_STYLE_SKIP}`:\n"
                    f"   {url}"
                )

        ###############################################################
        # Prepare the answer and send it
        ###############################################################
        content = content[:n]
        output = json.dumps(dict(response=content)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", len(output))
        self.end_headers()
        self.wfile.write(output)

    def search(
        self,
        q: str,
        n: int,
    ) -> Generator[str, None, None]:

        return NotImplemented(
            "Search is an abstract base class, not meant to be directly "
            "instantiated. You should instantiate a derived class like "
            "GoogleSearch."
        )


