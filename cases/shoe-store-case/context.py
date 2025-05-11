from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserContext:
    user_id: str
    session_start: datetime = datetime.now()