#!/bin/env python2.7
# encoding: utf-8

import argparse
import re
from textwrap import wrap

from collections import deque

parser = argparse.ArgumentParser(description='Transform outlines into graphs.')
parser.add_argument('filename', type=unicode, nargs='+',
                    help='files to process')

args = parser.parse_args()

class LineDef:
    """Subclasses must provide a 2-group `regex` attribute.

    Example: `regex = re.compile(r'^(\s*)[*+-] (.*)$')`
    """

    history = deque()

    def __init__(self, string):
        self.match = self.regex.match(string)
        if self.match:
            self.leading = self.match.group(1)
            self.text = self.match.group(2).strip()

            self.history_add(self)

    def __nonzero__(self):
        return bool(self.match)

    def find_parent(self):
        for predecessor in self.history:
            if self.is_parent(predecessor):
                return predecessor
        else:
            return None

    def is_parent(self, other):
        return other.indent < self.indent

    def history_add(self, other):
        self.history.appendleft(other)

    def history_reset(self):
        self.history.clear()

    @property
    def indent(self):
        return len(self.leading)

    def __str__(self):
        text = self.text.replace('"', r'\"')
        lines = wrap(text, 30)
        content = r'\n'.join(lines)
        return '"{}"'.format(content)

class NodeDef(LineDef):
    history = deque()  # All nodes share the same history.

class ChoiceNode(NodeDef):
    regex = re.compile(r'^(\s*)[*+-] (.*)$')

class SequentialNode(NodeDef):
    regex = re.compile(r'^(\s*)\d+\. (.*)$')

    def is_parent(self, other):
        return other.indent <= self.indent and self is not other

class DocumentStructure(LineDef):
    history = deque()

class DocumentStart(DocumentStructure):
    regex = re.compile(r'^()(.*?)$')

class Headline(DocumentStructure):
    regex = re.compile(r'^(#+)(.*?)(?:#+)?$')


class DotObject(object):
    def __init__(self, label, **kwargs):
        self.label = label
        self.attributes = kwargs

    def ref(self):
        return id(self.label)

class Node(DotObject):
    def __str__(self):
        attrs = ", ".join('{}="{}"'.format(k, v) for (k,v) in self.attributes.items())
        label = self.label.replace('"', r'\"')
        label = r'\n'.join(wrap(label, 20))
        return '{} [label="{}" {}];'.format(self.ref(), label, attrs)

class Edge(DotObject):
    def __init__(self, tail, head, **kwargs):
        DotObject.__init__(self, label="", **kwargs)
        self.tail = tail
        self.head = head

    def __str__(self):
        return '{} -> {};'.format(self.tail.ref(), self.head.ref())

class Graph(DotObject):
    template = """{keyword} cluster_{id} {{ label="{label}";\n{attrs}\n\n{nodes}\n\n{edges}\n\n{subgraphs} }}"""

    def __init__(self, label, parent=None, **kwargs):
        DotObject.__init__(self, label, **kwargs)
        self.parent = parent
        self.nodes = list()
        self.edges = list()
        self.subgraphs = list()

    def subgraph(self, label):
        g = Graph(label, parent=self)
        self.subgraphs.append(g)
        return g

    def __str__(self):
        keyword = "subgraph" if self.parent else "digraph"
        attrs = "\n".join('{}="{}"'.format(k, v) for (k,v) in self.attributes.items())
        return self.template.format(
                keyword=keyword,
                label=self.label,
                attrs=attrs,
                id=id(self.label),
                nodes="\n".join(map(str, self.nodes)),
                subgraphs="\n".join(map(str, self.subgraphs)),
                edges="\n".join(map(str, self.edges)))


class GraphCollector(object):
    def __init__(self):
        self.graphs = dict()
        self.nodes = dict()

    def identify_line(self, line):
        for Class in (ChoiceNode, SequentialNode, Headline):
            parsed = Class(line)
            if parsed:
                return parsed
        else:
            return None

    def process(self, thefile):
        headline = docstart = DocumentStart(thefile.name)
        self.graphs[headline] = Graph(label=headline.text)

        for line in thefile:
            theline = self.identify_line(line)
            if isinstance(theline, Headline):
                headline = theline
                NodeDef.history.clear()
                parentgraph = self.graphs[headline.find_parent()]
                currentgraph = parentgraph.subgraph(label=headline.text)
                self.graphs[headline] = currentgraph
            elif isinstance(theline, NodeDef):
                node = self.nodes.get(theline.text, Node(theline.text))
                self.nodes[theline.text] = node
                currentgraph.nodes.append(node)

                parentline = theline.find_parent()
                if parentline:
                    parentnode = self.nodes[parentline.text]
                    edge = Edge(parentnode, node)
                    currentgraph.edges.append(edge)


        return self.graphs[docstart]


collector = GraphCollector()

for filename in args.filename:
    with open(filename) as f:
        graph = collector.process(f)
        print graph
