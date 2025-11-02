#!/usr/bin/env bash
set -euo pipefail
base="http://127.0.0.1:8000"
sid="sess_suiteB"

curl -s -X DELETE "$base/memory/clear/$sid" >/dev/null

prompts=(
  "hi there"
  "add 7 and 3 then divide by 0"
  "add 7 and 3 then divide by 2"
  "use tool DIVDE with a: 50 and b: 10"
  "ADD 1 and 2"
  "again do the same"
  "uppercase hello world"
  "tell me what we talked about so far in one line"
  "good bye."
)

i=1
for p in "${prompts[@]}"; do
  echo "🧠 B-$i: $p"
  curl -s -X POST "$base/agent/react" \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\":\"$sid\",\"prompt\":\"$p\"}"
  echo -e "\n"
  ((i++))
done
