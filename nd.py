#!/usr/bin/env python3
from typing import List

class Node:
    def __init__(self, name: str, duration: int):
        self.id = 0
        self.name = name
        self.duration = duration
        self.prev_nodes = None
        self.next_nodes = None
        self.free_buffer = 0
        self.total_buffer = 0
        self.earliest_start = 0
        self.earliest_end = 0
        self.latest_start = 0
        self.latest_end = 0

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
        self.node_id = 0
        self.root = None

    def add_node(self, name: str, duration: int, preceding_node_names: List[str]):
        node = self.find_node(name)
        if node:
            return None
        node = self._create_node(name, duration, preceding_node_names)
        if not self.root:
            self.root = node
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
        node.earliest_end = node.earliest_start + node.duration
        node.earliest_start = 0

        if node.prev_nodes:
            max_earliest_end = 0
            for parent in node.prev_nodes:
                parent.earliest_end = parent.earliest_start + parent.duration
                if parent.earliest_end > max_earliest_end:
                    max_earliest_end = parent.earliest_end
            node.earliest_start = max_earliest_end
            node.earliest_end = node.earliest_start + node.duration 
            self.sort_nodes(node.prev_nodes)
        if node.next_nodes:
            for child in node.next_nodes:
                child.earliest_start = node.earliest_end
                self.calculate_forward_from_node(child)
            self.sort_nodes(node.next_nodes)

    def calculate_forward(self):
        for node in self.nodes:
            self.calculate_forward_from_node(node)
        self.sort_nodes(self.nodes)

    def sort_nodes(self, nodes):
        nodes.sort(key=lambda node: node.earliest_start)

    def calculate_backward(self):
        for node in reversed(self.nodes):
            self.calculate_backward_from_node(node)

    def calculate_backward_from_node(self, node: Node):
        node.latest_end = node.earliest_end
        node.latest_start = node.earliest_end - node.duration

        if node.next_nodes:
            min_latest_start = node.next_nodes[0].latest_start
            for child in node.next_nodes:
                if min_latest_start > child.latest_start:
                    min_latest_start = child.latest_start
            node.latest_end = min_latest_start
            node.latest_start = node.latest_end - node.duration

    def get_min_earliest_start(self, nodes):
        if not nodes:
            return 0
        min_start = nodes[0].earliest_start
        for node in nodes:
            if min_start > node.earliest_start:
                min_start = node.earliest_start
        return min_start

    def calculate_buffers(self):
        for node in self.nodes:
            node.total_buffer = node.latest_start - node.earliest_start
            if not node.next_nodes:
                node.free_buffer = 0
            else:
                node.free_buffer = self.get_min_earliest_start(node.next_nodes) - node.earliest_end


def detect_cycle(node: Node):
    pass

def display_node(node: Node):
    print(f'{node.name}|{node.duration}|{node.earliest_start}|{node.earliest_end}::{node.latest_start}|{node.latest_end} == gp: {node.total_buffer}| fp: {node.free_buffer}|')
    if not node.next_nodes:
        return
    for child in node.next_nodes:
        print(f'{child.name}|{child.duration}|{child.earliest_start}|{child.earliest_end}::{child.latest_start}|{child.latest_end}|== gp: {child.total_buffer}| fp: {child.free_buffer}')
        display_node(child)

def create_diagram(plan: Plan):
    display_node(plan.root)

def create_node(name: str, duration: int):
    pass

def parse_table_row(line: str):
    fields = line.split()
    if not fields or len(fields) < 2:
        return None
    if len(fields) >= 3:
        return fields[0], int(fields[1]), fields[2].split(',')
    return fields[0], int(fields[1]), []

def create_plan_from_table(file) -> Plan:
    plan = Plan()
    for line in file:
        name, duration, predecessors = parse_table_row(line.strip())
        plan.add_node(name, duration, predecessors)
    return plan

def main():
    with open('plan.txt', 'r') as f:
        plan = create_plan_from_table(f)
        plan.calculate_forward()
        plan.calculate_backward()
        plan.calculate_buffers()
        create_diagram(plan)

if __name__ == '__main__':
    main()