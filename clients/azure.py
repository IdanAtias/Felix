from typing import List
from dataclasses import dataclass
from http_noah.async_client import AsyncHTTPClient


@dataclass
class Subscriptions:
    client: AsyncHTTPClient
    path: str = "subscriptions"
    api_version: str = "2020-01-01"

    async def list(self) -> List[str]:
        data = await self.client.get(
            path=self.path,
            query_params={"api-version": self.api_version},
            response_type=dict,
        )
        return [sub["displayName"] for sub in data["value"]]


@dataclass
class Client:
    host: str = "management.azure.com"
    port: int = 443
    subscriptions: Subscriptions = Subscriptions(AsyncHTTPClient(host=host, port=port, scheme="https", api_base=""))

    def set_auth_token(self, token: object):
        self.subscriptions.client.set_auth_token(token=str(token))
