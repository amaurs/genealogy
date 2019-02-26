import sys
import requests
from bs4 import BeautifulSoup
import json

BASE_URL = 'https://www.genealogy.math.ndsu.nodak.edu/'
visited = []
parent_child = []
all_info = {}

def start(url):
    print("Processing: %s" % url)
    current = url.split("=")[1]
    info = {}
    req = requests.get(url)
    visited.append(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    info['name'] = soup.find("title").text.split(' - ')[0].rstrip()
    for span in soup.findAll("span"):
        if 'id' in span.attrs and span['id'] == 'thesisTitle' and len(span.text) > 0:
            info['title'] = span.text.rstrip().strip('\n')
        if 'style' in span.attrs and 'margin-left: 0.5em' in span['style']:
            info['school'] = span.text.rstrip()
        if 'style' in span.attrs and 'margin-right: 0.5em' in span['style']:
            info['year'] = span.text.rstrip().split(" ")[-1]
    all_info[current] = info
    for paragraph in soup.findAll("p"):
        if "Advisor" in paragraph.text:
            for link in paragraph.findAll("a"):
                new_url = BASE_URL + link['href']
                if new_url not in visited:
                    parent_child.append((current, new_url.split("=")[1]))
                    start(new_url)

def get_nodes(node_id):
    node = {}
    node['id'] = node_id
    node['name'] = all_info[node_id]['name']
    node['university'] = all_info[node_id]['school']
    node['dissertation'] = all_info[node_id]['title']
    node['year'] = all_info[node_id]['year']
    children = [x[1] for x in parent_child if x[0] == node_id]
    if children:
        node['children'] = [get_nodes(child_id) for child_id in children]
    return node

if __name__ == '__main__':
    url = "%s/id.php?id=%s" % (BASE_URL, sys.argv[1])
    start(url)
    parents, children = zip(*parent_child)
    root_nodes = {x for x in parents if x not in children}
    tree = get_nodes(url.split("=")[1])
    with open('genealogy.json', 'w') as outfile:
        json.dump(tree, outfile, indent=4)
    print(len(visited))