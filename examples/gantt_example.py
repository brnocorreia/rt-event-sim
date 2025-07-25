#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rt_event_sim.models import Task
from rt_event_sim.schedulers import EDFScheduler, RMScheduler
from rt_event_sim.simulation import Simulator
from rt_event_sim.visualization import plot_gantt_chart, plot_comparison_gantt


def create_example_tasks():
    return [
        Task(name="T1", wcet=1, period=4, deadline=4),
        Task(name="T2", wcet=2, period=5, deadline=5),
        Task(name="T3", wcet=1, period=10, deadline=10),
    ]


def run_single_algorithm_example():
    print("=== Single Algorithm Gantt Chart Example ===")

    tasks = create_example_tasks()
    scheduler = EDFScheduler()
    simulator = Simulator(tasks, scheduler, verbose=False)

    result = simulator.run(horizon=50, preemptive=True)

    print(f"Algorithm: {result.algorithm}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Missed Deadlines: {result.missed_deadlines}")

    plot_gantt_chart(
        result=result,
        tasks=tasks,
        show_deadlines=True,
        show_releases=True,
        title="EDF Scheduling Example",
        save_path="edf_gantt.png",
    )


def run_algorithm_comparison_example():
    print("\n=== Algorithm Comparison Example ===")

    tasks = create_example_tasks()
    horizon = 50

    schedulers = [("EDF", EDFScheduler()), ("RM", RMScheduler())]

    results = []

    for name, scheduler in schedulers:
        simulator = Simulator(tasks, scheduler, verbose=False)
        result = simulator.run(horizon=horizon, preemptive=True)
        results.append(result)

        print(
            f"{name}: Success Rate {result.success_rate:.1f}%, "
            f"Missed Deadlines: {result.missed_deadlines}"
        )

    plot_comparison_gantt(
        results=results, tasks=tasks, save_path="comparison_gantt.png"
    )


def run_challenging_scenario():
    print("\n=== Challenging Scenario Example ===")

    challenging_tasks = [
        Task(name="T1", wcet=3, period=10, deadline=8),
        Task(name="T2", wcet=2, period=8, deadline=6),
        Task(name="T3", wcet=4, period=15, deadline=12),
        Task(name="T4", wcet=1, period=5, deadline=4),
    ]

    scheduler = EDFScheduler()
    simulator = Simulator(challenging_tasks, scheduler, verbose=False)

    result = simulator.run(horizon=60, preemptive=True)

    print(f"Challenging scenario - Success Rate: {result.success_rate:.1f}%")

    plot_gantt_chart(
        result=result,
        tasks=challenging_tasks,
        title="Challenging Scenario - EDF Scheduling",
        figsize=(18, 10),
        save_path="challenging_gantt.png",
    )


def main():
    print("Real-Time Event Simulator - Gantt Chart Examples")
    print("=" * 50)

    run_single_algorithm_example()

    run_algorithm_comparison_example()

    run_challenging_scenario()

    print("\n=== All examples completed! ===")
    print("Generated files:")
    print("- edf_gantt.png")
    print("- comparison_gantt.png")
    print("- challenging_gantt.png")


if __name__ == "__main__":
    main()
