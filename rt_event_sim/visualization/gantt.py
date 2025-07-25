import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict, Tuple, Optional
from ..simulation.simulator import SimulationResult
from ..models.models import Task


def plot_gantt_chart(
    result: SimulationResult,
    tasks: List[Task],
    show_deadlines: bool = True,
    show_releases: bool = True,
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (15, 8),
    title: Optional[str] = None,
    show_interactive: bool = True,
) -> None:
    task_names = [task.name for task in tasks]
    task_colors = _generate_task_colors(task_names)

    fig, ax = plt.subplots(figsize=figsize)

    _plot_execution_timeline(ax, result.timeline, task_names, task_colors)

    if show_deadlines:
        _plot_deadlines(ax, tasks, result.total_time)

    if show_releases:
        _plot_releases(ax, tasks, result.total_time)

    _format_gantt_chart(ax, task_names, result, title)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Gantt chart saved to: {save_path}")

    if show_interactive:
        plt.show()
    else:
        plt.close(fig)


def _generate_task_colors(task_names: List[str]) -> Dict[str, str]:
    colors = [
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
        "#96CEB4",
        "#FFEAA7",
        "#DDA0DD",
        "#98D8C8",
        "#F7DC6F",
        "#BB8FCE",
        "#85C1E9",
    ]

    task_colors = {}
    for i, task_name in enumerate(task_names):
        task_colors[task_name] = colors[i % len(colors)]

    task_colors[None] = "#E8E8E8"

    return task_colors


def _plot_execution_timeline(
    ax,
    timeline: List[Tuple[int, Optional[str]]],
    task_names: List[str],
    task_colors: Dict[str, str],
) -> None:
    current_task = None
    start_time = 0

    for time, task_name in timeline:
        if task_name != current_task:
            if current_task is not None:
                _draw_execution_block(
                    ax,
                    current_task,
                    start_time,
                    time - start_time,
                    task_names,
                    task_colors,
                )
            current_task = task_name
            start_time = time

    if current_task is not None:
        _draw_execution_block(
            ax,
            current_task,
            start_time,
            len(timeline) - start_time,
            task_names,
            task_colors,
        )


def _draw_execution_block(
    ax,
    task_name: Optional[str],
    start_time: int,
    duration: int,
    task_names: List[str],
    task_colors: Dict[str, str],
) -> None:
    if task_name is None:
        y_pos = len(task_names)
        label = "IDLE"
        color = task_colors[None]
        alpha = 0.3
    else:
        try:
            y_pos = task_names.index(task_name)
            label = task_name
            color = task_colors[task_name]
            alpha = 0.8
        except ValueError:
            return

    rect = patches.Rectangle(
        (start_time, y_pos + 0.1),
        duration,
        0.8,
        linewidth=1,
        edgecolor="black",
        facecolor=color,
        alpha=alpha,
    )
    ax.add_patch(rect)

    if duration > 1:
        ax.text(
            start_time + duration / 2,
            y_pos + 0.5,
            label,
            ha="center",
            va="center",
            fontweight="bold",
            fontsize=9,
        )


def _plot_deadlines(ax, tasks: List[Task], total_time: int) -> None:
    for i, task in enumerate(tasks):
        deadline_times = []
        time = task.deadline
        while time <= total_time:
            deadline_times.append(time)
            time += task.period

        for deadline_time in deadline_times:
            ax.axvline(
                x=deadline_time,
                ymin=(i + 0.05) / (len(tasks) + 1),
                ymax=(i + 0.95) / (len(tasks) + 1),
                color="red",
                linestyle="--",
                linewidth=2,
                alpha=0.7,
            )


def _plot_releases(ax, tasks: List[Task], total_time: int) -> None:
    for i, task in enumerate(tasks):
        release_times = []
        time = 0
        while time <= total_time:
            release_times.append(time)
            time += task.period

        for release_time in release_times:
            ax.axvline(
                x=release_time,
                ymin=(i + 0.05) / (len(tasks) + 1),
                ymax=(i + 0.95) / (len(tasks) + 1),
                color="green",
                linestyle=":",
                linewidth=1.5,
                alpha=0.6,
            )


def _format_gantt_chart(
    ax, task_names: List[str], result: SimulationResult, title: Optional[str]
) -> None:
    task_labels = task_names + ["CPU IDLE"]
    y_positions = list(range(len(task_labels)))

    ax.set_yticks(y_positions)
    ax.set_yticklabels(task_labels)
    ax.set_xlabel("Time Units", fontsize=12, fontweight="bold")
    ax.set_ylabel("Tasks", fontsize=12, fontweight="bold")

    if title:
        chart_title = title
    else:
        chart_title = f"Gantt Chart - {result.algorithm} Scheduling"

    ax.set_title(chart_title, fontsize=14, fontweight="bold", pad=20)

    ax.set_xlim(0, result.total_time)
    ax.set_ylim(-0.5, len(task_labels) - 0.5)

    ax.grid(True, axis="x", alpha=0.3, linestyle="-", linewidth=0.5)
    ax.set_axisbelow(True)

    _add_legend(ax, task_names)
    _add_statistics_text(ax, result)


def _add_legend(ax, task_names: List[str]) -> None:
    legend_elements = []

    task_colors = _generate_task_colors(task_names)

    for task_name in task_names:
        legend_elements.append(
            patches.Patch(color=task_colors[task_name], label=f"Task {task_name}")
        )

    legend_elements.append(
        patches.Patch(color=task_colors[None], alpha=0.3, label="CPU Idle")
    )

    legend_elements.extend(
        [
            plt.Line2D(
                [0], [0], color="red", linestyle="--", linewidth=2, label="Deadlines"
            ),
            plt.Line2D(
                [0], [0], color="green", linestyle=":", linewidth=1.5, label="Releases"
            ),
        ]
    )

    ax.legend(handles=legend_elements, loc="upper right", bbox_to_anchor=(1.15, 1))


def _add_statistics_text(ax, result: SimulationResult) -> None:
    stats_text = (
        f"Algorithm: {result.algorithm}\n"
        f"Success Rate: {result.success_rate:.1f}%\n"
        f"Completed Jobs: {result.completed_jobs}\n"
        f"Missed Deadlines: {result.missed_deadlines}\n"
        f"Total Lateness: {result.total_lateness}"
    )

    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor="lightgray", alpha=0.8),
        fontsize=10,
        fontfamily="monospace",
    )


def plot_comparison_gantt(
    results: List[SimulationResult],
    tasks: List[Task],
    save_path: Optional[str] = None,
    figsize: Tuple[int, int] = (20, 12),
    show_interactive: bool = True,
) -> None:
    if not results:
        print("No results to plot")
        return

    num_algorithms = len(results)
    fig, axes = plt.subplots(num_algorithms, 1, figsize=figsize, sharex=True)

    if num_algorithms == 1:
        axes = [axes]

    task_names = [task.name for task in tasks]

    for i, (result, ax) in enumerate(zip(results, axes)):
        task_colors = _generate_task_colors(task_names)

        _plot_execution_timeline(ax, result.timeline, task_names, task_colors)

        _plot_deadlines(ax, tasks, result.total_time)
        _plot_releases(ax, tasks, result.total_time)

        task_labels = task_names + ["CPU IDLE"]
        y_positions = list(range(len(task_labels)))

        ax.set_yticks(y_positions)
        ax.set_yticklabels(task_labels)
        ax.set_ylabel("Tasks", fontsize=10, fontweight="bold")

        title = f"{result.algorithm} - Success Rate: {result.success_rate:.1f}%"
        ax.set_title(title, fontsize=12, fontweight="bold")

        ax.set_xlim(0, result.total_time)
        ax.set_ylim(-0.5, len(task_labels) - 0.5)
        ax.grid(True, axis="x", alpha=0.3)

        if i == 0:
            _add_legend(ax, task_names)

    axes[-1].set_xlabel("Time Units", fontsize=12, fontweight="bold")

    plt.suptitle("Scheduling Algorithm Comparison", fontsize=16, fontweight="bold")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Comparison chart saved to: {save_path}")

    if show_interactive:
        plt.show()
    else:
        plt.close(fig)
