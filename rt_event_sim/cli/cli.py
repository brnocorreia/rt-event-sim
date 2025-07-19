import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..models import Task
from ..schedulers import create_scheduler
from ..simulation import Simulator

app = typer.Typer(
    name="rt-event-sim",
    help="Real-time Event Simulator with EDF and RM scheduling algorithms",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def run(
    config_file: str = typer.Argument(
        ..., help="Path to JSON configuration file with tasks and simulation parameters"
    ),
    algorithm: str = typer.Option(
        "edf", "--algorithm", "-a", help="Scheduling algorithm to use: 'edf' or 'rm'"
    ),
    horizon: Optional[int] = typer.Option(
        None, "--horizon", "-h", help="Simulation horizon (overrides config file)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output showing detailed execution trace",
    ),
    timeline: bool = typer.Option(
        False, "--timeline", "-t", help="Show execution timeline"
    ),
    preemptive: bool = typer.Option(
        True,
        "--preemptive/--non-preemptive",
        help="Enable/disable preemptive scheduling (default: preemptive)",
    ),
):
    try:
        config = _load_config(config_file)
        tasks = _parse_tasks(config["tasks"])
        sim_horizon = horizon if horizon is not None else config.get("horizon", 100)

        scheduler = create_scheduler(algorithm)
        simulator = Simulator(tasks, scheduler, verbose=verbose)

        mode = "Preemptive" if preemptive else "Non-preemptive"
        console.print(f"\n[bold blue]Real-time Simulation Starting[/bold blue]")
        console.print(
            f"Algorithm: [green]{scheduler.name}[/green] ([cyan]{mode}[/cyan])"
        )
        console.print(f"Tasks: [yellow]{len(tasks)}[/yellow]")
        console.print(f"Horizon: [yellow]{sim_horizon}[/yellow] time units\n")

        result = simulator.run(sim_horizon, preemptive=preemptive)

        _display_results(result, timeline)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        raise typer.Exit(1)


@app.command()
def compare(
    config_file: str = typer.Argument(..., help="Path to JSON configuration file"),
    horizon: Optional[int] = typer.Option(
        None, "--horizon", "-h", help="Simulation horizon (overrides config file)"
    ),
):
    try:
        config = _load_config(config_file)
        tasks = _parse_tasks(config["tasks"])
        sim_horizon = horizon if horizon is not None else config.get("horizon", 100)

        algorithms = ["edf", "rm"]
        results = []

        console.print(f"\n[bold blue]Comparing Scheduling Algorithms[/bold blue]")
        console.print(f"Tasks: [yellow]{len(tasks)}[/yellow]")
        console.print(f"Horizon: [yellow]{sim_horizon}[/yellow] time units\n")

        for algo in algorithms:
            for preemptive_mode in [True, False]:
                scheduler = create_scheduler(algo)
                simulator = Simulator(tasks, scheduler, verbose=False)
                result = simulator.run(sim_horizon, preemptive=preemptive_mode)
                mode_suffix = (
                    " (Preemptive)" if preemptive_mode else " (Non-preemptive)"
                )
                result.algorithm = result.algorithm + mode_suffix
                results.append(result)

        _display_comparison(results)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        raise typer.Exit(1)


@app.command()
def validate(
    config_file: str = typer.Argument(
        ..., help="Path to JSON configuration file to validate"
    ),
    algorithm: str = typer.Option(
        "edf", "--algorithm", "-a", help="Scheduling algorithm to use: 'edf' or 'rm'"
    ),
):
    try:
        config = _load_config(config_file)
        tasks = _parse_tasks(config["tasks"])

        console.print(f"\n[bold green]Configuration Valid![/bold green]")
        console.print(f"Found {len(tasks)} tasks:")

        table = Table()
        table.add_column("Task", style="cyan")
        table.add_column("WCET", style="yellow")
        table.add_column("Period", style="green")
        table.add_column("Deadline", style="red")
        table.add_column("Utilization", style="magenta")

        scheduler = create_scheduler(algorithm)
        simulator = Simulator(tasks, scheduler, verbose=False)

        console.print(
            f"Checking if Scheduler {scheduler.name} can scale for the given tasks..."
        )

        is_scalable, message = scheduler.is_scalable(tasks)
        if is_scalable:
            console.print(
                "[bold green]✓ Scheduler can scale for the given tasks[/bold green]"
            )
            console.print(f"[bold green]✓ {message}[/bold green]")
        else:
            console.print(
                "[bold red]⚠ Scheduler cannot scale for the given tasks[/bold red]"
            )
            console.print(f"[bold red]⚠ {message}[/bold red]")
            raise typer.Exit(1)

        total_utilization = 0.0
        for task in tasks:
            utilization = task.wcet / task.period
            total_utilization += utilization
            table.add_row(
                task.name,
                str(task.wcet),
                str(task.period),
                str(task.deadline),
                f"{utilization:.3f}",
            )

        console.print(table)
        console.print(f"\nTotal Utilization: [bold]{total_utilization:.3f}[/bold]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", file=sys.stderr)
        raise typer.Exit(1)


def _load_config(config_file: str) -> dict:
    test_dir = Path(__file__).parent.parent / "test"
    config_path = test_dir / config_file
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        return json.load(f)


def _parse_tasks(task_configs: List[dict]) -> List[Task]:
    tasks = []
    for task_config in task_configs:
        try:
            task = Task(**task_config)
            tasks.append(task)
        except Exception as e:
            raise ValueError(f"Invalid task configuration {task_config}: {e}")
    return tasks


def _display_results(result, show_timeline: bool = False):
    table = Table(title="Simulation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Algorithm", result.algorithm)
    table.add_row("Total Time", str(result.total_time))
    table.add_row("Completed Jobs", str(result.completed_jobs))
    table.add_row("Missed Deadlines", str(result.missed_deadlines))
    table.add_row("Success Rate", f"{result.success_rate:.1f}%")
    table.add_row("Total Lateness", str(result.total_lateness))

    console.print(table)

    if result.task_stats:
        task_table = Table(title="Per-Task Statistics")
        task_table.add_column("Task", style="cyan")
        task_table.add_column("Completed", style="green")
        task_table.add_column("Missed", style="red")
        task_table.add_column("Total Lateness", style="yellow")

        for task_name, stats in result.task_stats.items():
            task_table.add_row(
                task_name,
                str(stats["completed"]),
                str(stats["missed"]),
                str(stats["total_lateness"]),
            )

        console.print(task_table)

    if show_timeline and result.timeline:
        _display_timeline(result.timeline)


def _display_timeline(timeline):
    console.print("\n[bold]Execution Timeline:[/bold]")
    for time, task_name in timeline[:50]:
        status = task_name if task_name else "IDLE"
        console.print(f"Time {time:3d}: {status}")

    if len(timeline) > 50:
        console.print(f"... (showing first 50 of {len(timeline)} time units)")


def _display_comparison(results):
    table = Table(title="Algorithm Comparison")
    table.add_column("Algorithm", style="cyan")
    table.add_column("Success Rate", style="green")
    table.add_column("Missed Deadlines", style="red")
    table.add_column("Total Lateness", style="yellow")

    for result in results:
        table.add_row(
            result.algorithm,
            f"{result.success_rate:.1f}%",
            str(result.missed_deadlines),
            str(result.total_lateness),
        )

    console.print(table)


if __name__ == "__main__":
    app()
