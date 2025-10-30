import subprocess

from fastapi.responses import StreamingResponse


def stream_local_model(prompt: str):
    """Stream token from ollama model as they arrive """
    cmd = ['ollama', 'run', 'llama3.1', prompt]

    result = subprocess.Popen(cmd, text=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)

    def generate():
        for line in result.stdout:
            yield line
        result.stdout.close()

    return StreamingResponse(generate(), media_type='text/plain')
