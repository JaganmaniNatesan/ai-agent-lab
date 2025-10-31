from typing import List, Tuple

from agent.memory_adaptor  import load_context, persist_turn
from models.llm import run_tool_request

MAX_STEPS = 10
MEMORY_TURNS = 6


def run_react(prompt: str, session_id: str, max_steps: int = MAX_STEPS):
    """
        Your existing ReAct controller, now with memory.
        1) Load last MEMORY_TURNS messages for session
        2) Add them to the model preface
        3) Run normal thought->action->observation loop
        4) Persist
    """

    past = load_context(session_id, max_steps)
    memory_block = format_memory(past)
    preface = (
        "You are a helpful, tool-using assistant.\n"
        "Use tools when needed. Think step by step.\n\n"
    )
    # 1) Load memory context
    if memory_block:
        preface += "Recent Conversation: \n" + memory_block + "\n\n"

    # 2) Build the initial controller prompt
    controller_input = f"{preface} Current user request:\n{prompt}\n"
    # 3) ReAct loop (sketch — keep your working version here)
    #    Make sure `controller_input` is fed to your reasoning LLM.
    final_answer = _react_core(controller_input, max_steps=max_steps)
    # (Where _react_core is your existing loop producing the final string.
    #  If your function already exists under a different name, just
    #  inject `controller_input` at the right place.)

    # 4) Persist this turn
    persist_turn(session_id, user_text=prompt, final_text=final_answer)

    return final_answer


def run_react_local(prompt: str) -> str:
    """
    ReAct loop: reason -> act -> observe -> reflect -> answer
    """
    conversation = []
    observation = ""

    for step in range(MAX_STEPS):
        context = "\n".join(conversation)
        model_input = (
            f"Previous context:\n{context}\n\n"
            f"Latest observation: {observation}\n"
            f"User request: {prompt}\n\n"
            "Think step by step. "
            "If you need external information or calculations, emit a JSON tool call. "
            "If you have the answer, respond with 'Final Answer: ...'"
        )

        output = run_reasoning_model(model_input)
        conversation.append(f"Step {step + 1} model output: {output}")

        # Check for Final Answer
        if output.strip().lower().startswith("final answer"):
            return output

        # Otherwise try a tool call
        if "tool" in output:
            observation = run_tool_request(output)
            conversation.append(f"Observation: {observation}")
        else:
            observation = "No tool call found"
            conversation.append("Observation: No tool call found")

    # If it never ends cleanly
    return "Reached max reasoning steps without final answer."


def format_memory(messages: List[Tuple[str, str]]) -> str:
    lines = []
    for role, content in messages:
        role_tag = "User" if role == "user" else "Assistant"
        lines.append(f"[{role_tag}] {content}")

    return "\n".join(lines)


from models.reason_llm import run_reasoning_model
from tools.registry import run_tool
import json
import re


import json
import re
from models.reason_llm import run_reasoning_model
from tools.registry import run_tool

import json
import re
from models.reason_llm import run_reasoning_model
from tools.registry import run_tool


def _react_core(prompt: str, max_steps: int = 10) -> str:
    """
    Step-by-step ReAct reasoning loop with debugging output.
    Handles tool calls, observations, and final answers.
    """
    controller_prompt = prompt
    print("\n=== 🧠 ReAct Debug Start ===")
    print(controller_prompt)
    print("============================\n")

    for step in range(max_steps):
        print(f"\n--- Step {step + 1} ---")
        model_output = run_reasoning_model(controller_prompt)
        print(f"Model raw output:\n{model_output}\n")

        # stop condition
        if "Final Answer:" in model_output:
            answer = model_output.split("Final Answer:")[-1].strip()
            print(f"✅ Final answer found: {answer}")
            print("=== 🧩 ReAct Debug End ===\n")
            return answer

        # detect JSON tool call
        match = re.search(r"\{.*?\}", model_output, flags=re.DOTALL)
        if match:
            try:
                tool_request = json.loads(match.group(0))
                tool = tool_request.get("tool")
                args = tool_request.get("args", {})
                print(f"🧰 Detected tool call: {tool}({args})")

                result = run_tool(tool, args)
                print(f"🔍 Tool result: {result}")

                observation = f"\nObservation: {result}\nThought: "
                controller_prompt += f"\n{model_output}{observation}\n"

            except Exception as e:
                controller_prompt += f"\nObservation: [error executing tool: {e}]\nThought: "
                print(f"❌ Tool execution error: {e}")

        else:
            # no JSON found — append hint and continue
            controller_prompt += f"\nObservation: (no valid tool call)\nThought: "
            print("⚠️ No JSON tool call detected.")

    print("⚠️ Reached max reasoning steps without final answer.\n")
    return "Reached max reasoning steps without final answer."
