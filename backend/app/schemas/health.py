from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class HealthStatus(BaseModel):
    status: str = Field(default="ok")
    environment: str
    timestamp: str
    version: str = Field(default="1.0.0")

class ReadinessStatus(BaseModel):
    status: str
    environment: str
    database: Dict[str, Any]
    blockchain: Dict[str, Any]
    storage: Optional[Dict[str, Any]] = None
    timestamp: str
