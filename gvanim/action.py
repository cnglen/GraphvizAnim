#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
each class denotes one action:
- NextStep(): 增加一帧
- others: 修改最后一帧
"""


class NextStep():
    """
    insert one frame to steps
    """

    def __init__(self, clean=False):
        self.clean = clean

    def __call__(self, steps):
        """
        steps新增一个元素:
        - 该元素初始化为最后一个元素 (if not self.clean)
        - 该元素初始化为空 (if self.clean)
        """
        from gvanim.animation import Step
        steps.append(Step(None if self.clean else steps[-1]))


class AddNode():
    """
    add a node to last frame
    """

    def __init__(self, v):
        self.v = v

    def __call__(self, steps):
        steps[-1].V.add(self.v)


class HighlightNode():
    """
    highlight node `v` using `color` in last frame
    """

    def __init__(self, v, color='red'):
        self.v = v
        self.color = color

    def __call__(self, steps):
        if self.v not in steps[-1].V:
            steps[-1].V.add(self.v)
        steps[-1].hV[self.v] = self.color


class LabelNode():
    """
    label `v` in last frame
    """

    def __init__(self, v, label):
        self.v = v
        self.label = label

    def __call__(self, steps):
        steps[-1].V.add(self.v)
        steps[-1].lV[self.v] = self.label


class UnlabelNode():
    def __init__(self, v):
        self.v = v

    def __call__(self, steps):
        steps[-1].V.add(self.v)
        try:
            del steps[-1].lV[self.v]
        except KeyError:
            pass


class RemoveNode():
    def __init__(self, v):
        self.v = v

    def __call__(self, steps):
        steps[-1].V.discard(self.v)
        try:
            del steps[-1].hV[self.v]
        except KeyError:
            pass
        try:
            del steps[-1].lV[self.v]
        except KeyError:
            pass
        dE = set(e for e in steps[-1].E if self.v in e)
        steps[-1].E -= dE
        for e in list(steps[-1].hE.keys()):
            if self.v in e:
                del steps[-1].hE[e]


class AddEdge():
    def __init__(self, u, v):
        self.u = u
        self.v = v

    def __call__(self, steps):
        steps[-1].V.add(self.u)
        steps[-1].V.add(self.v)
        steps[-1].E.add((self.u, self.v))


class HighlightEdge():
    def __init__(self, u, v, color='red'):
        self.u = u
        self.v = v
        self.color = color

    def __call__(self, steps):
        steps[-1].V.add(self.u)
        steps[-1].V.add(self.v)
        steps[-1].hV[self.u] = self.color
        steps[-1].hV[self.v] = self.color
        steps[-1].E.add((self.u, self.v))
        steps[-1].hE[(self.u, self.v)] = self.color


class LabelEdge():
    def __init__(self, u, v, label):
        self.u = u
        self.v = v
        self.label_edge = label

    def __call__(self, steps):
        steps[-1].V.add(self.u)
        steps[-1].V.add(self.v)
        steps[-1].E.add((self.u, self.v))
        steps[-1].lE[(self.u, self.v)] = self.label_edge


class UnlabelEdge():
    def __init__(self, u, v):
        self.u = u
        self.v = v

    def __call__(self, steps):
        steps[-1].V.add(self.u)
        steps[-1].V.add(self.v)
        steps[-1].E.add((self.u, self.v))
        try:
            del steps[-1].lE[(self.u, self.v)]
        except KeyError:
            pass


class RemoveEdge():
    def __init__(self, u, v):
        self.u = u
        self.v = v

    def __call__(self, steps):
        steps[-1].E.discard((self.u, self.v))
        try:
            del steps[-1].hE[(self.u, self.v)]
            del steps[-1].lE[(self.u, self.v)]
        except KeyError:
            pass
