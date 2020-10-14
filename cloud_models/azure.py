from typing import Optional
from pydantic import BaseModel
from enum import Enum


class AzureResource(BaseModel):
    id: str
    name: str
    rg: Optional[str]


class Subscription(AzureResource):
    pass


class VmPowerState(str, Enum):
    # https://docs.microsoft.com/en-us/azure/virtual-machines/states-lifecycle
    starting = "starting"
    running = "running"
    stopping = "stopping"
    stopped = "stopped"
    deallocating = "deallocating"
    deallocated = "deallocated"


class Vm(AzureResource):
    power_state: VmPowerState
