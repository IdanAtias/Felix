from pydantic import BaseModel
from enum import Enum


class Project(BaseModel):
    id: str
    name: str


class InstanceState(str, Enum):
    provisioning = "PROVISIONING"
    staging = "STAGING"
    running = "RUNNING"
    stopping = "STOPPING"
    terminated = "TERMINATED"
    suspending = "SUSPENDING"
    suspended = "SUSPENDED"


class Instance(BaseModel):
    id: str
    name: str
    zone: str
    project: str
    state: InstanceState

