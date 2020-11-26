import asyncio
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass
from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    PromptOptions,
    Choice,
    ChoicePrompt,
)
from botbuilder.dialogs.prompts import OAuthPrompt, OAuthPromptSettings

from dialogs import LogoutDialog

from cloud_clients import GcpClient
from cloud_models.gcp import Instance, Project

US_ZONES_LIST = [
    'us-central1-a',
    'us-central1-b',
    'us-central1-c',
    'us-central1-f',
    'us-east1-b',
    'us-east1-c',
    'us-east1-d',
    'us-east4-a',
    'us-east4-b',
    'us-east4-c',
    'us-west1-a',
    'us-west1-b',
    'us-west1-c',
    'us-west2-a',
    'us-west2-b',
    'us-west2-c',
    'us-west3-a',
    'us-west3-b',
    'us-west3-c',
    'us-west4-a',
    'us-west4-b',
    'us-west4-c',
]


class ChosenProjectType(str, Enum):
    SPECIFIC = "Specific"
    ALL = "All"


@dataclass
class GcpDialogData:
    projects: List[Project] = None
    selected_projects: List[Project] = None
    running_instances: List[Instance] = None

    @property
    def running_instances_string(self) -> str:
        return "\n\n".join(
            [
                f"{i+1}. {instance.name} (project: {instance.project}, zone: {instance.zone})"
                for i, instance in enumerate(self.running_instances)
            ]
        )

    def get_project_by_name(self, name: str) -> Optional[Project]:
        for project in self.projects:
            if project.name == name:
                return project
        return None


class GcpDialog(LogoutDialog):
    def __init__(self, connection_name: str):
        super(GcpDialog, self).__init__(GcpDialog.__name__, connection_name)

        self.gclient = GcpClient()
        self.data = GcpDialogData()

        self.add_dialog(
            OAuthPrompt(
                "GcpAuthPrompt",
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="Please Sign In",
                    title="Sign In",
                    timeout=300000,
                ),
            )
        )
        self.add_dialog(
            WaterfallDialog(
                "GcpDialog",
                [
                    self.get_token_step,
                    self.choose_all_or_specific_project,
                    self.choose_specific_project_step,
                    self.list_running_instances_step,
                ],
            )
        )

        self.initial_dialog_id = "GcpDialog"

    async def get_token_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # There is no reason to store the token locally in the bot because we can always just call
        # the OAuth prompt to get the token or get a new token if needed.
        return await step_context.begin_dialog("GcpAuthPrompt")

    async def choose_all_or_specific_project(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        token = step_context.result.token
        if not token:
            await step_context.context.send_activity(
                "Login was not successful please try again."
            )
            return await step_context.end_dialog()

        self.gclient.set_auth_token(token)

        await step_context.context.send_activity("You're in! Let's start..")
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Would you like me to check all your GCP projects or a specific one?"),
                choices=[choice_type.value for choice_type in ChosenProjectType],
            )
        )

    async def choose_specific_project_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # we need all projects either way (SPECIFIC/ALL)
        self.data.projects = await self.gclient.projects.list()

        chosen_project_type = str(step_context.result.value)
        if chosen_project_type == ChosenProjectType.ALL:
            await step_context.context.send_activity("All projects it is!")
            return await step_context.next(result=ChosenProjectType.ALL)

        # specific project selection
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("OK. Which one?"),
                choices=[Choice(project.name) for project in self.data.projects],
            )
        )

    async def _list_running_instances_in_a_single_project_and_zone(self, project: Project, zone: str):
        running_instances = []
        next_page_token = None
        while True:
            # aggregate running instances
            instances, next_page_token = await self.gclient.instances.list_running(
                project=project.id, zone=zone, next_page_token=next_page_token,
            )
            running_instances += instances
            if not next_page_token:
                # no more instances
                break
        return running_instances

    async def list_running_instances_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result == ChosenProjectType.ALL:
            self.data.selected_projects = self.data.projects
            await step_context.context.send_activity(
                f"OK! Let's check for running instances across all your projects...(US zones only)"
            )
        else:
            project_name = str(step_context.result.value)
            project: Project = self.data.get_project_by_name(name=project_name)
            if not project:
                return await step_context.end_dialog()
            self.data.selected_projects = [project]
            await step_context.context.send_activity(
                f"OK! Let's check for running instances in {project.name}...(US zones only)"
            )

        tasks = []
        for project in self.data.selected_projects:
            for zone in US_ZONES_LIST:
                tasks.append(self._list_running_instances_in_a_single_project_and_zone(project=project, zone=zone))

        self.data.running_instances = []
        for running_instances in await asyncio.gather(*tasks):
            self.data.running_instances += running_instances

        if self.data.running_instances:
            msg = self.data.running_instances_string
        elif step_context.result == ChosenProjectType.ALL:
            msg = f"Looks like there are no running instances in all of your GCP projects (US zones only)"
        else:
            msg = f"Looks like there are no running instances in {project.name} (US zones only)"
        await step_context.context.send_activity(msg)

        return await step_context.end_dialog()
