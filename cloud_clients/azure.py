import urllib.parse as urlparse
from typing import List, Tuple, Optional, Callable, Dict
from dataclasses import dataclass
from http_noah.async_client import AsyncHTTPClient

from cloud_models.azure import Subscription, Vm, VmPowerState


@dataclass
class Subscriptions:
    client: AsyncHTTPClient
    list_path: str = "subscriptions"
    api_version: str = "2020-01-01"

    async def list(self) -> List[Subscription]:
        data = await self.client.get(
            path=self.list_path,
            query_params={"api-version": self.api_version},
            response_type=dict,
        )
        return [Subscription(id=sub["subscriptionId"], name=sub["displayName"]) for sub in data["value"]]


@dataclass
class Vms:
    client: AsyncHTTPClient
    list_all_path: str = "subscriptions/{subscription_id}/providers/Microsoft.Compute/virtualMachines"
    api_version: str = "2020-06-01"

    async def list_all(
            self, subscription: Subscription, filter_func: Callable[[Vm], bool] = None, next_link: str = None
    ) -> Tuple[List[Vm], Optional[str]]:
        """
        list all VMs in subscriptions
        next link is for getting the next page of results
        filter func for filtering only vms that match filter conditions
        """
        if next_link:
            next_link_parsed = urlparse.urlparse(next_link)
            path = next_link_parsed.path
            parsed_query_params: Dict[str, List] = urlparse.parse_qs(next_link_parsed.query)
            query_params: Dict[str, str] = dict((k, v[0]) for k, v in parsed_query_params.items())  # convert dict style
        else:
            path = self.list_all_path.format(subscription_id=subscription.id)
            query_params = {"api-version": self.api_version, "statusOnly": "true"}

        data = await self.client.get(
            path=path,
            query_params=query_params,
            response_type=dict,
        )

        vms = []
        for vm_data in data["value"]:
            vm = Vm.from_raw_data(data=vm_data)
            if not filter_func or filter_func(vm):
                vms.append(vm)

        return vms, data.get("nextLink")

    async def list_all_running_vms(
            self, subscription: Subscription, next_link: str = None
    ) -> Tuple[List[Vm], Optional[str]]:
        def filter_func(vm: Vm):
            return vm.power_state == VmPowerState.running

        return await self.list_all(subscription=subscription, filter_func=filter_func, next_link=next_link)


@dataclass
class Client:
    host: str = "management.azure.com"
    port: int = 443
    scheme: str = "https"
    api_base: str = ""

    def __post_init__(self):
        self.client = AsyncHTTPClient(host=self.host, port=self.port, scheme=self.scheme, api_base=self.api_base)
        self.subscriptions = Subscriptions(self.client)
        self.vms = Vms(self.client)

    def set_auth_token(self, token: object):
        self.client.set_auth_token(str(token))
