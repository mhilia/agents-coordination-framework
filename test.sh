#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="prj-152202612488"
REGION="europe-west1"
MODEL="claude-sonnet-4-6"
TOKEN=$(gcloud auth print-access-token)

curl -s -X POST \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/publishers/anthropic/models/${MODEL}:rawPredict" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "anthropic_version": "vertex-2023-10-16",
    "max_tokens": 64,
    "messages": [{"role": "user", "content": "ping"}]
  }' | python3 -m json.tool