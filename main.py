from types import FunctionType
import requests
from pprint import pprint
import numpy as np
from alive_progress import alive_bar


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
            links_json = list(response.json()['query']['pages'].values())[0]['links']
        except KeyError:
            print('Error', url, response.json())
        links = [link['title'] for link in links_json]
        links = filter_links(links)
    return links

def fetch_main_page_links() -> list[str]:
    url = "https://en.wikipedia.org/w/api.php?action=query&titles=Main_Page&prop=links&format=json&pllimit=max"
    return fetch_page_links(url)

def select_n_links(links: list[str], n: int) -> list[str]:
    selected = np.random.choice(links, size=n)
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
        crawl(topic_url(topic), links[topic], path, topic == next_topic, depth-1, width, bar)

def build():
    links = fetch_main_page_links()
    starting_topic = np.random.choice(links)
    print(starting_topic)
    
    links = {starting_topic: {}}
    path = [starting_topic]
    depth, width = 3, 3
    n_nodes = int((width**(depth+1)-1) / (width - 1))
    with alive_bar(n_nodes) as bar:
        crawl(topic_url(starting_topic), links[starting_topic], path, True, depth, width, bar)

if __name__ == '__main__':
    build()