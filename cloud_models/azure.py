import structlog
from typing import Optional
from pydantic import BaseModel
from enum import Enum

logger = structlog.get_logger(__name__)


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
    na = "N/A"  # not applicable for cases where power state is not available (for example, when vm provisioning fails)


class Vm(AzureResource):
    power_state: VmPowerState

    @classmethod
    def from_raw_data(cls, data: dict):
        vm_id = data["properties"]["vmId"]
        name = data["name"]
        rg = data["id"].split("/")[4]
        try:
            power_state = data["properties"]["instanceView"]["statuses"][1]["code"].split("/")[1]
        except Exception:
            logger.exception("could not extract power state for vm", vm_id=vm_id, name=name, rg=rg)
            power_state = VmPowerState.na.value

        return cls(id=vm_id, name=name, rg=rg, power_state=power_state)
