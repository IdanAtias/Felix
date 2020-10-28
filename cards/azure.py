import json
from typing import List

from botbuilder.core import CardFactory
from botbuilder.schema import Attachment

from cloud_models.azure import Vm


AZURE_VMS_CARD_JSON_TEMPLATE = """
{
    "type": "AdaptiveCard",
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.2",
    "body": [
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "10",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "",
                            "wrap": true
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "50",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "VM",
                            "wrap": true,
                            "isSubtle": true
                        }
                    ]
                },
                {
                    "type": "Column",
                    "width": "40",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "RG",
                            "wrap": true,
                            "isSubtle": true
                        }
                    ]
                }
            ]
        },
        {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": "10",
                    "items": []
                },
                {
                    "type": "Column",
                    "width": "50",
                    "items": []
                },
                {
                    "type": "Column",
                    "width": "40",
                    "items": []
                }
            ]
        }
    ]
}
"""


def _get_text_block_dict(text: str, wrap: bool = False, is_subtle: bool = False) -> dict:
    return {
        "type": "TextBlock",
        "text": text,
        "wrap": wrap,
        "isSubtle": is_subtle,
    }


def _get_vm_idx_dict(idx: int) -> dict:
    return _get_text_block_dict(text=f"{idx}.", is_subtle=True)


def _get_vm_name_dict(name: str) -> dict:
    return _get_text_block_dict(text=name)


def _get_vm_rg_dict(rg: str) -> dict:
    return _get_text_block_dict(text=rg)


def get_azure_vms_card(vms: List[Vm]) -> Attachment:
    data = json.loads(AZURE_VMS_CARD_JSON_TEMPLATE)
    idx_col, name_col, rg_col = data["body"][1]["columns"]
    for i, vm in enumerate(vms):
        idx_col["items"].append(_get_vm_idx_dict(idx=i+1))
        name_col["items"].append(_get_vm_name_dict(name=vm.name))
        rg_col["items"].append(_get_vm_rg_dict(rg=vm.rg))
    return CardFactory.adaptive_card(card=data)
