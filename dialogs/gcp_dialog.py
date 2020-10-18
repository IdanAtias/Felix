from typing import List
from dataclasses import dataclass
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import OAuthPrompt, OAuthPromptSettings

from dialogs import LogoutDialog

from cloud_clients import GcpClient
from cloud_models.gcp import Instance


@dataclass
class GcpDialogData:
    running_instances: List[Instance] = None

    @property
    def running_instances_string(self) -> str:
        return "\n\n".join(
            [
                f"{i+1}. {instance.name} (project: {instance.project}, zone: {instance.zone})"
                for i, instance in enumerate(self.running_instances)
            ]
        )


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
                    self.list_running_vms_step,
                ],
            )
        )

        self.initial_dialog_id = "GcpDialog"

    async def get_token_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # There is no reason to store the token locally in the bot because we can always just call
        # the OAuth prompt to get the token or get a new token if needed.
        return await step_context.begin_dialog("GcpAuthPrompt")

    async def list_running_vms_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        token = step_context.result.token
        if not token:
            await step_context.context.send_activity(
                "Login was not successful please try again."
            )
            return await step_context.end_dialog()

        self.gclient.set_auth_token(token)
        await step_context.context.send_activity(f"OK! Let's check for running instances in GCP...")

        next_page_token = None
        self.data.running_instances = []
        while True:
            # aggregate running vms
            instances, next_page_token = await self.gclient.instances.list_all_running_instances(
                # TODO currently only flex-gcp-kdp and us-central1-c is supported for GCP
                project="flex-gcp-kdp", zone="us-central1-c", next_page_token=next_page_token,
            )
            self.data.running_instances += instances
            if not next_page_token:
                # no more vms
                break

        if self.data.running_instances:
            msg = self.data.running_instances_string
        else:
            msg = "Looks like there are no running instances in GCP"
        await step_context.context.send_activity(msg)

        return await step_context.end_dialog()
