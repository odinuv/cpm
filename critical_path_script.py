import json
import os
import glob
from collections import defaultdict, deque

def load_json_files(pattern):
    """Load and merge all JSON files matching the pattern"""
    files = glob.glob(pattern)
    merged_data = []
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    merged_data.append(data)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading {file_path}: {e}")
    
    return merged_data

def build_graph(dependencies):
    """Build adjacency lists for the dependency graph"""
    graph = defaultdict(list)  # node -> list of dependent nodes
    reverse_graph = defaultdict(list)  # node -> list of prerequisite nodes
    in_degree = defaultdict(int)
    out_degree = defaultdict(int)
    all_nodes = set()
    
    for dep in dependencies:
        source = dep['source']
        target = dep['target']
        
        graph[source].append(target)
        reverse_graph[target].append(source)
        out_degree[source] += 1
        in_degree[target] += 1
        
        all_nodes.add(source)
        all_nodes.add(target)
    
    # Ensure all nodes have entries
    for node in all_nodes:
        if node not in in_degree:
            in_degree[node] = 0
        if node not in out_degree:
            out_degree[node] = 0
    
    return graph, reverse_graph, in_degree, out_degree, all_nodes

def topological_sort(graph, in_degree):
    """Perform topological sort to get valid ordering"""
    queue = deque([node for node, degree in in_degree.items() if degree == 0])
    topo_order = []
    temp_in_degree = in_degree.copy()
    
    while queue:
        node = queue.popleft()
        topo_order.append(node)
        
        for neighbor in graph[node]:
            temp_in_degree[neighbor] -= 1
            if temp_in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return topo_order

def calculate_critical_path(graph, reverse_graph, in_degree, out_degree, all_nodes):
    """Calculate the critical path using longest path algorithm"""
    
    # Step 1: Calculate earliest start times (forward pass)
    earliest_start = {}
    topo_order = topological_sort(graph, in_degree)
    
    # Initialize start nodes (no dependencies)
    for node in all_nodes:
        if in_degree[node] == 0:
            earliest_start[node] = 0
    
    # Calculate earliest start for all nodes
    for node in topo_order:
        if node not in earliest_start:
            earliest_start[node] = 0
        
        for dependent in graph[node]:
            # Assuming each task takes 1 unit of time
            new_start = earliest_start[node] + 1
            if dependent not in earliest_start or new_start > earliest_start[dependent]:
                earliest_start[dependent] = new_start
    
    # Step 2: Calculate latest start times (backward pass)
    latest_start = {}
    
    # Initialize end nodes (no dependents)
    max_time = max(earliest_start.values()) if earliest_start else 0
    for node in all_nodes:
        if out_degree[node] == 0:
            latest_start[node] = earliest_start.get(node, 0)
    
    # Calculate latest start for all nodes (reverse topological order)
    for node in reversed(topo_order):
        if node not in latest_start:
            if out_degree[node] == 0:
                latest_start[node] = earliest_start.get(node, 0)
            else:
                # Find minimum latest start of all dependents
                min_dependent_latest = float('inf')
                for dependent in graph[node]:
                    if dependent in latest_start:
                        min_dependent_latest = min(min_dependent_latest, latest_start[dependent] - 1)
                
                if min_dependent_latest != float('inf'):
                    latest_start[node] = min_dependent_latest
                else:
                    latest_start[node] = earliest_start.get(node, 0)
    
    # Step 3: Identify critical nodes (slack = 0)
    critical_nodes = set()
    for node in all_nodes:
        earliest = earliest_start.get(node, 0)
        latest = latest_start.get(node, 0)
        if earliest == latest:
            critical_nodes.add(node)
    
    return critical_nodes, earliest_start, latest_start

def create_missing_nodes(nodes, dependencies):
    """Create placeholder nodes for any node IDs referenced in dependencies but missing from nodes"""
    existing_node_ids = {node['id'] for node in nodes}
    referenced_node_ids = set()
    
    # Collect all node IDs referenced in dependencies
    for dep in dependencies:
        referenced_node_ids.add(dep['source'])
        referenced_node_ids.add(dep['target'])
    
    # Find missing node IDs
    missing_node_ids = referenced_node_ids - existing_node_ids
    
    if missing_node_ids:
        print(f"Creating placeholder nodes for missing IDs: {sorted(missing_node_ids)}")
        
        # Create placeholder nodes
        for node_id in missing_node_ids:
            placeholder_node = {
                "id": node_id,
                "title": f"Placeholder for {node_id}",
                "status": "Unknown",
                "assignee": "Unassigned",
                "priority": "medium",
                "epicName": "Unknown Epic",
                "onCriticalPath": False
            }
            nodes.append(placeholder_node)
    
    return nodes

def update_nodes_and_dependencies(nodes, dependencies, critical_nodes):
    """Update nodes and dependencies with critical path information"""
    
    # First, create any missing nodes
    nodes = create_missing_nodes(nodes, dependencies)
    
    # Update nodes
    node_lookup = {node['id']: node for node in nodes}
    for node in nodes:
        node['onCriticalPath'] = node['id'] in critical_nodes
    
    # Build critical path edges
    critical_edges = set()
    graph = defaultdict(list)
    
    for dep in dependencies:
        graph[dep['source']].append(dep['target'])
    
    # An edge is critical if both nodes are critical and connected
    for dep in dependencies:
        source = dep['source']
        target = dep['target']
        
        if source in critical_nodes and target in critical_nodes:
            critical_edges.add((source, target))
    
    # Update dependencies
    for dep in dependencies:
        source = dep['source']
        target = dep['target']
        
        if (source, target) in critical_edges:
            dep['pathType'] = 'critical'
        else:
            dep['pathType'] = 'parallel'
    
    return nodes, dependencies

def main():
    # Set the working directory
    os.chdir(r'D:\\claude\\')
    
    print("Loading nodes files...")
    nodes = load_json_files('nodes*.json')
    print(f"Loaded {len(nodes)} nodes")
    
    print("Loading dependencies files...")
    dependencies = load_json_files('dependencies*.json')
    print(f"Loaded {len(dependencies)} dependencies")
    
    if not dependencies:
        print("No dependencies found. All nodes will be marked as not on critical path.")
        for node in nodes:
            node['onCriticalPath'] = False
    else:
        print("Building dependency graph...")
        graph, reverse_graph, in_degree, out_degree, all_nodes = build_graph(dependencies)
        
        print("Calculating critical path...")
        critical_nodes, earliest_start, latest_start = calculate_critical_path(
            graph, reverse_graph, in_degree, out_degree, all_nodes
        )
        
        print(f"Found {len(critical_nodes)} critical nodes: {sorted(critical_nodes)}")
        
        print("Updating nodes and dependencies...")
        nodes, dependencies = update_nodes_and_dependencies(nodes, dependencies, critical_nodes)
    
    # Save results
    print("Saving results...")
    
    # Save nodes
    with open('nodes.json', 'w', encoding='utf-8') as f:
        json.dump(nodes, f, indent=2, ensure_ascii=False)
    
    # Save dependencies
    with open('dependencies.json', 'w', encoding='utf-8') as f:
        json.dump(dependencies, f, indent=2, ensure_ascii=False)
    
    print("✅ Critical path analysis complete!")
    print(f"📁 Saved {len(nodes)} nodes to nodes.json")
    print(f"🔗 Saved {len(dependencies)} dependencies to dependencies.json")
    
    # Print summary
    if dependencies:
        critical_count = sum(1 for node in nodes if node.get('onCriticalPath', False))
        critical_deps = sum(1 for dep in dependencies if dep.get('pathType') == 'critical')
        parallel_deps = sum(1 for dep in dependencies if dep.get('pathType') == 'parallel')
        
        print(f"\n📊 Summary:")
        print(f"   Critical nodes: {critical_count}/{len(nodes)}")
        print(f"   Critical paths: {critical_deps}")
        print(f"   Parallel paths: {parallel_deps}")

if __name__ == "__main__":
    main()