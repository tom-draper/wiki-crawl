import sys
from types import FunctionType

import keyboard
import numpy as np
import requests
from alive_progress import alive_bar
from colorama import Fore


def valid(link: str) -> bool:
    return ('Wikipedia' not in link and 'Template' not in link
            and 'User' not in link and 'Help' not in link
            and 'Portal' not in link)


def filter_links(links: list[str]) -> list[str]:
    return [link for link in links if valid(link)]


def fetch_page_links(url: str) -> list[str]:
    response = requests.get(url)

    links = []
    if response.status_code == 200:
        try:
            links_json = list(response.json()['query']['pages'].values())[
                0]['links']
            links = [link['title'] for link in links_json]
            links = filter_links(links)
        except KeyError:
            print('Error', url, response.json())
    return links


def fetch_main_page_links() -> list[str]:
    url = "https://en.wikipedia.org/w/api.php?action=query&titles=Main_Page&prop=links&format=json&pllimit=max"
    return fetch_page_links(url)


def select_n_links(links: list[str], n: int) -> list[str]:
    selected = list(set(np.random.choice(links, size=n)))
    return selected


def topic_url(topic: str) -> str:
    return f"https://en.wikipedia.org/w/api.php?format=xml&action=query&prop=links&format=json&redirects=true&titles={topic.replace(' ', '%20')}"


def crawl(url: dict, links: dict, path: list[str], on_path: bool, depth: int,
          width: int, bar: FunctionType):
    """
    Crawl Wikipedia links from url, adding a tree of results to the links dict.
    For each link, it crawls [width] new links on that page.
    Continues until a chain of links of length [depth] has been achieved.
    """
    bar()  # Update progress bar
    if depth < 1:
        return

    page_links = fetch_page_links(url)
    selected = select_n_links(page_links, width)
    next_topic = np.random.choice(selected)

    # If currently on the correct link path, extend path with chosen topic
    if on_path:
        path.append(next_topic)

    for topic in selected:
        links[topic] = {}
        crawl(topic_url(topic), links[topic], path,
              on_path and topic == next_topic, depth-1, width, bar)


def insert_final_topic(path: str, bar) -> str:
    bar()
    page_links = fetch_page_links(topic_url(path[-1]))
    selected = select_n_links(page_links, width)
    topic = np.random.choice(selected)
    path.append(topic)


def build(width, depth) -> tuple[dict, list[str]]:
    links = fetch_main_page_links()
    starting_topic = np.random.choice(links)
    print(starting_topic)

    links = {starting_topic: {}}
    path = [starting_topic]
    n_nodes = int((width**(depth+1)-1) / (width - 1)) + 1
    
    if n_nodes > 800:
        print('Number of links too high ({n_nodes})')
        return {}, []
        
    with alive_bar(n_nodes) as bar:
        crawl(topic_url(starting_topic),
              links[starting_topic], path, True, depth, width, bar)
        insert_final_topic(path, bar)

    return links, path


class Game:
    def __init__(self, width, depth, hints_enabled=True):
        self.width = width
        self.depth = depth
        self.hints_enabled = hints_enabled
        self.links, self.path = build(width, depth)
        self.chosen_path = list(self.links.keys())
        self.current_width = 0

    def _clear(self, n):
        for _ in range(n):
            sys.stdout.write("\033[F")  # back to previous line
            sys.stdout.write("\033[K")  # clear line

    def _max_topic_size(self, links, _max):
        for k, v in links.items():
            return max(len(k), self._max_topic_size(v, _max))
        return _max

    def view(self, clear=True):
        if clear:
            self._clear(self.width)

        print(len(self.path), self.path)
        if len(self.chosen_path) == len(self.path) - 1:
            if self.hints_enabled:
                # Show green topics up until first mistake
                final_path = self.chosen_path + [self.path[-1]]
                mistake = False
                for i, topic in enumerate(final_path):
                    if topic == self.path[i] and not mistake:
                        final_path[i] = Fore.GREEN + topic
                    else:
                        final_path[i] = Fore.RED + topic
                        mistake = True
                string = '    '.join([topic for topic in final_path]) + Fore.WHITE + '\n' * (self.width)
            else:
                final_path = self.chosen_path + [self.path[-1]]
                if final_path == self.path:
                    colour = Fore.GREEN
                else:
                    colour = Fore.RED
                string = colour + '    '.join([topic for topic in final_path]) + \
                    Fore.WHITE + '\n' * (self.width)
        else:
            # Init rows
            rows = [['' for _ in range(self.depth+2)]
                    for _ in range(self.width)]

            # Insert path followed so far
            for col, topic in enumerate(self.chosen_path):
                rows[0][col] = Fore.CYAN + topic + Fore.WHITE
                for i in range(1, self.width):
                    rows[i][col] = ' '*len(topic)

            # Travel to current topic in links tree to access next topics available
            cur = self.links
            for topic in self.chosen_path:
                cur = cur[topic]
            next_topics = list(cur.keys())

            # Insert options available from current position
            col = len(self.chosen_path)
            self.current_width = min(len(next_topics)-1, self.current_width)
            if len(next_topics) > 0:
                max_topic_len = len(max(next_topics, key=len))
            for row, topic in enumerate(next_topics):
                if row == self.current_width:
                    colour = Fore.MAGENTA
                else:
                    colour = Fore.WHITE
                rows[row][col] = colour + \
                    topic.ljust(max_topic_len) + Fore.WHITE

            # Insert final target topic
            rows[0][-1] = self.path[-1]

            # Convert rows to completed string to display
            string = ' -> '.join(rows[0]) + '\n'
            for row in rows[1:]:
                string += '    '.join(row) + '\n'
        sys.stdout.write(string)

    def _update(self, e: str):
        if e.name == 'up':
            self.current_width = max(0, self.current_width-1)
        elif e.name == 'down':
            self.current_width = min(self.width-1, self.current_width+1)
        elif e.name == 'left':
            if len(self.chosen_path) > 1:
                self.chosen_path.pop()
        elif e.name == 'right':
            cur = self.links
            for i, val in enumerate(self.chosen_path):
                cur = cur[val]

            for i, topic in enumerate(cur.keys()):
                if i == self.current_width:
                    self.chosen_path.append(topic)
                    break

        self.view()

    def run(self):
        keyboard.on_press_key("left", self._update)
        keyboard.on_press_key("right", self._update)
        keyboard.on_press_key("up", self._update)
        keyboard.on_press_key("down", self._update)

        self._clear(2)
        self.view(clear=False)

        while True:
            pass


if __name__ == '__main__':
    width, depth = 6, 2
    Game(width, depth).run()
