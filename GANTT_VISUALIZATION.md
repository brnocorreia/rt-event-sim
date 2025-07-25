# Gantt Chart Visualization

The rt-event-sim now supports generating beautiful Gantt charts to visualize the execution sequence of real-time tasks. This provides an intuitive way to understand scheduling behavior, identify missed deadlines, and compare different algorithms.

## Features

- **Task execution timeline**: Shows which task executes at each time unit
- **Release markers**: Green dotted lines showing when tasks are released
- **Deadline markers**: Red dashed lines showing task deadlines
- **CPU idle periods**: Gray blocks indicating when no task is executing
- **Algorithm statistics**: Success rate, missed deadlines, and completion counts
- **Color-coded tasks**: Each task has a unique color for easy identification
- **Comparison mode**: Side-by-side comparison of different scheduling algorithms

## Usage

### 1. Integrated with `run` command

Generate a Gantt chart while running a simulation:

```bash
rt-event-sim run example_config.json --plot
```

#### Options:

- `--plot, -p`: Enable Gantt chart generation
- `--plot-output FILE`: Specify output filename (default: gantt_chart.png)
- `--deadlines/--no-deadlines`: Show/hide deadline markers (default: show)
- `--releases/--no-releases`: Show/hide release markers (default: show)

#### Examples:

```bash
rt-event-sim run example_config.json --plot --plot-output my_chart.png

rt-event-sim run example_config.json --algorithm rm --plot --no-deadlines

rt-event-sim run example_config.json --plot --horizon 30 --non-preemptive
```

### 2. Dedicated `plot` command

Generate charts without detailed simulation output:

```bash
rt-event-sim plot example_config.json
```

#### Options:

- `--algorithm, -a`: Choose EDF or RM (default: edf)
- `--output, -o`: Output filename (default: gantt_chart.png)
- `--compare, -c`: Compare EDF vs RM algorithms
- `--horizon, -h`: Override simulation time horizon
- `--preemptive/--non-preemptive`: Scheduling mode
- `--deadlines/--no-deadlines`: Show/hide deadline markers
- `--releases/--no-releases`: Show/hide release markers

#### Examples:

```bash
rt-event-sim plot example_config.json --compare --output comparison.png

rt-event-sim plot challenging_config.json --algorithm rm --output rm_chart.png

rt-event-sim plot example_config.json --horizon 100 --no-releases
```

## Interpreting the Charts

### Visual Elements

1. **Colored blocks**: Task execution periods

   - Each task has a unique color
   - Block height represents the task
   - Block width represents execution duration

2. **Green dotted lines**: Task release times

   - Vertical lines showing when jobs are released
   - Limited to the corresponding task's row

3. **Red dashed lines**: Task deadlines

   - Vertical lines showing deadline points
   - Limited to the corresponding task's row

4. **Gray blocks**: CPU idle periods

   - Shown in the bottom "CPU IDLE" row
   - Indicates no task is executing

5. **Statistics box**: Shows algorithm performance
   - Success rate percentage
   - Number of completed jobs
   - Number of missed deadlines
   - Total lateness

### Example Scenarios

#### Successful Scheduling

```
T1: ███░░███░░███░░███░░███
T2: ░░██████░░░░██████░░░░██
T3: ░░░░░░░███████░░░░░░░███
IDLE: ░█░░░░░░░░█░░░░░░░░░░█
```

#### With Missed Deadlines

The chart will show tasks executing past their deadline markers, helping identify scheduling issues.

## Configuration Files

Use JSON configuration files to define tasks:

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

## Output Files

Charts are saved as high-resolution PNG files (300 DPI) suitable for:

- Research papers and presentations
- System documentation
- Educational materials
- Performance analysis reports

The generated files can be easily integrated into documents or shared for collaborative analysis.
