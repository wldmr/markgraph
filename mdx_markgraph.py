import sys

from collections import namedtuple

import markdown

from markdown.inlinepatterns import SimpleTagPattern, SimpleTextPattern
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree
from markdown.extensions import Extension

from dot import call_dot


class Regex:
    graph_filename = r'\bgraph_(?P<substring>.+?)\.(?P<filetype>.+?)\b'


class GraphNamePattern(SimpleTextPattern):
    tup = namedtuple("NodeDef", "filename, query, filetype")
    history = set()

    def handleMatch(self, m):
        tup = self.tup(m.group(2), m.group('substring'), m.group('filetype'))
        self.history.add(tup)
        #return SimpleTagPattern.handleMatch(self, m)


class MarkgraphTreeProcessor(Treeprocessor):

    headtags = set('h'+str(i) for i in range(1,6))

    margraphtags = set(('markgraph-node', 'markgraph-filename', 'markgraph-reference'))

    def run(self, root):
        # collect edges
        edges = set()
        cluster = root
        context = None
        for elem in root.iter():
            if elem.tag in self.headtags:
                cluster = elem
            elif elem.tag == "a":
                href = elem.get('href')
                if not href or href.startswith("?"):  # We're linking two graph nodes
                    if context is None:
                        raise Exception("Hey, no context yet: <{e.tag}>{e.text}</{e.tag}>".format(e=elem))
                    edges.add((context.text, elem.text))
                elif href.startswith("!"):  # A node definition
                    context = elem
                    elem.set('cluster', cluster)
                elif href.startswith(":"):  # We're switching context
                    context = elem

        # Output graph
        string = """digraph {{ {edges} }}""".format(
            edges = '\n'.join('"{}" -> "{}";'.format(*e) for e in edges),
        )
        call_dot("test.svg", 'svg', string)




class MarkgraphExtension(Extension):
    def extendMarkdown(self, md, md_globals):

        graph_def = GraphNamePattern(Regex.graph_filename, "markgraph-filename")
        md.inlinePatterns.add('markgraph_graph', graph_def, '_begin')

        md.treeprocessors['markgraph'] = MarkgraphTreeProcessor(md)


markgraph = MarkgraphExtension()
md = markdown.Markdown(extensions=[markgraph])

for fname in sys.argv[1:]:
    html = md.convertFile(fname)
