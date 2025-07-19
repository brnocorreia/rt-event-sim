# Real-Time Event Simulator

A discrete-time simulator for real-time scheduling algorithms including Earliest Deadline First (EDF) and Rate Monotonic (RM).

## Features

- **EDF (Earliest Deadline First)** scheduling algorithm
- **RM (Rate Monotonic)** scheduling algorithm  
- CLI interface with rich formatting
- Configuration validation
- Algorithm comparison
- Verbose execution tracing
- Timeline visualization
- Event Driven Time Execution Simulation

## Installation

This project uses `uv` for dependency management:

```bash
uv sync
```

## Usage

### Configuration Files

Configuration files are located in the `rt_event_sim/test/` directory. The following test configurations are available:
- `example_config.json` - Basic example with two tasks
- `challenging_config.json` - More complex scenario
- `preemptive_config.json` - Preemptive scheduling test case
- `tight_deadlines_config.json` - Tasks with tight deadline constraints

### Basic Simulation

Run a simulation with EDF:
```bash
uv run rt-event-sim run example_config.json --algorithm edf
```

Run a simulation with Rate Monotonic:
```bash
uv run rt-event-sim run example_config.json --algorithm rm
```

### Compare Algorithms

Compare both algorithms on the same task set:
```bash
uv run rt-event-sim compare example_config.json
```

### Validate Configuration

Check if a configuration file is valid:
```bash
uv run rt-event-sim validate example_config.json
```

### Verbose Mode

See detailed execution trace:
```bash
uv run rt-event-sim run example_config.json --algorithm edf --verbose --timeline
```

### Running Tests

Test the simulator with different configurations:

```bash
# Test basic functionality
uv run rt-event-sim run example_config.json

# Test challenging scenarios
uv run rt-event-sim run challenging_config.json --verbose

# Test preemptive vs non-preemptive scheduling
uv run rt-event-sim run preemptive_config.json --preemptive
uv run rt-event-sim run preemptive_config.json --non-preemptive

# Test tight deadline scenarios
uv run rt-event-sim run tight_deadlines_config.json --algorithm edf
uv run rt-event-sim run tight_deadlines_config.json --algorithm rm

# Compare all algorithms on a test case
uv run rt-event-sim compare challenging_config.json
```

## Configuration Format

The simulator expects a JSON configuration file with the following format:

```json
{
  "horizon": 50,
  "tasks": [
    {
      "name": "T1",
      "wcet": 1,
      "period": 4,
      "deadline": 4
    },
    {
      "name": "T2", 
      "wcet": 2,
      "period": 5,
      "deadline": 5
    }
  ]
}
```

### Parameters

- `horizon`: Total simulation time
- `wcet`: Worst-case execution time
- `period`: Task period (how often the task is released)
- `deadline`: Relative deadline (must be ≤ period)

## CLI Commands

### `run`

Run a simulation with a specific algorithm.

**Options:**
- `--algorithm, -a`: Choose 'edf' or 'rm' (default: edf)
- `--horizon, -h`: Override simulation horizon
- `--verbose, -v`: Show detailed execution trace
- `--timeline, -t`: Show execution timeline

### `compare`

Compare EDF and RM algorithms on the same task set.

**Options:**
- `--horizon, -h`: Override simulation horizon

### `validate`

Validate a configuration file and show task utilization analysis.

## Examples

```bash
# Validate a configuration file
uv run rt-event-sim validate example_config.json

# Run EDF simulation with timeline
uv run rt-event-sim run example_config.json -a edf --verbose --timeline --horizon 20

# Compare algorithms on a challenging test case
uv run rt-event-sim compare challenging_config.json

# Test preemptive vs non-preemptive with tight deadlines
uv run rt-event-sim run tight_deadlines_config.json --preemptive
uv run rt-event-sim run tight_deadlines_config.json --non-preemptive
```
