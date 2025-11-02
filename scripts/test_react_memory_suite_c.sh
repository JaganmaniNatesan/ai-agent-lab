#!/usr/bin/env bash
set -euo pipefail
base="http://127.0.0.1:8000"
sid="sess_suiteC"

curl -s -X DELETE "$base/memory/clear/$sid" >/dev/null

prompts=(
  "hey, call me Jay."
  "who am i?"
  "add 100 and 23"
  "add 10 and 5 then multiply by 3"
  "what was the result of my first calculation?"
  "title case \"hello jay agent\""
  "uppercase <last_result>"
  "Add 12 and 8"
  "divide <last_result> by 5"
  "tell me what we talked about so far in one line"
  "see you later"
  "who am I?"
)

i=1
for p in "${prompts[@]}"; do
  echo "🧠 C-$i: $p"
  curl -s -X POST "$base/agent/react" \
    -H 'Content-Type: application/json' \
    -d "{\"session_id\":\"$sid\",\"prompt\":\"$p\"}"
  echo -e "\n"
  ((i++))
done
