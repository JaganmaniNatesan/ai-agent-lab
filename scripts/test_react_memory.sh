#!/usr/bin/env bash
set -euo pipefail
base="http://127.0.0.1:8000"
sid="sess_suiteA"

curl -s -X DELETE "$base/memory/clear/$sid" >/dev/null

prompts=(
  "Hello, my name is Jagan."
  "Remember my name for later."
  "Add 10 and 5."
  "Now multiply that result by 2."
  "Convert the last answer to uppercase text."
  "Who am I?"
  "Tell me what we talked about so far in one line."
  "Add 20 and 30, then divide by 10."
  "What was the result of my first calculation?"
  "Goodbye!"
)

i=1
for p in "${prompts[@]}"; do
  echo "🧠 A-$i: $p"
  curl -s -X POST "$base/agent/react" \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\":\"$sid\",\"prompt\":\"$p\"}"
  echo -e "\n"
  ((i++))
done
