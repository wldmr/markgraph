import sys

from collections import namedtuple

import markdown

from markdown.inlinepatterns import SimpleTagPattern, SimpleTextPattern
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree
from markdown.extensions import Extension


class Regex:
    node_def = r'(\|)(.+?)\2'  # |This is a node definition|
    graph_filename = r'\bgraph_(?P<substring>.+?)\.(?P<filetype>.+?)\b'


class NodeDefPattern(SimpleTagPattern):
    history = set()

    def handleMatch(self, m):
        self.history.add(m.group(3))
        return SimpleTagPattern.handleMatch(self, m)

class GraphNamePattern(SimpleTextPattern):
    tup = namedtuple("NodeDef", "filename, query, filetype")
    history = set()

    def handleMatch(self, m):
        tup = self.tup(m.group(2), m.group('substring'), m.group('filetype'))
        self.history.add(tup)
        return SimpleTextPattern.handleMatch(self, m)


class MarkgraphTreeProcessor(Treeprocessor):
    def run(self, root):
        root.text = 'modified content'


class MarkgraphExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        node_def = NodeDefPattern(Regex.node_def, "markgraph-node")
        md.inlinePatterns['markgraph_node'] = node_def

        graph_def = GraphNamePattern(Regex.graph_filename, "markgraph-filename")
        md.inlinePatterns.add('markgraph_graph', graph_def, '_begin')

        md.treeprocessors['markgraph'] = MarkgraphTreeProcessor(md)


markgraph = MarkgraphExtension()
md = markdown.Markdown(extensions=[markgraph])

for fname in sys.argv[1:]:
    html = md.convertFile(fname)
    print >> sys.stderr, "Nodes:", NodeDefPattern.history
    print >> sys.stderr, "Graphs:", GraphNamePattern.history
