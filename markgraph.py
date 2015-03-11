#!/bin/env python2.7

import argparse
import re
from textwrap import wrap

from collections import deque

parser = argparse.ArgumentParser(description='Transform outlines into graphs.')
parser.add_argument('filename', type=unicode, nargs='+',
                    help='files to process')

args = parser.parse_args()

class NodeDef:
    """Subclasses must provide a 2-group `regex` attribute
    and define a find_parent method.

    Example: `regex = re.compile(r'^(\s*)[*+-] (.*)$')`
    """

    def __init__(self, string):
        self.match = self.regex.match(string)
        if self.match:
            self.leading = self.match.group(1)
            self.text = self.match.group(2).strip()

    def __nonzero__(self):
        return bool(self.match)

    @property
    def indent(self):
        return len(self.leading)

    def __str__(self):
        text = self.text.replace('"', r'\"')
        lines = wrap(text, 30)
        content = r'\n'.join(lines)
        return '"{}"'.format(content)

class ChoiceNode(NodeDef):
    regex = re.compile(r'^(\s*)[*+-] (.*)$')

    def find_parent(self, history):
        for predecessor in history:
            if predecessor.indent < self.indent:
                return predecessor
        else:
            return None

class SequentialNode(NodeDef):
    regex = re.compile(r'^(\s*)\d+\. (.*)$')

    def find_parent(self, history):
        for predecessor in history:
            if predecessor.indent <= self.indent:
                return predecessor
        else:
            return None


class Edge(object):
    def __init__(self, tail, head):
        self.tail = tail
        self.head = head

    def __str__(self):
        return '{} -> {};\n'.format(self.tail, self.head)


class Graph(object):
    template = """digraph {{ {nodes}\n\n{edges} }}"""

    def __init__(self, label):
        self.label = label
        self.nodes = set()
        self.edges = set()

    def __str__(self):
        return self.template.format(
                label=self.label,
                nodes="\n".join(map(str, self.nodes)),
                edges="\n".join(map(str, self.edges)))


class GraphCollector(object):
    def __init__(self):
        self.nodes = dict()
        self.edges = set()
        self.groups = dict()

        self.outfiles = set()

    def identify_line(self, line):
        for Class in (ChoiceNode, SequentialNode):
            parsed = Class(line)
            if parsed:
                return parsed
        else:
            return None

    def process(self, thefile):
        graph = Graph(thefile)
        history = deque()
        for line in thefile:
            node = self.identify_line(line)
            if node:
                graph.nodes.add(node)
                parent = node.find_parent(history)
                history.appendleft(node)
                if parent:
                    graph.edges.add(Edge(parent, node))
        return graph


collector = GraphCollector()

for filename in args.filename:
    with open(filename) as f:
        graph = collector.process(f)
        print graph
