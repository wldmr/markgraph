import sys

from collections import namedtuple

import markdown

from markdown.inlinepatterns import SimpleTagPattern, SimpleTextPattern
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree
from markdown.extensions import Extension

from dot import call_dot


class Regex:
    graph_filename = r'\b(?P<filename>graph_(?P<substring>.+?)\.(?P<filetype>.+?))\b'


class GraphNamePattern(SimpleTextPattern):
    tup = namedtuple("NodeDef", "filename, query, filetype")
    history = set()

    def handleMatch(self, m):
        tup = self.tup(m.group('filename'), m.group('substring'), m.group('filetype'))
        self.history.add(tup)
        #return SimpleTagPattern.handleMatch(self, m)


class MarkgraphOutlineProcessor(Treeprocessor):
    def __init__(self, md, depth=1):
        super(MarkgraphOutlineProcessor, self).__init__(md)
        self.depth = depth
        self.tag = 'h'+str(depth)

    def run(self, root):
        self.make_sections(root, 1)

    def make_sections(self, root, depth):
        tag = 'h'+str(depth)
        section = root
        sections = []
        for elem in root.findall('./*'):
            if elem.tag == tag:
                section = etree.SubElement(root, 'section')
                section.set('title', elem.text)
                elem.tag = "h1"
                elem.text = str(depth) + " " + elem.text
                sections.append(section)
            root.remove(elem)
            section.append(elem)

        for newroot in sections:
            self.make_sections(newroot, depth+1)


class MarkgraphTreeProcessor(Treeprocessor):

    Edge = namedtuple("Edge", 'tail, head')

    def run(self, root):
        # collect edges
        edges = set()
        cluster = root
        context = None
        for elem in root.iter():
            if elem.tag == "section":
                cluster = elem
                elem.set("markgraph-type", "cluster")
            elif elem.tag == "a":
                href = elem.get('href')
                if not href or href.startswith("?"):  # We're linking two graph nodes
                    if context is None:
                        raise Exception("Hey, no context yet: <{e.tag}>{e.text}</{e.tag}>".format(e=elem))
                    edges.add(self.Edge(context.text, elem.text))
                    elem.set('markgraph-type', "node-reference")
                elif href.startswith("!"):  # A node definition
                    context = elem
                    elem.set('markgraph-cluster', cluster.get('title'))
                    elem.set('markgraph-type', "node")
                elif href.startswith(":"):  # We're switching context
                    context = elem

        # Output graphs
        for cluster in root.iterfind(".//section[@markgraph-type='cluster']"):
            for info in GraphNamePattern.history:
                if info.query in cluster.get('title'):
                    print cluster.get('title'), info.query
                    dot = self.cluster2dot(cluster, edges, True)
                    with open(info.filename+".dot", 'w') as f:
                        f.write(dot)
                    with open(info.filename, 'w') as f:
                        f.write(dot)
                    call_dot(info.filename, info.filetype, dot)

    def cluster2dot(self, cluster, edges, standalone=False):
        keyword = "digraph" if standalone else "subgraph"
        dot = "{} cluster_{} ".format(keyword, id(cluster)) + " {\n"

        # Attributes
        #for k, v in cluster.items():
        #    dot += '{}="{}";\n'.format(k, v)

        dot += 'label="{}";\n'.format(cluster.get('title'))

        # Nodes defined here
        xpath = ".//a[@markgraph-cluster='{}']"
        xpath = xpath.format(cluster.get('title'))
        ournodes = set(n.text for n in cluster.findall(xpath))
        for node in ournodes:
            dot += '"{}";\n'.format(node)

        # Subclusters
        for subcluster in cluster.findall("./*[@markgraph-type='cluster']"):
            dot += self.cluster2dot(subcluster, edges)


        if standalone:
            xpath = ".//a[@markgraph-type='node']"
            nodes_internal = set(n.text for n in cluster.findall(xpath))

            xpath = ".//a[@markgraph-type='node-reference']"
            nodes_external = set(n.text for n in cluster.findall(xpath))
            nodes_external -= nodes_internal

            allnodes = nodes_internal | nodes_external

            inneredges = set()
            outeredges = set()

            for edge in edges:
                if edge.tail in allnodes or edge.head in allnodes:
                    if edge.tail in nodes_external or edge.head in nodes_external:
                        outeredges.add(edge)
                    else:
                        inneredges.add(edge)

            for edge in inneredges:
                dot += '"{0.tail}" -> "{0.head}";\n'.format(edge)

            dot += "subgraph outside {\n"
            dot += 'node [color=grey, fontcolor=grey];'
            dot += 'edge [color=grey, fontcolor=grey];'
            for node in nodes_external:
                dot += '"{}";\n'.format(node)
            for edge in outeredges:
                dot += '"{0.tail}" -> "{0.head}";\n'.format(edge)
            dot += "}\n"

        dot += "}\n\n"

        return dot




class MarkgraphExtension(Extension):
    def extendMarkdown(self, md, md_globals):

        graph_def = GraphNamePattern(Regex.graph_filename, "markgraph-filename")
        md.inlinePatterns.add('markgraph_graph', graph_def, '_begin')

        md.treeprocessors['outline'] = MarkgraphOutlineProcessor(md)
        md.treeprocessors['markgraph'] = MarkgraphTreeProcessor(md)


markgraph = MarkgraphExtension()
md = markdown.Markdown(extensions=[markgraph])

for fname in sys.argv[1:]:
    html = md.convertFile(fname)
