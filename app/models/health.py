from datetime import datetime
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: datetime
    version: str 