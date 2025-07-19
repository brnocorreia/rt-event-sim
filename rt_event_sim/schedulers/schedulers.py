import heapq
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from rich.console import Console

from rt_event_sim.models.models import Task
from rt_event_sim.schedulers.constants import (
    EDF_NON_SCALABILITY_MESSAGE,
    EDF_SCALABILITY_MESSAGE,
    RM_LL_SCALABILITY_MESSAGE,
    RM_RTA_NON_SCALABILITY_MESSAGE,
    RM_RTA_SCALABILITY_MESSAGE,
)
from ..models import Job

console = Console()

class Scheduler(ABC):
    def __init__(self):
        self.ready_queue: List[Tuple[int, int, Job]] = []
        self.counter = 0

    def add_job(self, job: Job) -> None:
        priority = self._get_priority(job)
        heapq.heappush(self.ready_queue, (priority, self.counter, job))
        self.counter += 1

    def get_next_job(self) -> Optional[Job]:
        if not self.ready_queue:
            return None
        _, _, job = heapq.heappop(self.ready_queue)
        return job

    def has_jobs(self) -> bool:
        return len(self.ready_queue) > 0

    def clear(self) -> None:
        self.ready_queue.clear()
        self.counter = 0

    @abstractmethod
    def _get_priority(self, job: Job) -> int:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_scalable(self, tasks: List[Task], console: Console = None) -> Tuple[bool, str]:
        """
        Check if the scheduler is scalable for the given tasks.
        """
        pass


class EDFScheduler(Scheduler):
    def _get_priority(self, job: Job) -> int:
        return job.absolute_deadline

    @property
    def name(self) -> str:
        return "Earliest Deadline First (EDF)"

    def is_scalable(self, tasks: List[Task], console: Console = None) -> Tuple[bool, str]:
        """
        Check if the scheduler is scalable for the given tasks.

        If, for the given tasks, the sum of the utilization of all tasks is less than or equal to 1,
        then the scheduler is scalable. If not, the set of tasks is not scalable.
        """
        total_utilization = sum(task.wcet / task.period for task in tasks)
        is_scalable = total_utilization <= 1.0
        return (
            is_scalable,
            EDF_SCALABILITY_MESSAGE if is_scalable else EDF_NON_SCALABILITY_MESSAGE,
        )


class RMScheduler(Scheduler):
    def _get_priority(self, job: Job) -> int:
        return job.task.period

    @property
    def name(self) -> str:
        return "Rate Monotonic (RM)"

    def is_scalable(self, tasks: List[Task], console: Console = None) -> Tuple[bool, str]:
        """
        Check if the scheduler is scalable for the given tasks.

        It uses the Liu and Layland utilization bound to check if the scheduler is scalable.
        If its not possible to define using this bound, it fallbacks to RTA algorithm.
        """
        if not tasks:
            return True

        n = len(tasks)
        utilization_bound = n * (2 ** (1 / n) - 1)
        total_utilization = sum(task.wcet / task.period for task in tasks)

        if total_utilization <= utilization_bound:
            return True, RM_LL_SCALABILITY_MESSAGE

        sorted_tasks = sorted(tasks, key=lambda task: task.period)

        for i, task in enumerate(sorted_tasks):
            higher_priority_tasks = sorted_tasks[:i]

            initial_response_time = task.wcet + sum(
                hp_task.wcet for hp_task in higher_priority_tasks
            )

            response_time = initial_response_time

            while True:
                new_response_time = task.wcet + sum(
                    ((response_time + hp_task.period - 1) // hp_task.period)
                    * hp_task.wcet
                    for hp_task in higher_priority_tasks
                )

                if new_response_time > task.deadline:
                    console.print(f"[bold red]⚠ New response time {new_response_time} is greater than the deadline {task.deadline}[/bold red]")
                    return False, RM_RTA_NON_SCALABILITY_MESSAGE

                if new_response_time == response_time:
                    console.print(f"[bold green]✓ Response time {response_time} is equal to the new response time {new_response_time}[/bold green]")
                    break

                response_time = new_response_time

            if response_time > task.deadline:
                console.print(f"[bold red]⚠ Response time {response_time} is greater than the deadline {task.deadline}[/bold red]")
                return False, RM_RTA_NON_SCALABILITY_MESSAGE

        return True, RM_RTA_SCALABILITY_MESSAGE


def create_scheduler(algorithm: str) -> Scheduler:
    algorithm = algorithm.lower().strip()
    if algorithm in ["edf", "earliest-deadline-first"]:
        return EDFScheduler()
    elif algorithm in ["rm", "rate-monotonic"]:
        return RMScheduler()
    else:
        raise ValueError(f"Unknown scheduling algorithm: {algorithm}")
