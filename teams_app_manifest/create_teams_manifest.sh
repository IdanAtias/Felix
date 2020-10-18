#!/bin/bash

MS_APP_ID=$1

cat manifest_template.json | sed "s/MICROSOFT-APP-ID/$MS_APP_ID/" | sed "s/MICROSOFT-APP-ID/$MS_APP_ID/" > manifest.json

zip manifest.zip manifest.json icon-color.png icon-outline.png
rm -f manifest.json

echo "done"

