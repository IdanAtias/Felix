#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

""" Bot Configuration """


class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ["MicrosoftAppId"]
    APP_PASSWORD = os.environ["MicrosoftAppPassword"]
    AAD_CONNECTION_NAME = os.environ.get("AadConnectionName")
    GCP_CONNECTION_NAME = os.environ.get("GcpConnectionName")
