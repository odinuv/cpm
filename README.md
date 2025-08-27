# CPM (Critical Path Method) Experiment

**This repository is fully generated.**

This repository contains a Python-based implementation for calculating and visualizing the critical path in project dependencies using the Critical Path Method (CPM).

## Overview

The Critical Path Method is a project management technique used to identify the longest sequence of dependent tasks that determines the minimum project duration. This experiment processes project nodes (tasks) and their dependencies to:

- Calculate the critical path through the project
- Identify which tasks are critical to project completion
- Visualize the dependency graph with interactive web interface
- Mark dependencies as either critical or parallel

## Files Structure

### Core Scripts
- `critical_path_script.py` - Basic CPM calculator with task duration of 1 unit each
- `critical_path_script_2.py` - Advanced CPM calculator with weighted durations based on priority and status

### Data Files
- `nodes.json` - Project tasks/nodes with metadata (title, status, priority, assignee)
- `dependencies.json` - Task dependencies defining the project structure

### Visualization
- `dependency_graph.html` - Interactive web-based dependency graph visualization using D3.js and Dagre
- `run.cmd` - Simple HTTP server launcher for viewing the visualization

## Usage

### Running CPM Analysis

**Basic calculator:**
```bash
python critical_path_script.py
```

**Advanced calculator with weighted durations:**
```bash
python critical_path_script_2.py
```

Both scripts will:
1. Load all `nodes*.json` and `dependencies*.json` files
2. Calculate the critical path
3. Update the data files with critical path information
4. Output analysis results to the console

### Viewing Visualization

To serve the interactive dependency graph:

```bash
python -m http.server 8000
```

Then open your browser to `http://localhost:8000/dependency_graph.html`

## Features

- **Automatic file discovery** - Processes all matching JSON files in the directory
- **Critical path calculation** - Uses topological sorting and longest path algorithms
- **Weighted durations** - Advanced script considers task priority and status
- **Interactive visualization** - Web-based graph with D3.js
- **Data validation** - Creates placeholder nodes for missing references
- **Multiple output formats** - Updates source files with analysis results

## Requirements

- Python 3.x
