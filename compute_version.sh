#!/bin/bash

LATEST_VERSION_DIGEST=$(curl -s 'https://registry.hub.docker.com/v2/repositories/matan8520/dms_backend/tags?name=latest' \
                                    | jq -r '.results[0].digest')
LATEST_VERSION_TAG=$(curl -s https://registry.hub.docker.com/v2/repositories/matan8520/dms_backend/tags \
                            | jq -r --arg d "$LATEST_VERSION_DIGEST" '
                            .results[]
                            | select(.digest == $d)
                            | select(.name | startswith("v"))
                            | .name
                        ' | cut -d'v' -f2-)
if [ "$LATEST_VERSION_TAG" = "" ]; then 
    LATEST_VERSION_TAG="0.0.0"
fi

declare -i major=$(echo "$LATEST_VERSION_TAG" | cut -d'.' -f1)
declare -i minor=$(echo "$LATEST_VERSION_TAG" | cut -d'.' -f2)
declare -i patch=$(echo "$LATEST_VERSION_TAG" | cut -d'.' -f3)

patch=$((patch + 1))

NEW_VERSION_TAG="v$major.$minor.$patch"
