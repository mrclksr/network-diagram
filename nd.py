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
        self.general_buffer = 0
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

    def add_node(self, name: str, duration: int, preceeding_node_names: List[str]):
        node = self.find_node(name)
        if node:
            return None
        node = self._create_node(name, duration, preceeding_node_names)
        if not self.root:
            self.root = node
        self.nodes.append(node)
        return node

    def find_node(self, name: str):
        for known_node in self.nodes:
            if known_node.name == name:
                return known_node
        return None

    def _create_node(self, name: str, duration: int, preceeding_node_names: List[str]):
        node = Node(name, duration)
        for pnn in preceeding_node_names:
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
        if node.next_nodes:
            for child in node.next_nodes:
                child.earliest_start = node.earliest_end
                self.calculate_forward_from_node(child)

    def calculate_forward(self):
        for node in self.nodes:
            self.calculate_forward_from_node(node)

    def calculate_backward(self):
        pass

    def calculate_buffers(self):
        pass


def detect_cycle(node: Node):
    pass

def display_node(node: Node):
    print(f'{node.name}|{node.duration}|{node.earliest_start}|{node.earliest_end}|')
    if not node.next_nodes:
        return
    for child in node.next_nodes:
        print(f'{child.name}|{child.duration}|{child.earliest_start}|{child.earliest_end}|')
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
        print(line)
        name, duration, predecessors = parse_table_row(line.strip())
        print(name, duration, predecessors)
        plan.add_node(name, duration, predecessors)
    return plan

def main():
    with open('plan.txt', 'r') as f:
        print("here")
        plan = create_plan_from_table(f)
        plan.calculate_forward()
        create_diagram(plan)

if __name__ == '__main__':
    main()