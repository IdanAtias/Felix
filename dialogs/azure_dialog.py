import math
from typing import List, Optional
from dataclasses import dataclass
from botbuilder.schema import ActivityTypes, Activity
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

from cards import get_azure_vms_card, AZURE_VMS_CARD_MAX_VMS
from dialogs import LogoutDialog

from cloud_clients import AzureClient
from cloud_models.azure import Subscription, Vm


@dataclass
class AzureDialogData:
    subscriptions: List[Subscription] = None
    running_vms: List[Vm] = None

    @property
    def running_vms_string(self) -> str:
        return "\n\n".join([f"{i+1}. {vm.name} (rg: {vm.rg})" for i, vm in enumerate(self.running_vms)])

    def get_subscription_by_name(self, name: str) -> Optional[Subscription]:
        for sub in self.subscriptions:
            if sub.name == name:
                return sub
        return None


class AzureDialog(LogoutDialog):
    def __init__(self, connection_name: str):
        super(AzureDialog, self).__init__(AzureDialog.__name__, connection_name)

        self.azclient = AzureClient()
        self.data = AzureDialogData()

        self.add_dialog(
            OAuthPrompt(
                "AzureAuthPrompt",
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="Please Sign In",
                    title="Sign In",
                    timeout=300000,
                ),
            )
        )
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                "AzureDialog",
                [
                    self.get_token_step,
                    self.choose_subscription_step,
                    self.list_running_vms_step,
                ],
            )
        )

        self.initial_dialog_id = "AzureDialog"

    async def get_token_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # There is no reason to store the token locally in the bot because we can always just call
        # the OAuth prompt to get the token or get a new token if needed.
        return await step_context.begin_dialog("AzureAuthPrompt")

    async def choose_subscription_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        token = step_context.result.token
        if token:
            await step_context.context.send_activity("You're in! Let's start...")
            self.azclient.set_auth_token(token)
            self.data.subscriptions = await self.azclient.subscriptions.list()
            return await step_context.prompt(
                ChoicePrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please choose a subscription"),
                    choices=[Choice(sub.name) for sub in self.data.subscriptions],
                )
            )

        await step_context.context.send_activity(
            "Login was not successful please try again."
        )
        return await step_context.end_dialog()

    async def list_running_vms_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        chosen_subscription_name = step_context.result.value
        subscription = self.data.get_subscription_by_name(name=chosen_subscription_name)
        if not subscription:
            await step_context.context.send_activity(f"Can't find such option. Please try again.")
            return await step_context.end_dialog()

        await step_context.context.send_activity(f"OK! Let's check for running VMs in {subscription.name}...")

        next_link = None
        self.data.running_vms = []
        while True:
            # aggregate running vms
            vms, next_link = await self.azclient.vms.list_all_running_vms(
                subscription=subscription, next_link=next_link
            )
            self.data.running_vms += vms
            if not next_link:
                # no more vms
                break

        if self.data.running_vms:
            vm_cards = []
            for i in range(0, len(self.data.running_vms), AZURE_VMS_CARD_MAX_VMS):
                vm_cards.append(
                    get_azure_vms_card(vms=self.data.running_vms[i:i+AZURE_VMS_CARD_MAX_VMS], start_idx=i+1)
                )
            msg = Activity(
                type=ActivityTypes.message,
                attachments=vm_cards,
            )
        else:
            msg = f"Looks like there are no running VMs in {subscription.name}"
        await step_context.context.send_activity(msg)

        return await step_context.end_dialog()
