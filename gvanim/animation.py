#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from typing import List, Dict
from email.utils import quote
import shlex
import subprocess
import pathos.multiprocessing as mp
from gvanim import action


class ParseException(Exception):
    """
    ParseException
    """


class Step():
    """
    对应动画里的一帧

    V: set of vertexs
    E: set of edges
    lV: {v:label for v in V}
    lE: {e:label for e in E}
    hV: {e:color for v in V}
    hE: {e:color for e in E}
    """

    def __init__(self, step=None):
        if step:
            self.V = step.V.copy()
            self.E = step.E.copy()
            self.lV = step.lV.copy()
            self.lE = step.lE.copy()
            self.hV = step.hV.copy()
            self.hE = step.hE.copy()
        else:
            self.V = set()
            self.E = set()
            self.lV = dict()    # label of vertex
            self.lE = dict()    # label of edge
            self.hV = dict()        # high light of V (color)
            self.hE = dict()        # high light of E (color)

    def node_format(self, v) -> str:
        """
        get format string of node `v` according t self.LV and self.hV
        """
        fmt = []

        if v in self.lV:
            fmt.append('label="{}"'.format(quote(str(self.lV[v]))))

        if v in self.hV:
            fmt.append('color={}'.format(self.hV[v]))

        if v not in self.V:
            fmt.append('style=invis')  # invisiable

        if fmt:
            return '[{}]'.format(', '.join(fmt))

        return ''

    def edge_format(self, e):
        """
        formate of edge
        """
        fmt = []
        if e in self.lE:
            fmt.append('label="{}"'.format(quote(str(self.lE[e]))))

        if e in self.hE:
            fmt.append('color={}'.format(self.hE[e]))

        if e not in self.E:
            fmt.append('style=invis')

        if fmt:
            return '[{}]'.format(', '.join(fmt))

        return ''

    def __repr__(self):
        """
        repr
        """
        return '{{ V = {}, E = {}, hV = {}, hE = {}, lV = {}, lE = {} }}'.format(self.V, self.E, self.hV, self.hE, self.lV, self.lE)

    def graph(self, directed=True) -> str:
        """
        dot string
        """
        graph = []

        if directed:
            graph.append('digraph G {')
        else:
            graph.append('graph G {')

        for v in self.V:
            graph.append('"{}" {};'.format(quote(str(v)), self.node_format(v)))

        for e in self.E:
            if directed:
                graph.append('"{}" -> "{}" {};'.format(quote(str(e[0])), quote(str(e[1])), self.edge_format(e)))
            else:
                graph.append('"{}" -- "{}" {};'.format(quote(str(e[0])), quote(str(e[1])), self.edge_format(e)))

        graph.append('}')

        return '\n'.join(graph)


class Animation():
    """
    animation

    对于node和edge:
    - add
    - remove
    - label
    - unlabel
    - high light
    """

    def __init__(self, directed=True):
        self._actions = []
        self.directed = directed

    @classmethod
    def from_dict(cls, g: Dict, color=None, directed=True):
        """
        init from a dict using `color`
        """
        a = Animation(directed=directed)
        for u, adj in g.items():
            for v in adj:
                a.add_edge(u, v)
                if color:
                    a.highlight_edge(u, v, color=color)
        return a

    def next_step(self, clean=False):
        self._actions.append(action.NextStep(clean))

    def add_node(self, v):
        """
        add node of `v` to self._actions
        """
        self._actions.append(action.AddNode(v))

    def highlight_node(self, v, color='red'):
        """
        highlight node `v` using `color`
        """
        self._actions.append(action.HighlightNode(v, color=color))

    def label_node(self, v, label):
        """
        label node `v` using `label`
        """
        self._actions.append(action.LabelNode(v, label))

    def unlabel_node(self, v):
        """
        unlabel of node `v`
        """
        self._actions.append(action.UnlabelNode(v))

    def remove_node(self, v):
        """
        remove node `v`
        """
        self._actions.append(action.RemoveNode(v))

    def add_edge(self, u, v):
        """
        add edge  (`u`, `v`)
        """
        self._actions.append(action.AddEdge(u, v))

    def highlight_edge(self, u, v, color='red'):
        """
        hightlight edge (`u`, `v`) using `color`
        """
        self._actions.append(action.HighlightEdge(u, v, color=color))

    def label_edge(self, u, v, label):
        """
        label edge (`u`, `v`)
        """
        self._actions.append(action.LabelEdge(u, v, label))

    def unlabel_edge(self, u, v):
        """
        unlabel edge (`u`, `v`)
        """
        self._actions.append(action.UnlabelEdge(u, v))

    def remove_edge(self, u, v):
        """
        remove edge `u` and `v`
        """
        self._actions.append(action.RemoveEdge(u, v))

    def parse(self, lines):
        """
        parse of lines
        """
        action2method = {
            'ns': self.next_step,
            'an': self.add_node,
            'hn': self.highlight_node,
            'ln': self.label_node,
            'un': self.unlabel_node,
            'rn': self.remove_node,
            'ae': self.add_edge,
            'he': self.highlight_edge,
            'le': self.label_edge,
            'ue': self.unlabel_edge,
            're': self.remove_edge,
        }
        for line in lines:
            parts = shlex.split(line.strip(), True)
            if not parts:
                continue
            _action, params = parts[0], parts[1:]
            try:
                action2method[_action](*params)
            except KeyError:
                raise ParseException('unrecognized command: {}'.format(action))
            except TypeError:
                raise ParseException('wrong number of parameters: {}'.format(line.strip()))

    def steps(self):
        """
        ?
        """
        steps = [Step()]
        for _action in self._actions:
            _action(steps)
        return steps

    def graphs(self) -> List[str]:
        """
        return dot string
        """
        steps = self.steps()
        V, E = set(), set()
        for step in steps:
            V |= step.V         # 顶点
            E |= step.E         # 边

        graphs = []
        for s in steps:
            graphs.append(s.graph(directed=self.directed))
        return graphs

    def render(self, base_name="undefined", fmt="png", dpi=500, output_gif=True, delay=50):
        """
        render to a png/gif images
        """
        def _generate_static_image(params):
            path, fmt, size, graph = params
            with open(path, 'w') as out:
                pipe = subprocess.Popen(['dot',  '-Gsize=1,1!', '-Gdpi={}'.format(size), '-T', fmt], stdout=out, stdin=subprocess.PIPE, stderr=None)
                pipe.communicate(input=graph.encode())
            return path

        def _generate_gif(files, basename):
            """
            generate gif from files
            """
            for file in files:
                subprocess.call(['mogrify', '-gravity', 'center', '-background', 'white', '-extent', str(dpi), file])
            cmd = ['convert']
            for file in files:
                cmd.extend(('-delay', str(delay), file))
            cmd.append(basename + '.gif')
            subprocess.call(cmd)

        with mp.ProcessPool(nodes=os.cpu_count()) as pool:
            files = pool.map(_generate_static_image, [('{}_{:03}.{}'.format(base_name, n, fmt), fmt, dpi, graph) for n, graph in enumerate(self.graphs())])

        if output_gif:
            _generate_gif(files, base_name)
