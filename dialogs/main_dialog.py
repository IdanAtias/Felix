from typing import Dict, Optional, List
from dataclasses import dataclass
from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    PromptOptions,
    NumberPrompt,
)
from botbuilder.dialogs.prompts import OAuthPrompt, OAuthPromptSettings

from dialogs import LogoutDialog

from cloud_clients import AzureClient
from cloud_models.azure import Subscription, Vm

Index = str  # representing int index as string


@dataclass
class MainDialogData:
    subscriptions: Dict[Index, Subscription] = None
    running_vms: List[Vm] = None

    @property
    def subscriptions_string(self):
        return " ".join([f"{i}: {s.name}" for i, s in self.subscriptions.items()])

    @property
    def running_vms_string(self):
        return " ".join([f"(name: {vm.name}, rg: {vm.rg})" for vm in self.running_vms])


class MainDialog(LogoutDialog):
    def __init__(self, connection_name: str):
        super(MainDialog, self).__init__(MainDialog.__name__, connection_name)

        self.azclient = AzureClient()
        self.data = MainDialogData()

        # add the dialogs we are going to use
        self.add_dialog(
            OAuthPrompt(
                OAuthPrompt.__name__,
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="Please Sign In",
                    title="Sign In",
                    timeout=300000,
                ),
            )
        )
        self.add_dialog(NumberPrompt(NumberPrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                "WFDialog",
                [
                    self.get_token_step,
                    self.choose_subscription_step,
                    self.show_chosen_subscription_step,
                ],
            )
        )

        # Indicating with what dialog to start
        self.initial_dialog_id = "WFDialog"

    async def get_token_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # There is no reason to store the token locally in the bot because we can always just call
        # the OAuth prompt to get the token or get a new token if needed.
        return await step_context.begin_dialog(OAuthPrompt.__name__)

    async def choose_subscription_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        token = step_context.result.token
        if token:
            await step_context.context.send_activity("You're in! Let's start...")
            self.azclient.set_auth_token(token)
            subscriptions = dict((str(i + 1), sub) for i, sub in enumerate(await self.azclient.subscriptions.list()))
            self.data.subscriptions = subscriptions
            return await step_context.prompt(
                NumberPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text(f"Please choose a subscription: {self.data.subscriptions_string}"),
                )
            )

        await step_context.context.send_activity(
            "Login was not successful please try again."
        )
        return await step_context.end_dialog()

    async def show_chosen_subscription_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        chosen_subscription_idx = str(step_context.result)
        if chosen_subscription_idx not in self.data.subscriptions:
            await step_context.context.send_activity(f"Can't find such option. Please try again.")
            return await step_context.end_dialog()

        subscription = self.data.subscriptions[chosen_subscription_idx]
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
            msg = self.data.running_vms_string
        else:
            msg = f"Looks like there are no running VMs in {subscription.name}"
        await step_context.context.send_activity(msg)

        return await step_context.end_dialog()
