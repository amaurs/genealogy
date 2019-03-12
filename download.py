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
                parent_child.append({"source": current, "target": new_url.split("=")[1]})
                if new_url not in visited:
                    start(new_url)

def get_nodes(node_id):
    node = {}
    node['gen_id'] = node_id
    node['name'] = all_info[node_id]['name']
    node['university'] = all_info[node_id]['school']
    node['dissertation'] = all_info[node_id]['title']
    node['year'] = all_info[node_id]['year']
    children = [x[1] for x in parent_child if x[0] == node_id]
    if children:
        node['children'] = [get_nodes(child_id) for child_id in children]
    return node


good_nodes = {}
good_edges = []

def find_and_add(node, nodes, edges):

    good_nodes[node] = nodes[node]

    for edge in edges:
        if node == edge["source"]:
            good_edges.append(edge)
            find_and_add(edge["target"], nodes, edges)



if __name__ == '__main__':
    url = "%s/id.php?id=%s" % (BASE_URL, sys.argv[1])
    start(url)
    #parents, children = zip(*parent_child)
    #root_nodes = {x for x in parents if x not in children}
    #tree = get_nodes(url.split("=")[1])

    #with open('genealogy.json', 'w') as outfile:
    #    json.dump(tree, outfile, indent=4)

    nodes = dict(all_info)
    for node in all_info:
        if ('school' in all_info[node] and len(all_info[node]['school']) == 0) or ('year' in all_info[node] and len(all_info[node]['year']) == 0) or not all_info[node]['year'].isdigit():
            del nodes[node]

    final_edges = []


    print(parent_child)
    for edge in parent_child:
        if ("source" in edge and edge["source"] in nodes) and ("target" in edge and edge["target"] in nodes):
            final_edges.append(edge)

    final_nodes = dict(nodes)

    for node in nodes:
        found = False
        for edge in final_edges:
            if node == edge["target"]:
                found = True

        if not (found or node == sys.argv[1]):
            del final_nodes[node]



    find_and_add(sys.argv[1], final_nodes, final_edges)


    with open('nodes.json', 'w') as outfile:
        json.dump(good_nodes, outfile, indent=4)

    with open('edges.json', 'w') as outfile:
        json.dump(good_edges, outfile, indent=4)
    print(len(visited))