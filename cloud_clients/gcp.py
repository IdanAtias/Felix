from typing import List, Tuple, Optional
from dataclasses import dataclass
from http_noah.async_client import AsyncHTTPClient

from cloud_models.gcp import Instance, InstanceState


@dataclass
class Instances:
    client: AsyncHTTPClient
    list_all_path: str = "compute/beta/projects/{project}/zones/{zone}/instances"

    async def list_all_running_instances(
            self, project: str, zone: str, next_page_token: str = None
    ) -> Tuple[List[Instance], Optional[str]]:
        """
        list all running instances in project
        next page token is for getting the next page of results
        """
        path = self.list_all_path.format(project=project, zone=zone)
        query_params = {"filter": f"status = {InstanceState.running}"}
        if next_page_token:
            query_params["pageToken"] = next_page_token

        data = await self.client.get(
            path=path,
            query_params=query_params,
            response_type=dict,
        )

        running_instances = []
        for instance_data in data.get("items", []):

            instance_state = instance_data["status"]
            if instance_state != InstanceState.running:
                raise ValueError(f"Got an instance that is not in RUNNING state. instance_state={instance_state}")

            instance = Instance(
                 id=instance_data["id"],
                 name=instance_data["name"],
                 zone=zone,
                 project=project,
                 state=instance_state,
            )
            running_instances.append(instance)

        return running_instances, data.get("nextPageToken")


@dataclass
class Client:
    host: str = "compute.googleapis.com"
    port: int = 443
    scheme: str = "https"
    api_base: str = ""

    def __post_init__(self):
        self.client = AsyncHTTPClient(host=self.host, port=self.port, scheme=self.scheme, api_base=self.api_base)
        self.instances = Instances(self.client)

    def set_auth_token(self, token: object):
        self.client.set_auth_token(str(token))
