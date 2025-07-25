from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import heapq
from enum import Enum
from ..models import Task, Job
from ..schedulers import Scheduler


class EventType(Enum):
    JOB_RELEASE = "job_release"
    JOB_COMPLETION = "job_completion"


@dataclass
class Event:
    time: int
    event_type: EventType
    task: Optional[Task] = None
    job: Optional[Job] = None

    def __lt__(self, other):
        if self.time != other.time:
            return self.time < other.time
        return self.event_type.value < other.event_type.value


@dataclass
class SimulationResult:
    algorithm: str
    total_time: int
    completed_jobs: int
    missed_deadlines: int
    total_lateness: int
    task_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    timeline: List[Tuple[int, Optional[str]]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.completed_jobs == 0:
            return 0.0
        return (self.completed_jobs - self.missed_deadlines) / self.completed_jobs * 100


class Simulator:
    def __init__(self, tasks: List[Task], scheduler: Scheduler, verbose: bool = False):
        self.tasks = tasks
        self.scheduler = scheduler
        self.verbose = verbose
        self.current_time = 0
        self.job_counter = 0
        self.completed_jobs = 0
        self.missed_deadlines = 0
        self.total_lateness = 0
        self.task_stats: Dict[str, Dict[str, int]] = {}
        self.timeline: List[Tuple[int, Optional[str]]] = []

        for task in tasks:
            self.task_stats[task.name] = {
                "completed": 0,
                "missed": 0,
                "total_lateness": 0,
            }

    def run(self, horizon: int, preemptive: bool = True) -> SimulationResult:
        self._reset()

        if self.verbose:
            mode = "preemptive" if preemptive else "non-preemptive"
            print(f"Starting {mode} simulation with {self.scheduler.name}")
            print(f"Tasks: {[t.name for t in self.tasks]}")
            print(f"Horizon: {horizon} time units")
            print("-" * 50)

        current_job: Optional[Job] = None

        for time in range(horizon):
            self.current_time = time

            self._release_jobs()

            if current_job and current_job.is_finished:
                self._complete_job(current_job)
                current_job = None

            if preemptive and current_job and self.scheduler.has_jobs():
                next_job = self.scheduler.get_next_job()
                if next_job and self._should_preempt(current_job, next_job):
                    if self.verbose:
                        print(
                            f"Time {time}: Preempting {current_job.task.name} with {next_job.task.name}"
                        )
                    self.scheduler.add_job(current_job)
                    current_job = next_job
                else:
                    if next_job:
                        self.scheduler.add_job(next_job)

            if not current_job:
                current_job = self.scheduler.get_next_job()

            if current_job:
                current_job.remaining -= 1
                task_name = current_job.task.name
                if self.verbose:
                    print(
                        f"Time {time}: Executing {task_name} (remaining: {current_job.remaining})"
                    )
            else:
                task_name = None
                if self.verbose:
                    print(f"Time {time}: CPU idle")

            self.timeline.append((time, task_name))

        # TODO: Remove this as its not guaranteed that all jobs are completed
        if current_job and not current_job.is_finished:
            self._complete_job(current_job)

        result = SimulationResult(
            algorithm=self.scheduler.name,
            total_time=horizon,
            completed_jobs=self.completed_jobs,
            missed_deadlines=self.missed_deadlines,
            total_lateness=self.total_lateness,
            task_stats=self.task_stats.copy(),
            timeline=self.timeline.copy(),
        )

        if self.verbose:
            self._print_summary(result)

        return result

    def run_event_driven(
        self, horizon: int, preemptive: bool = True
    ) -> SimulationResult:
        self._reset()

        if self.verbose:
            mode = "preemptive" if preemptive else "non-preemptive"
            print(f"Starting event-driven {mode} simulation with {self.scheduler.name}")
            print(f"Tasks: {[t.name for t in self.tasks]}")
            print(f"Horizon: {horizon} time units")
            print("-" * 50)

        event_queue = []
        current_job: Optional[Job] = None
        last_time = 0

        for task in self.tasks:
            release_event = Event(time=0, event_type=EventType.JOB_RELEASE, task=task)
            heapq.heappush(event_queue, release_event)

        while event_queue and event_queue[0].time < horizon:
            event = heapq.heappop(event_queue)
            current_time = event.time

            if current_job and last_time < current_time:
                execution_time = current_time - last_time
                current_job.remaining -= execution_time

                if self.verbose:
                    print(
                        f"Time {last_time}-{current_time}: Executing {current_job.task.name} "
                        f"for {execution_time} units (remaining: {current_job.remaining})"
                    )

                for t in range(last_time, current_time):
                    self.timeline.append((t, current_job.task.name))
            elif last_time < current_time:
                if self.verbose:
                    print(f"Time {last_time}-{current_time}: CPU idle")
                for t in range(last_time, current_time):
                    self.timeline.append((t, None))

            self.current_time = current_time

            if event.event_type == EventType.JOB_RELEASE:
                self._handle_job_release_event(event, event_queue, horizon)

                if preemptive and current_job and self.scheduler.has_jobs():
                    next_job = self.scheduler.get_next_job()
                    if next_job and self._should_preempt(current_job, next_job):
                        if self.verbose:
                            print(
                                f"Time {current_time}: Preempting {current_job.task.name} with {next_job.task.name}"
                            )
                        self._remove_completion_events(current_job, event_queue)
                        self.scheduler.add_job(current_job)
                        current_job = next_job
                        self._schedule_completion_event(
                            current_job, event_queue, current_time
                        )
                    else:
                        if next_job:
                            self.scheduler.add_job(next_job)
                elif not current_job and self.scheduler.has_jobs():
                    current_job = self.scheduler.get_next_job()
                    if current_job:
                        self._schedule_completion_event(
                            current_job, event_queue, current_time
                        )

            elif event.event_type == EventType.JOB_COMPLETION:
                if (
                    current_job
                    and current_job == event.job
                    and current_job.remaining <= 0
                ):
                    # if self.verbose:
                    # print(f"Time {current_time}: Job {current_job.job_id} of task {current_job.task.name} completed")
                    self._complete_job(current_job)
                    current_job = None

                    if self.scheduler.has_jobs():
                        current_job = self.scheduler.get_next_job()
                        if current_job:
                            self._schedule_completion_event(
                                current_job, event_queue, current_time
                            )

            last_time = current_time

        if current_job and last_time < horizon:
            execution_time = horizon - last_time
            current_job.remaining -= execution_time

            for t in range(last_time, horizon):
                self.timeline.append((t, current_job.task.name))

            if current_job.remaining <= 0:
                self._complete_job(current_job)
        elif last_time < horizon:
            for t in range(last_time, horizon):
                self.timeline.append((t, None))

        result = SimulationResult(
            algorithm=self.scheduler.name,
            total_time=horizon,
            completed_jobs=self.completed_jobs,
            missed_deadlines=self.missed_deadlines,
            total_lateness=self.total_lateness,
            task_stats=self.task_stats.copy(),
            timeline=self.timeline.copy(),
        )

        if self.verbose:
            self._print_summary(result)

        return result

    def _handle_job_release_event(
        self, event: Event, event_queue: List[Event], horizon: int
    ):
        task = event.task
        job = Job(
            task=task,
            release_time=self.current_time,
            remaining=task.wcet,
            absolute_deadline=self.current_time + task.deadline,
            job_id=self.job_counter,
        )
        self.job_counter += 1
        self.scheduler.add_job(job)

        if self.verbose:
            print(
                f"Time {self.current_time}: Released job {job.job_id} of task {task.name} "
                f"(deadline: {job.absolute_deadline})"
            )

        next_release_time = self.current_time + task.period
        if next_release_time < horizon:
            next_release_event = Event(
                time=next_release_time, event_type=EventType.JOB_RELEASE, task=task
            )
            heapq.heappush(event_queue, next_release_event)

    def _schedule_completion_event(
        self, job: Job, event_queue: List[Event], current_time: int
    ):
        completion_time = current_time + job.remaining
        completion_event = Event(
            time=completion_time, event_type=EventType.JOB_COMPLETION, job=job
        )
        heapq.heappush(event_queue, completion_event)

    def _remove_completion_events(self, job: Job, event_queue: List[Event]):
        event_queue[:] = [
            event
            for event in event_queue
            if not (event.event_type == EventType.JOB_COMPLETION and event.job == job)
        ]
        heapq.heapify(event_queue)

    def _reset(self):
        self.current_time = 0
        self.job_counter = 0
        self.completed_jobs = 0
        self.missed_deadlines = 0
        self.total_lateness = 0
        self.timeline.clear()
        self.scheduler.clear()

        for task_name in self.task_stats:
            self.task_stats[task_name] = {
                "completed": 0,
                "missed": 0,
                "total_lateness": 0,
            }

    def _release_jobs(self):
        for task in self.tasks:
            if self.current_time % task.period == 0:
                job = Job(
                    task=task,
                    release_time=self.current_time,
                    remaining=task.wcet,
                    absolute_deadline=self.current_time + task.deadline,
                    job_id=self.job_counter,
                )
                self.job_counter += 1
                self.scheduler.add_job(job)

                if self.verbose:
                    print(
                        f"Time {self.current_time}: Released job {job.job_id} of task {task.name} "
                        f"(deadline: {job.absolute_deadline})"
                    )

    def _complete_job(self, job: Job):
        completion_time = self.current_time
        lateness = max(0, completion_time - job.absolute_deadline)

        self.completed_jobs += 1
        self.task_stats[job.task.name]["completed"] += 1

        if lateness > 0:
            self.missed_deadlines += 1
            self.total_lateness += lateness
            self.task_stats[job.task.name]["missed"] += 1
            self.task_stats[job.task.name]["total_lateness"] += lateness

            if self.verbose:
                print(
                    f"Time {completion_time}: Job {job.job_id} of task {job.task.name} "
                    f"completed with lateness {lateness}"
                )
        else:
            if self.verbose:
                print(
                    f"Time {completion_time}: Job {job.job_id} of task {job.task.name} "
                    f"completed on time"
                )

    def _should_preempt(self, current_job: Job, new_job: Job) -> bool:
        current_priority = self.scheduler._get_priority(current_job)
        new_priority = self.scheduler._get_priority(new_job)
        return new_priority < current_priority

    def _print_summary(self, result: SimulationResult):
        print("\n" + "=" * 50)
        print("SIMULATION SUMMARY")
        print("=" * 50)
        print(f"Algorithm: {result.algorithm}")
        print(f"Total simulation time: {result.total_time}")
        print(f"Completed jobs: {result.completed_jobs}")
        print(f"Missed deadlines: {result.missed_deadlines}")
        print(f"Success rate: {result.success_rate:.1f}%")
        print(f"Total lateness: {result.total_lateness}")

        print("\nPer-task statistics:")
        for task_name, stats in result.task_stats.items():
            print(
                f"  {task_name}: {stats['completed']} completed, "
                f"{stats['missed']} missed, lateness {stats['total_lateness']}"
            )
        print("=" * 50)
