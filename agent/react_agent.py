from typing import List, Tuple

from models.reason_llm import run_reasoning_model
from models.llm import run_tool_request
from memory_adaptor import load_context, persist_turn

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
        conversation.append(f"Step {step+1} model output: {output}")

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


def format_memory(messages: List[Tuple[str,str]]) -> str:
    lines =[]
    for role, content in messages:
        role_tag ="User" if role == "user" else "Assistant"
        lines.append(f"[{role_tag}] {content}")

    return "\n".join(lines)
