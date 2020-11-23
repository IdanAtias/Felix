from pydantic import BaseModel
from enum import Enum


class GcpResource(BaseModel):
    id: str
    name: str
    zone: str
    project: str


class Project(GcpResource):
    zone: str = None
    project: str = None


class InstanceState(str, Enum):
    provisioning = "PROVISIONING"
    staging = "STAGING"
    running = "RUNNING"
    stopping = "STOPPING"
    terminated = "TERMINATED"
    suspending = "SUSPENDING"
    suspended = "SUSPENDED"


class Instance(GcpResource):
    state: InstanceState

