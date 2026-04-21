from dataclasses import dataclass
from datetime import datetime


# This model is represent the logical insight topic, which is the result of a pipeline run.
@dataclass
class InsightTopic:
    id: str
    topic: str
    created_at: datetime
