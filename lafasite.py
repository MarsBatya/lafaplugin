# VERSION: 1.00
# AUTHORS: Mars (mars.hall.tg.fck@gmail.com)
# LICENSING INFORMATION
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"a simple lafasite plugin"

import re
import logging
import random
from html.parser import HTMLParser

from helpers import download_file, retrieve_url
from novaprinter import prettyPrinter

RESOLUTION_PATTERN = re.compile(r"\d+x\d+")

class Parser(HTMLParser):
    "abstract parser"
    results: list

    def get_results(self, data: str) -> list:
        "utility function"
        self.feed(data)
        return self.results


class SearchResultsParser(Parser):
    "a parser that extracts results from the searching html"

    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.results = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag.lower() == "a" and attrs and attrs[0][0] == "href":
            self.results.append(attrs[0][1])


class PageParser(Parser):
    "a parser to extract each torrent info from a particular page"

    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.parsing = {
            "link": "",
            "name": "",
            "size": "",
            "seeds": 0,
            "leech": 0,
            "engine_url": lafasite.url,
            "extra": [],
        }
        self.results = []
        self.working: bool = False
        self.current_thing = ""
        self.current_tr = 0

    def handle_starttag(  # noqa: C901
        self, tag: str, attrs: list[tuple[str, str]],
    ) -> None:
        dattrs = dict(attrs)

        if tag == "tbody" and dattrs.get("class", None) == "tbody_class":
            self.working = True
            return

        if not self.working:
            return

        if tag == "tr":
            if dattrs.get("class", None) == "expand-child":
                self.current_tr = 2
            elif self.current_tr in (0, 3):
                self.current_tr = 1
            else:
                self.current_tr = 3

        if tag == "div" and dattrs.get("style", None) == "float:left;":
            self.current_thing = "name"
        elif tag == "div" and dattrs.get("style", None) == "clear:both;":
            self.current_thing = "desc"
        elif tag == "a" and dattrs.get("class", None) == "dlink_t no-pop":
            self.parsing["link"] = lafasite.url + dattrs["href"]
        elif tag == "td" and dattrs.get("data-sort-value", ""):
            self.current_thing = "size"
        elif tag == "span" and dattrs.get("id", "").startswith("seeders_"):
            self.current_thing = "seeds"
        elif tag == "span" and dattrs.get("id", "").startswith("leechers_"):
            self.current_thing = "leech"
        elif tag == "img" and dattrs.get("src", None) == "/pic/rk.svg":
            self.parsing["extra"].append("📢ADS")

    def handle_endtag(self, tag: str) -> None:
        if not self.working:
            return
        if tag == "tbody":
            self.working = False
        if tag == "tr":
            if self.current_tr in (2, 3):
                if not self.parsing["name"]:
                    return
                self.results.append(self.parsing.copy())
                self.parsing = {
                    "link": "",
                    "name": "",
                    "size": "",
                    "seeds": 0,
                    "leech": 0,
                    "engine_url": lafasite.url,
                    "extra": [],
                }

    def handle_data(self, data: str) -> None:
        if self.current_thing == "name":
            self.parsing["name"] = data.strip()
        elif self.current_thing == "size":
            self.parsing["size"] = data.strip().replace(" ", "")
        elif self.current_thing == "seeds":
            self.parsing["seeds"] = data.strip()
        elif self.current_thing == "leech":
            self.parsing["leech"] = data.strip()
        elif self.current_thing == "desc":
            res = RESOLUTION_PATTERN.search(data)
            if res:
                self.parsing["extra"].append(f"({res.group(0)})")
        else:
            return
        self.current_thing = ""


class lafasite(object):  # noqa: N801
    """
    `url`, `name`, `supported_categories`
    should be static variables of the engine_name class,
     otherwise qbt won't install the plugin.

    `url`: The URL of the search engine.
    `name`: The name of the search engine, spaces
    and special characters are allowed here.
    `supported_categories`: What categories are supported by
    the search engine and their corresponding id,
    possible categories are ('all', 'anime', 'books', 'games',
    'movies', 'music', 'pictures', 'software', 'tv').
    """

    url = "https://top.lafa.site"
    name = "top.lafa.site"
    supported_categories = {
        "all": "0",
        "anime": "7",
        "games": "2",
        "movies": "6",
        "music": "1",
        "software": "3",
        "tv": "4",
    }

    def __init__(self) -> None:
        """
        Some initialization
        """

    def download_torrent(self, info) -> None:
        """
        Providing this function is optional.
        It can however be interesting to provide your own torrent download
        implementation in case the search engine in question does not allow
        traditional downloads (for example, cookie-based download).
        """
        print(download_file(info))

    # DO NOT CHANGE the name and parameters of this function
    # This function will be the one called by nova2.py
    def search(self, what, cat: str = "all") -> None:
        """
        Here you can do what you want to get the result from the search engine website.
        Everytime you parse a result line, store it in a dictionary
        and call the prettyPrint(your_dict) function.

        `what` is a string with the search tokens, already escaped (e.g. "Ubuntu+Linux")
        `cat` is the name of a search category in
        ('all', 'anime', 'books', 'games', 'movies',
        'music', 'pictures', 'software', 'tv')
        """
        logging.debug(
            "this plugin doesn't support search by category: %s", cat,
        )
        search = retrieve_url(
            f"https://top.lafa.site/ajax.php?rnd={random.uniform(0, 1)}"
            f"&action=quicksearch&keyword={what}",
        )
        for path in SearchResultsParser().get_results(search):
            url = self.url + path
            # print(url)
            current_page = retrieve_url(url)
            for result in PageParser().get_results(current_page):
                result["desc_link"] = url
                if result["extra"]:
                    result["name"] += " " + " ".join(result["extra"])
                prettyPrinter(result)


def main() -> None:
    "main function"

    # searching
    lafasite().search("holmes")

    # # downloading a particular page
    # with open('tempage.html', 'w', encoding='utf-8') as file:
    #     file.write(retrieve_url(
    #         "https://top.lafa.site/film/Detektiv/enola-holms-2.htm"
    #     ))

    # # parsing a particular page
    # with open('tempage.html', encoding='utf-8') as file:
    #     text = file.read()
    # for result in PageParser().get_results(text):
    #     print(result)


if __name__ == "__main__":
    main()
