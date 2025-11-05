# /Users/jagan/ai-agent-lab/agent/long_memory/ollama_embed_demo.py
import requests, math, json

MODEL = "nomic-embed-text:latest"
URL   = "http://127.0.0.1:11434/api/embeddings"   # use 127.0.0.1 to avoid odd resolver issues

def embed_one(text: str):
    r = requests.post(URL, json={"model": MODEL, "prompt": text}, timeout=60)
    try:
        r.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"HTTP error for {text!r}: {r.text[:200]}") from e
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"Ollama error for {text!r}: {data['error']}")
    vec = data.get("embedding")
    if not isinstance(vec, list) or not vec:
        raise RuntimeError(f"Empty/invalid embedding for {text!r}: {json.dumps(data)[:300]}")
    return vec

def ollama_embed(texts):
    return [embed_one(t) for t in texts]

def cosine_similarity(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb)

if __name__ == "__main__":
    texts = ["apple", "red fruit"]
    vecs = ollama_embed(texts)
    print("dims:", len(vecs), "x", len(vecs[0]))  # should print: 2 x <dimension>
    sim = cosine_similarity(vecs[0], vecs[1])
    print(f"cosine_similarity('apple','red fruit') = {sim:.4f}")