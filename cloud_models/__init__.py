from enum import Enum


class Cloud(str, Enum):
    azure = "Azure"
    gcp = "GCP"
