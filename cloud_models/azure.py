from pydantic import BaseModel
from enum import Enum


class AzureResource(BaseModel):
    id: str
    name: str


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

    @property
    def rg(self) -> str:
        """
        extract resource group from vm id
        example id:
        /subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.Compute/virtualMachines/<vm-name>"
        """
        return self.id.split("/")[4]
