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
                sections.append(section)
            root.remove(elem)
            section.append(elem)

        for newroot in sections:
            self.make_sections(newroot, depth+1)


class MarkgraphTreeProcessor(Treeprocessor):

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
                    edges.add((context.text, elem.text))
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
                    self.output(cluster, info)
            #string = """digraph {{ {edges} }}""".format(
            #    edges = '\n'.join('"{}" -> "{}";'.format(*e) for e in edges),
            #)
            #call_dot("test.svg", 'svg', string)

    def output(self, cluster, info):
        nodes = cluster.findall("./a[@markgraph-type='node']")
        subclusters = cluster.findall("./*[@markgraph-type='cluster']")




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
