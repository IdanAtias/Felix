import json

from botbuilder.core import CardFactory
from botbuilder.schema import Attachment


AZURE_VM_CARD_JSON_TEMPLATE = """
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.2",
    "body": [
        {
            "type": "Container",
            "items": [
                {
                    "type": "ColumnSet",
                    "columns": [
                        {
                            "type": "Column",
                            "width": "stretch",
                            "id": "",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "<replace-with-vm-name>",
                                    "wrap": true
                                }
                            ]
                        },
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {
                                    "type": "TextBlock",
                                    "text": "<replace-with-vm-rg>",
                                    "wrap": true
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
"""


def get_azure_vm_card(name: str, rg: str) -> Attachment:
    data = json.loads(AZURE_VM_CARD_JSON_TEMPLATE)
    cols = data["body"][0]["items"][0]["columns"]
    cols[0]["items"][0]["text"] = name
    cols[1]["items"][0]["text"] = rg
    return CardFactory.adaptive_card(card=data)
