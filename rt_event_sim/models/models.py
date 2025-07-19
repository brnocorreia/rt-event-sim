from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    name: str
    wcet: int          
    period: int
    deadline: int      
    
    def __post_init__(self):
        if self.wcet <= 0:
            raise ValueError("WCET must be positive")
        if self.period <= 0:
            raise ValueError("Period must be positive")
        if self.deadline <= 0:
            raise ValueError("Deadline must be positive")
        if self.deadline > self.period:
            raise ValueError("Deadline cannot exceed period")


@dataclass
class Job:
    task: Task
    release_time: int
    remaining: int
    absolute_deadline: int
    job_id: Optional[int] = None
    
    def __post_init__(self):
        if self.remaining <= 0:
            raise ValueError("Remaining execution time must be positive")
        if self.absolute_deadline < self.release_time:
            raise ValueError("Absolute deadline cannot be before release time")
    
    @property
    def is_finished(self) -> bool:
        return self.remaining <= 0
    
    @property
    def priority_rm(self) -> int:
        return self.task.period
    
    @property
    def priority_edf(self) -> int:
        return self.absolute_deadline 