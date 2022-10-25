import sys
from colorama import Fore
import keyboard
from crawl import Crawler


class Game:
    def __init__(self, width: int, depth: int, hints_enabled: bool = True):
        self.width = width
        self.depth = depth
        self.hints_enabled = hints_enabled
        
        self.crawler = Crawler()
        self.links, self.path = self.crawler.build(width, depth)
        
        self.chosen_path = list(self.links.keys())
        self.current_row = 0

    def _clear(self, n):
        for _ in range(n):
            sys.stdout.write("\033[F")  # back to previous line
            sys.stdout.write("\033[K")  # clear line

    def _max_topic_size(self, links: dict, _max: int | float):
        for k, v in links.items():
            return max(len(k), self._max_topic_size(v, _max))
        return _max

    def _finished_link(self) -> str:
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
            string = '    '.join(
                [topic for topic in final_path]) + Fore.WHITE + '\n' * (self.width)
        else:
            final_path = self.chosen_path + [self.path[-1]]
            if final_path == self.path:
                colour = Fore.GREEN
            else:
                colour = Fore.RED
            string = colour + '    '.join([topic for topic in final_path]) + \
                Fore.WHITE + '\n' * (self.width)
        return string

    @staticmethod
    def _rows_to_str(rows) -> str:
        string = [f"{' -> '.join(rows[0])}\n"]
        for row in rows[1:]:
            string.append(f"{'    '.join(row)}\n")
        return ''.join(string)

    def _inprogress_link(self) -> str:
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
        self.current_row = min(len(next_topics)-1, self.current_row)
        if len(next_topics) > 0:
            max_topic_len = len(max(next_topics, key=len))
        for row, topic in enumerate(next_topics):
            if row == self.current_row:
                colour = Fore.MAGENTA
            else:
                colour = Fore.WHITE
            rows[row][col] = colour + topic.ljust(max_topic_len) + Fore.WHITE

        # Insert final target topic
        rows[0][-1] = self.path[-1]

        # Convert rows to completed string to display
        string = self._rows_to_str(rows)
        return string

    def view(self, clear=True):
        if clear:
            self._clear(self.width)

        if len(self.chosen_path) == len(self.path) - 1:
            string = self._finished_link()
        else:
            string = self._inprogress_link()
        sys.stdout.write(string)

    def _update(self, e: keyboard.KeyboardEvent):
        if e.name == 'up':
            self.current_row = max(0, self.current_row-1)
        elif e.name == 'down':
            self.current_row = min(self.width-1, self.current_row+1)
        elif e.name == 'left':
            if len(self.chosen_path) > 1:
                self.chosen_path.pop()
        elif e.name == 'right':
            cur = self.links
            for i, val in enumerate(self.chosen_path):
                cur = cur[val]

            for i, topic in enumerate(cur.keys()):
                if i == self.current_row:
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

        while True:  # Listening for keyboard events
            pass
