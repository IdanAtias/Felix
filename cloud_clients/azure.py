from typing import List
from dataclasses import dataclass
from http_noah.async_client import AsyncHTTPClient

from cloud_models.azure import Subscription


@dataclass
class Subscriptions:
    client: AsyncHTTPClient
    path: str = "subscriptions"
    api_version: str = "2020-01-01"

    async def list(self) -> List[Subscription]:
        data = await self.client.get(
            path=self.path,
            query_params={"api-version": self.api_version},
            response_type=dict,
        )
        return [Subscription(id=sub["id"], name=sub["displayName"]) for sub in data["value"]]


@dataclass
class Client:
    host: str = "management.azure.com"
    port: int = 443
    scheme: str = "https"
    api_base: str = ""

    def __post_init__(self):
        self.subscriptions = Subscriptions(
            AsyncHTTPClient(host=self.host, port=self.port, scheme=self.scheme, api_base=self.api_base)
        )

    def set_auth_token(self, token: object):
        self.subscriptions.client.set_auth_token(token=str(token))
