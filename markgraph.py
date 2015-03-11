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
    regex = re.compile(r'^(\s*)([*+-]|\d+\.) (.*)$')

    def __init__(self, string):
        self.match = self.regex.match(string)
        if self.match:
            self.leading = self.match.group(1)
            self.nodetype = self.match.group(2)
            self.text = self.match.group(3).strip()

    def __nonzero__(self):
        return bool(self.match)

    def find_parent(self, history):
        for predecessor in history:
            if predecessor.indent < self.indent:
                return predecessor
        else:
            return None
    @property
    def indent(self):
        return len(self.leading)

    def __str__(self):
        text = self.text.replace('"', r'\"')
        lines = wrap(text, 30)
        content = r'\n'.join(lines)
        return '"{}"'.format(content)


class GraphCollector(object):
    def __init__(self):
        self.nodes = dict()
        self.edges = set()
        self.groups = dict()

        self.outfiles = set()

    def process(self, thefile):
        history = deque()
        for line in thefile:
            node = NodeDef(line)
            if node:
                self.nodes[node.text] = node
                parent = node.find_parent(history)
                history.appendleft(node)
                if parent:
                    self.edges.add((parent, node))


collector = GraphCollector()

for filename in args.filename:
    with open(filename) as f:
        collector.process(f)

print "digraph {"
for node in collector.nodes.values():
    print str(node)
for edge in collector.edges:
    print '{} -> {};'.format(edge[0], edge[1])
print "}"
