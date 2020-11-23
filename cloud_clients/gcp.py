from typing import List, Tuple, Optional
from dataclasses import dataclass
from http_noah.async_client import AsyncHTTPClient

from cloud_models.gcp import Instance, InstanceState, Project


@dataclass
class Projects:
    client: AsyncHTTPClient
    list_projects_path: str = "v1/projects"

    async def list(self) -> List[Project]:
        """
        list all available projects
        """
        data = await self.client.get(path=self.list_projects_path, response_type=dict)
        projects = []
        for project_data in data.get("projects", []):
            if project_data["lifecycleState"] != "ACTIVE":
                # skip not active projects
                continue
            projects.append(Project(id=project_data["projectId"], name=project_data["name"]))
        return projects


@dataclass
class Instances:
    client: AsyncHTTPClient
    list_instances_path: str = "compute/beta/projects/{project}/zones/{zone}/instances"

    async def list_running(
            self, project: str, zone: str, next_page_token: str = None
    ) -> Tuple[List[Instance], Optional[str]]:
        """
        list all running instances in project
        next page token is for getting the next page of results
        """
        path = self.list_instances_path.format(project=project, zone=zone)
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
    compute_host: str = "compute.googleapis.com"
    cloud_resource_manager_host: str = "cloudresourcemanager.googleapis.com"
    port: int = 443
    scheme: str = "https"
    api_base: str = ""

    def __post_init__(self):
        self.cloud_resource_manager_client = AsyncHTTPClient(
            host=self.cloud_resource_manager_host, port=self.port, scheme=self.scheme, api_base=self.api_base
        )
        self.compute_client = AsyncHTTPClient(
            host=self.compute_host, port=self.port, scheme=self.scheme, api_base=self.api_base
        )
        self.projects = Projects(self.cloud_resource_manager_client)
        self.instances = Instances(self.compute_client)

    def set_auth_token(self, token: object):
        token = str(token)
        self.cloud_resource_manager_client.set_auth_token(token)
        self.compute_client.set_auth_token(token)
