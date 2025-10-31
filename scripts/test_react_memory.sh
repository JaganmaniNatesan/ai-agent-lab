#!/bin/bash
# ======================================================
# 🧠 AI-Agent-Lab ReAct & Memory Test Loop
# Runs a series of POST /agent/react calls using curl
# ======================================================

URL="http://127.0.0.1:8000/agent/react"
SESSION_ID="sess_demo"

declare -a TESTS=(
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

echo "=== 🧩 Running 10-turn ReAct Memory Test ==="
echo "Session ID: $SESSION_ID"
echo "-------------------------------------------"

for i in "${!TESTS[@]}"; do
  PROMPT="${TESTS[$i]}"
  echo -e "\n🧠 Turn $((i+1)) - Prompt: \"$PROMPT\""

  curl -s -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"$PROMPT\", \"session_id\": \"$SESSION_ID\"}" \
    | jq -r '.response'

  sleep 2  # small delay for readability
done

echo -e "\n✅ Test sequence complete."
