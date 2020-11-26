from .azure import get_azure_vms_card, AZURE_VMS_CARD_MAX_VMS
from .gcp import get_gcp_instances_card, GCP_INSTANCES_CARD_MAX_INSTANCES

__all__ = [
    "get_azure_vms_card",
    "AZURE_VMS_CARD_MAX_VMS",
    "get_gcp_instances_card",
    "GCP_INSTANCES_CARD_MAX_INSTANCES",
]
