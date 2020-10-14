from typing import Dict, Optional
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
from cloud_models.azure import Subscription

Index = int  # representing an index


@dataclass
class MainDialogData:
    subscriptions: Dict[Index, Subscription]

    @property
    def subscriptions_string(self):
        return " ".join([f"{i}: {s.name}" for i, s in self.subscriptions.items()])


class MainDialog(LogoutDialog):
    def __init__(self, connection_name: str):
        super(MainDialog, self).__init__(MainDialog.__name__, connection_name)

        self.azclient = AzureClient()
        self.data: Optional[MainDialogData] = None

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
                    self.show_chosen_subscription,
                ],
            )
        )

        # Indicating with what dialog to start
        self.initial_dialog_id = "WFDialog"

    async def _refresh_data(self, token: object):
        """helper func to refresh all relevant cloud data for the dialog"""
        if not token:
            raise ValueError("Can't work with without a valid token!")

        self.azclient.set_auth_token(token)
        subscriptions = dict((i + 1, sub) for i, sub in enumerate(await self.azclient.subscriptions.list()))
        self.data = MainDialogData(subscriptions=subscriptions)

    async def get_token_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # There is no reason to store the token locally in the bot because we can always just call
        # the OAuth prompt to get the token or get a new token if needed.
        return await step_context.begin_dialog(OAuthPrompt.__name__)

    async def choose_subscription_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        token = step_context.result.token
        if token:
            await step_context.context.send_activity("You're in! Let's start...")
            await self._refresh_data(token)
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

    async def show_chosen_subscription(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        chosen_subscription_idx = int(step_context.result)
        if chosen_subscription_idx not in self.data.subscriptions:
            await step_context.context.send_activity(f"Can't find such option. Please try again.")
            return await step_context.end_dialog()

        subscription_name = self.data.subscriptions[chosen_subscription_idx].name
        await step_context.context.send_activity(f"OK! Let's start sniffing around in {subscription_name}...")
        return await step_context.end_dialog()
