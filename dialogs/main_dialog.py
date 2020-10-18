from botbuilder.core import MessageFactory
from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
    PromptOptions,
    Choice,
    ChoicePrompt,
)
from botbuilder.dialogs import ComponentDialog

from .azure_dialog import AzureDialog
from cloud_models import Cloud


class MainDialog(ComponentDialog):
    def __init__(self, azure_connection_name: str = None, gcp_connection_name: str = None):
        super(MainDialog, self).__init__(MainDialog.__name__)

        if not azure_connection_name and not gcp_connection_name:
            raise ValueError(f"Felix must be provided with at least 1 connection name (GCP/Azure)")

        # add the dialogs
        if azure_connection_name:
            self.azure_dialog = AzureDialog(connection_name=azure_connection_name)
            self.add_dialog(self.azure_dialog)

        if gcp_connection_name:
            pass  # todo

        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                "MainDialog",
                [
                    self.choose_cloud_step,
                    self.begin_cloud_dialog_step,
                ]
            )
        )

        self.initial_dialog_id = "MainDialog" # Indicating with what dialog to start

    async def choose_cloud_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Please choose the cloud you want me to have a look at"),
                choices=[Choice(Cloud.azure.value), Choice(Cloud.gcp.value)],
            )
        )

    async def begin_cloud_dialog_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        cloud = step_context.result.value

        if cloud == Cloud.azure:
            return await step_context.begin_dialog(self.azure_dialog.id)

        if cloud == Cloud.gcp:
            await step_context.context.send_activity("GCP chosen")
            return await step_context.end_dialog()

        await step_context.context.send_activity("Sorry, I don't support such cloud. Please try again.")
