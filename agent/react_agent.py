from models.reason_llm import run_reasoning_model
from models.llm import run_tool_request

MAX_STEPS = 10

def run_react(prompt: str) -> str:
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
