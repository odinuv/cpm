#!/usr/bin/env python3
"""
Script to merge nodes and dependencies JSON files and compute the critical path.
"""

import json
import os
import glob
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Any

class CriticalPathCalculator:
    def __init__(self):
        self.nodes = {}
        self.dependencies = []
        self.graph = defaultdict(list)  # adjacency list for forward edges
        self.reverse_graph = defaultdict(list)  # adjacency list for backward edges
        
    def load_files(self, directory: str):
        """Load all nodes*.json and dependencies*.json files from the directory."""
        print(f"Loading files from {directory}...")
        
        # Load nodes
        nodes_files = glob.glob(os.path.join(directory, "nodes*.json"))
        for file_path in nodes_files:
            print(f"Loading nodes from {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                nodes_data = json.load(f)
                for node in nodes_data:
                    self.nodes[node['id']] = node
        
        # Load dependencies
        deps_files = glob.glob(os.path.join(directory, "dependencies*.json"))
        for file_path in deps_files:
            print(f"Loading dependencies from {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                deps_data = json.load(f)
                self.dependencies.extend(deps_data)
        
        print(f"Loaded {len(self.nodes)} nodes and {len(self.dependencies)} dependencies")
    
    def build_graph(self):
        """Build adjacency lists for the dependency graph."""
        self.graph.clear()
        self.reverse_graph.clear()
        
        for dep in self.dependencies:
            source = dep['source']
            target = dep['target']
            
            # Only process if both nodes exist
            if source in self.nodes and target in self.nodes:
                self.graph[source].append(target)
                self.reverse_graph[target].append(source)
    
    def get_priority_weight(self, priority: str) -> int:
        """Convert priority to numeric weight (higher number = higher priority)."""
        priority_map = {
            'Highest': 5,
            'High': 4,
            'Medium': 3,
            'Low': 2,
            'Lowest': 1
        }
        return priority_map.get(priority, 1)
    
    def get_status_weight(self, status: str) -> float:
        """Convert status to effort multiplier."""
        status_map = {
            'Done': 0,
            'In Progress': 0.5,
            'To Do': 1.0,
            'On hold': 1.5  # On hold tasks might take longer
        }
        return status_map.get(status, 1.0)
    
    def calculate_node_duration(self, node_id: str) -> float:
        """Calculate estimated duration for a node based on priority and status."""
        node = self.nodes[node_id]
        priority_weight = self.get_priority_weight(node.get('priority', 'Low'))
        status_weight = self.get_status_weight(node.get('status', 'To Do'))
        
        # Base duration is influenced by priority (higher priority = longer duration assumption)
        # and current status
        base_duration = priority_weight * status_weight
        return max(base_duration, 0.1)  # Minimum duration of 0.1
    
    def topological_sort(self) -> List[str]:
        """Perform topological sort to find processing order."""
        in_degree = defaultdict(int)
        
        # Initialize in-degrees
        for node_id in self.nodes:
            in_degree[node_id] = 0
        
        # Calculate in-degrees
        for source in self.graph:
            for target in self.graph[source]:
                in_degree[target] += 1
        
        # Start with nodes that have no dependencies
        queue = deque([node_id for node_id in self.nodes if in_degree[node_id] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Process all targets of current node
            for target in self.graph[current]:
                in_degree[target] -= 1
                if in_degree[target] == 0:
                    queue.append(target)
        
        # Check for cycles
        if len(result) != len(self.nodes):
            print("Warning: Cycle detected in dependency graph!")
            # Return all nodes anyway for partial processing
            missing_nodes = set(self.nodes.keys()) - set(result)
            result.extend(missing_nodes)
        
        return result
    
    def calculate_critical_path(self):
        """Calculate the critical path using forward and backward pass."""
        print("Calculating critical path...")
        
        # Build the graph
        self.build_graph()
        
        # Get topological order
        topo_order = self.topological_sort()
        
        # Initialize earliest start/finish times
        earliest_start = {}
        earliest_finish = {}
        
        # Forward pass - calculate earliest start and finish times
        for node_id in topo_order:
            duration = self.calculate_node_duration(node_id)
            
            # Earliest start is the maximum earliest finish of all predecessors
            max_predecessor_finish = 0
            for pred in self.reverse_graph.get(node_id, []):
                if pred in earliest_finish:
                    max_predecessor_finish = max(max_predecessor_finish, earliest_finish[pred])
            
            earliest_start[node_id] = max_predecessor_finish
            earliest_finish[node_id] = earliest_start[node_id] + duration
        
        # Find project completion time (maximum earliest finish time)
        if earliest_finish:
            project_completion = max(earliest_finish.values())
        else:
            project_completion = 0
        
        # Initialize latest start/finish times
        latest_start = {}
        latest_finish = {}
        
        # Set latest finish for end nodes (nodes with no successors)
        end_nodes = [node_id for node_id in self.nodes if not self.graph.get(node_id, [])]
        for node_id in end_nodes:
            latest_finish[node_id] = project_completion
        
        # Backward pass - calculate latest start and finish times
        for node_id in reversed(topo_order):
            duration = self.calculate_node_duration(node_id)
            
            if node_id not in latest_finish:
                # Latest finish is the minimum latest start of all successors
                min_successor_start = project_completion
                for succ in self.graph.get(node_id, []):
                    if succ in latest_start:
                        min_successor_start = min(min_successor_start, latest_start[succ])
                latest_finish[node_id] = min_successor_start
            
            latest_start[node_id] = latest_finish[node_id] - duration
        
        # Calculate slack (float) for each node
        slack = {}
        for node_id in self.nodes:
            slack[node_id] = latest_start.get(node_id, 0) - earliest_start.get(node_id, 0)
        
        # Nodes on critical path have zero or near-zero slack
        critical_nodes = set()
        for node_id, slack_value in slack.items():
            if abs(slack_value) < 0.001:  # Account for floating point precision
                critical_nodes.add(node_id)
        
        print(f"Found {len(critical_nodes)} nodes on critical path")
        
        # Update nodes with critical path information
        for node_id in self.nodes:
            self.nodes[node_id]['onCriticalPath'] = node_id in critical_nodes
        
        # Update dependencies with path type
        for dep in self.dependencies:
            source = dep['source']
            target = dep['target']
            
            # A dependency is critical if both source and target are on critical path
            if (source in critical_nodes and target in critical_nodes and 
                source in self.nodes and target in self.nodes):
                dep['pathType'] = 'critical'
            else:
                dep['pathType'] = 'parallel'
        
        return critical_nodes, slack
    
    def save_results(self, output_dir: str):
        """Save the merged and processed nodes and dependencies."""
        nodes_output = os.path.join(output_dir, 'nodes.json')
        deps_output = os.path.join(output_dir, 'dependencies.json')
        
        # Convert nodes dict to list for output
        nodes_list = list(self.nodes.values())
        
        print(f"Saving {len(nodes_list)} nodes to {nodes_output}")
        with open(nodes_output, 'w', encoding='utf-8') as f:
            json.dump(nodes_list, f, indent=2, ensure_ascii=False)
        
        print(f"Saving {len(self.dependencies)} dependencies to {deps_output}")
        with open(deps_output, 'w', encoding='utf-8') as f:
            json.dump(self.dependencies, f, indent=2, ensure_ascii=False)
    
    def print_statistics(self, critical_nodes: Set[str], slack: Dict[str, float]):
        """Print statistics about the critical path analysis."""
        print("\n=== Critical Path Analysis Results ===")
        print(f"Total nodes: {len(self.nodes)}")
        print(f"Total dependencies: {len(self.dependencies)}")
        print(f"Critical path nodes: {len(critical_nodes)}")
        
        if critical_nodes:
            print("\nNodes on critical path:")
            for node_id in sorted(critical_nodes):
                node = self.nodes[node_id]
                print(f"  {node_id}: {node.get('title', 'No title')} "
                      f"[{node.get('status', 'Unknown')}] "
                      f"[{node.get('priority', 'Unknown')}]")
        
        # Show dependencies by type
        critical_deps = [dep for dep in self.dependencies if dep.get('pathType') == 'critical']
        parallel_deps = [dep for dep in self.dependencies if dep.get('pathType') == 'parallel']
        
        print(f"\nCritical path dependencies: {len(critical_deps)}")
        print(f"Parallel dependencies: {len(parallel_deps)}")
        
        if slack:
            print(f"\nNode with most slack: {max(slack.items(), key=lambda x: x[1])}")
            print(f"Node with least slack: {min(slack.items(), key=lambda x: x[1])}")

def main():
    calculator = CriticalPathCalculator()
    
    # Directory containing the input files
    input_dir = "D:\\claude"
    
    try:
        # Load all input files
        calculator.load_files(input_dir)
        
        if not calculator.nodes:
            print("Error: No nodes loaded. Check if files exist and are valid JSON.")
            return
        
        # Calculate critical path
        critical_nodes, slack = calculator.calculate_critical_path()
        
        # Save results
        calculator.save_results(input_dir)
        
        # Print statistics
        calculator.print_statistics(critical_nodes, slack)
        
        print("\n✅ Script completed successfully!")
        print(f"Output files saved: nodes.json and dependencies.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
