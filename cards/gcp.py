import json
from typing import List

from botbuilder.core import CardFactory
from botbuilder.schema import Attachment

from cloud_models.gcp import Instance

GCP_INSTANCES_CARD_MAX_INSTANCES = 50
GCP_INSTANCES_CARD_JSON_TEMPLATE = """
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
                            "text": "Instance",
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
                            "text": "Project",
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


def _get_instance_idx_dict(idx: int) -> dict:
    return _get_text_block_dict(text=f"{idx}.", is_subtle=True)


def _get_instance_name_dict(name: str) -> dict:
    return _get_text_block_dict(text=name)


def _get_instance_project_dict(project: str) -> dict:
    return _get_text_block_dict(text=project)


def get_gcp_instances_card(instances: List[Instance], start_idx: int) -> Attachment:
    data = json.loads(GCP_INSTANCES_CARD_JSON_TEMPLATE)
    idx_col, name_col, project_col = data["body"][1]["columns"]
    for i, instance in enumerate(instances):
        idx_col["items"].append(_get_instance_idx_dict(idx=start_idx+i))
        name_col["items"].append(_get_instance_name_dict(name=instance.name))
        project_col["items"].append(_get_instance_project_dict(project=instance.project))
    return CardFactory.adaptive_card(card=data)
