from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import tiktoken
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model import Kynto, KyntoConfig

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# load model
print("Loading Kynto...")
device = "mps" if torch.backends.mps.is_available() else "cpu"
enc = tiktoken.get_encoding("gpt2")
config = KyntoConfig()
model = Kynto(config).to(device)

model_path = "kynto_sft.pt" if os.path.exists("kynto_sft.pt") else "kynto.pt"
state = torch.load(model_path, map_location=device, weights_only=False)
if isinstance(state, dict) and "model" in state:
    state = state["model"]
model.load_state_dict(state, strict=False)
model.eval()
print(f"Kynto loaded from {model_path} on {device}")

class ChatRequest(BaseModel):
    message: str
    model: str = "Kynto Base"

@torch.no_grad()
def generate(prompt, max_tokens=250, temperature=0.7, top_k=40, top_p=0.9, rep_penalty=1.3):
    tokens = enc.encode(prompt, allowed_special={"<|endoftext|>"})
    idx = torch.tensor(tokens, dtype=torch.long, device=device).unsqueeze(0)
    prompt_len = len(tokens)

    for _ in range(max_tokens):
        logits, _ = model(idx[:, -1024:])
        logits = logits[:, -1, :]

        seen = set(idx[0].tolist())
        for tid in seen:
            if logits[0, tid] > 0: logits[0, tid] /= rep_penalty
            else: logits[0, tid] *= rep_penalty

        logits = logits / temperature
        if top_k > 0:
            v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
            logits[logits < v[:, [-1]]] = -float("inf")

        probs = torch.softmax(logits, dim=-1)
        if torch.isnan(probs).any(): break
        next_id = torch.multinomial(probs, 1)
        idx = torch.cat([idx, next_id], dim=1)
        if next_id.item() == enc.eot_token: break

    return enc.decode(idx[0, prompt_len:].tolist()).strip()

@app.post("/chat")
async def chat(req: ChatRequest):
    is_sft = os.path.exists("kynto_sft.pt")
    if is_sft:
        prompt = f"<|user|>{req.message}\n<|assistant|>"
    else:
        prompt = f"Question: {req.message}\nAnswer:"

    response = generate(prompt)
    return {"response": response, "model": req.model}

@app.get("/health")
async def health():
    return {"status": "ok", "model": model_path, "device": device}
