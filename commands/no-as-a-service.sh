#!/bin/bash

# Fetch the JSON response
RESPONSE=$(curl -s https://naas.isalman.dev/no)

# Use Python to extract the 'reason' key
REASON=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['reason'])")

echo "$REASON"
