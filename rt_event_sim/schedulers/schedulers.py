import heapq
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from ..models import Job


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


class EDFScheduler(Scheduler):
    def _get_priority(self, job: Job) -> int:
        return job.absolute_deadline
    
    @property
    def name(self) -> str:
        return "Earliest Deadline First (EDF)"


class RMScheduler(Scheduler):
    def _get_priority(self, job: Job) -> int:
        return job.task.period
    
    @property
    def name(self) -> str:
        return "Rate Monotonic (RM)"


def create_scheduler(algorithm: str) -> Scheduler:
    algorithm = algorithm.lower().strip()
    if algorithm in ["edf", "earliest-deadline-first"]:
        return EDFScheduler()
    elif algorithm in ["rm", "rate-monotonic"]:
        return RMScheduler()
    else:
        raise ValueError(f"Unknown scheduling algorithm: {algorithm}") 