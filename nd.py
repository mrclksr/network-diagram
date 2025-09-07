#!/usr/bin/env python3
import csv
import argparse
import networkx as nx
import matplotlib.pyplot as plt

from typing import List


class DiagramError(Exception):
    """Exception raised for problems with the diagram definition.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Node:
    def __init__(self, name: str, duration: int):
        self.id = 0
        self.name = name
        self.duration = duration
        self.prev_nodes = None
        self.next_nodes = None
        self.free_float = 0
        self.total_float = 0
        self.early_start_time = 0
        self.early_finish_time = 0
        self.late_start_time = 0
        self.late_finish_time = 0
        self.level = 0

    def add_prev_node(self, node):
        if not self.prev_nodes:
            self.prev_nodes = []
        self.prev_nodes.append(node)

    def add_next_node(self, node):
        if not self.next_nodes:
            self.next_nodes = []
        self.next_nodes.append(node)

    def set_id(self, id: int):
        self.id = id


class Plan:
    def __init__(self):
        self.nodes: List[Node] = []
        self.critical_path_nodes: List[Node] = []
        self.node_id = 0
        self.nodes_per_level = {}
        self.level_nodes = {}
        self.max_node_level = 0

    def add_node(self, name: str, duration: int, preceding_node_names: List[str]):
        if name in preceding_node_names:
            raise DiagramError(f'Node "{name}" is its own predecessor.')
        node = self.find_node(name)
        if node:
            raise DiagramError(f'Node "{name}" already defined.')
        if duration <= 0:
            raise DiagramError(f'Duration of node {name} <= 0.')
        node = self._create_node(name, duration, preceding_node_names)
        self.nodes.append(node)
        return node

    def find_node(self, name: str):
        for known_node in self.nodes:
            if known_node.name == name:
                return known_node
        return None

    def _create_node(self, name: str, duration: int, preceding_node_names: List[str]):
        node = Node(name, duration)
        for pnn in preceding_node_names:
            pn = self.find_node(pnn)
            if pn:
                node.add_prev_node(pn)
            pn.add_next_node(node)
        self.node_id += 1
        node.set_id(self.node_id)
        return node

    def calculate_forward_from_node(self, node):
        node.early_finish_time = node.early_start_time + node.duration
        node.early_start_time = 0

        if node.prev_nodes:
            max_early_finish_time = 0
            for parent in node.prev_nodes:
                parent.early_finish_time = parent.early_start_time + parent.duration
                if parent.early_finish_time > max_early_finish_time:
                    max_early_finish_time = parent.early_finish_time
            node.early_start_time = max_early_finish_time
            node.early_finish_time = node.early_start_time + node.duration
        if node.next_nodes:
            for child in node.next_nodes:
                self.calculate_forward_from_node(child)

    def calculate_forward(self):
        for node in self.nodes:
            self.calculate_forward_from_node(node)

    def calculate_backward(self):
        for node in reversed(self.nodes):
            self.calculate_backward_from_node(node)

    def calculate_backward_from_node(self, node: Node):
        node.late_finish_time = node.early_finish_time
        node.late_start_time = node.early_finish_time - node.duration

        if node.next_nodes:
            min_late_start_time = node.next_nodes[0].late_start_time
            for child in node.next_nodes:
                if min_late_start_time > child.late_start_time:
                    min_late_start_time = child.late_start_time
            node.late_finish_time = min_late_start_time
            node.late_start_time = node.late_finish_time - node.duration

    def get_min_early_start_time(self, nodes):
        if not nodes:
            return 0
        min_start = nodes[0].early_start_time
        for node in nodes:
            if min_start > node.early_start_time:
                min_start = node.early_start_time
        return min_start

    def calculate_buffers(self):
        for node in self.nodes:
            node.total_float = node.late_start_time - node.early_start_time
            if not node.next_nodes:
                node.free_float = 0
            else:
                node.free_float = self.get_min_early_start_time(
                    node.next_nodes) - node.early_finish_time

    def calculate_node_levels(self):
        # Find all starting nodes. That is, nodes without parents.
        for node in self.nodes:
            if node.prev_nodes:
                continue
            node.level = 0
            self.calculate_child_node_levels(node, 1)

    def calculate_child_node_levels(self, parent: Node, level: int) -> int:
        if not parent.next_nodes:
            return level
        for node in parent.next_nodes:
            if node.level < level:
                node.level = level
            if self.max_node_level < node.level:
                self.max_node_level = node.level
            self.calculate_child_node_levels(node, level + 1)

    def collect_level_nodes(self):
        for node in self.nodes:
            list = self.level_nodes.get(node.level, [])
            list.append(node)
            self.level_nodes[node.level] = list
            self.nodes_per_level[node.level] = self.nodes_per_level.get(
                node.level, 0) + 1

    def collect_critical_path_nodes(self):
        self.critical_path_nodes = []
        for node in self.nodes:
            if node.total_float == 0:
                self.critical_path_nodes.append(node)
        self.critical_path_nodes.sort(key=lambda node: node.level)

    def get_level_nodes(self, level: int) -> List[Node]:
        return self.level_nodes[level]

    def get_nodes_per_level(self, level: int):
        return self.nodes_per_level.get(level, 0)

    def get_critical_path(self):
        return self.critical_path_nodes

    def get_level(self):
        return self.max_node_level

    def build(self):
        self.calculate_forward()
        self.calculate_backward()
        self.calculate_buffers()
        self.calculate_node_levels()
        self.collect_level_nodes()
        self.collect_critical_path_nodes()


def create_label_from_node(node: Node):
    return (
        f'{node.early_start_time:>2} {node.early_finish_time:>5}\n{node.name:^}\n'
        f'{node.duration:>2} {node.total_float:>2} {node.free_float:>2}\n'
        f'{node.late_start_time:>2} {node.late_finish_time:>5}'
    )


def draw_diagram(plan: Plan):
    G = nx.DiGraph()
    for level in range(0, plan.get_level()):
        for node in plan.get_level_nodes(level):
            parent_node_label = create_label_from_node(node)
            G.add_node(parent_node_label, layer=node.level)
            if not node.next_nodes:
                continue
            for child in node.next_nodes:
                if node.total_float == 0 and child.total_float == 0:
                    color = 'red'
                else:
                    color = 'black'
                child_node_label = create_label_from_node(child)
                G.add_node(child_node_label, layer=child.level)
                G.add_edge(parent_node_label, child_node_label, color=color)
    pos = nx.multipartite_layout(G, subset_key='layer')
    colors = nx.get_edge_attributes(G, 'color').values()
    nx.draw(G, with_labels=True, font_family='monospace', pos=pos,
            node_size=3500, node_color='skyblue', edge_color=colors, node_shape='s')
    plt.show()


def parse_table_row(row: List):
    if len(row) != 3:
        raise RuntimeError('Table rows must have 3 columns')
    if not row[2]:
        return row[0], int(row[1]), []
    return row[0], int(row[1]), row[2].split(',')


def create_plan_from_table(csv_reader) -> Plan:
    plan = Plan()
    for row in csv_reader:
        name, duration, predecessors = parse_table_row(row)
        plan.add_node(name, duration, predecessors)
    plan.build()
    return plan


def main():
    delimiter = ' '
    arg_parser = argparse.ArgumentParser(
        description='A simple program for calculating and displaying network diagrams for project management',
    )
    arg_parser.add_argument('filename', type=str)
    arg_parser.add_argument('-d', '--delimiter', type=str,
                            help='Field delimiter of given CSV file')
    args = arg_parser.parse_args()
    if args.delimiter:
        delimiter = args.delimiter
    with open(args.filename, 'r') as f:
        reader = csv.reader(f, delimiter=delimiter)
        plan = create_plan_from_table(reader)
        draw_diagram(plan)


if __name__ == '__main__':
    main()
