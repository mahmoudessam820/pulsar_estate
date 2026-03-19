from datetime import datetime
from typing import Optional


class JobStatus:
    def __init__(self):
        self.last_run: Optional[datetime] = None
        self.last_duration: Optional[float] = None
        self.last_error: Optional[str] = None


pipeline_job_status = JobStatus()
