import os
import torch
import tiktoken
from model import Kynto, KyntoConfig

# -----------------------
# CONFIG
# -----------------------
_default_model = "kynto_sft.pt" if os.path.exists("kynto_sft.pt") else "kynto.pt"
MODEL_PATH = os.getenv("MODEL_PATH", _default_model)
BLOCK_SIZE = 1024
IS_SFT = "sft" in os.path.basename(MODEL_PATH)

# -----------------------
# DEVICE
# -----------------------
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"device: {device}  |  model: {MODEL_PATH}  |  mode: {'SFT' if IS_SFT else 'base'}", flush=True)

# -----------------------
# TOKENIZER
# -----------------------
enc = tiktoken.get_encoding("gpt2")

# -----------------------
# LOAD MODEL
# -----------------------
config = KyntoConfig(block_size=BLOCK_SIZE)
model = Kynto(config).to(device)

state = torch.load(MODEL_PATH, map_location=device, weights_only=False)
if isinstance(state, dict) and "model" in state:
    state = state["model"]
model.load_state_dict(state, strict=False)
model.eval()

print("Kynto model loaded.")
print("Type your prompt. Type 'exit' or 'quit' to stop.\n")

# -----------------------
# GENERATION
# -----------------------
@torch.no_grad()
def generate_text(
    prompt: str,
    max_new_tokens: int = 250,
    temperature: float = 0.8,
    top_k: int = 50,
    top_p: float = 0.9,
    repetition_penalty: float = 1.3,
    no_repeat_ngram_size: int = 3,   # blocks repeating any 3-gram
) -> str:
    prompt = prompt.strip()
    if not prompt:
        return "Please type something."

    if IS_SFT:
        input_text = f"<|user|>{prompt}\n<|assistant|>"
    else:
        input_text = f"Question: {prompt}\nAnswer:"

    prompt_tokens = enc.encode(input_text, allowed_special={"<|endoftext|>"})
    idx = torch.tensor(prompt_tokens, dtype=torch.long, device=device).unsqueeze(0)
    prompt_len = idx.size(1)

    def get_banned_ngram_tokens(sequence, n):
        # returns tokens that would create a repeated n-gram
        if len(sequence) < n - 1:
            return set()
        prefix = tuple(sequence[-(n - 1):])
        banned = set()
        for i in range(len(sequence) - n + 1):
            if tuple(sequence[i:i + n - 1]) == prefix:
                banned.add(sequence[i + n - 1])
        return banned

    for _ in range(max_new_tokens):
        idx_cond = idx[:, -BLOCK_SIZE:]
        logits, _ = model(idx_cond)
        if logits.size(1) == 0:
            break
        logits = logits[:, -1, :]

        # repetition penalty
        if repetition_penalty != 1.0:
            seen = set(idx[0].tolist())
            for tid in seen:
                if logits[0, tid] > 0:
                    logits[0, tid] /= repetition_penalty
                else:
                    logits[0, tid] *= repetition_penalty

        # no-repeat n-gram blocking (kills the looping)
        if no_repeat_ngram_size > 0:
            banned = get_banned_ngram_tokens(idx[0].tolist(), no_repeat_ngram_size)
            for tid in banned:
                logits[0, tid] = -float("inf")

        if temperature <= 0:
            next_id = torch.argmax(logits, dim=-1, keepdim=True)
        else:
            logits = logits / temperature
            if top_k > 0:
                topk_vals, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < topk_vals[:, [-1]]] = -float("inf")
            if top_p < 1.0:
                sorted_logits, sorted_idx = torch.sort(logits, descending=True, dim=-1)
                cum_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
                remove = cum_probs - torch.softmax(sorted_logits, dim=-1) > top_p
                sorted_logits[remove] = -float("inf")
                logits = logits.scatter(dim=-1, index=sorted_idx, src=sorted_logits)
            probs = torch.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)

        idx = torch.cat((idx, next_id), dim=1)
        if next_id.item() == enc.eot_token:
            break

    generated_ids = idx[0, prompt_len:].tolist()
    return enc.decode(generated_ids).strip()

# -----------------------
# CHAT LOOP
# -----------------------
while True:
    try:
        user_input = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        break
    if user_input.lower() in ["exit", "quit", "q"]:
        print("Goodbye.")
        break
    if not user_input:
        print("Please type something.\n")
        continue
    output = generate_text(user_input)
    print(f"\nKynto:\n{output}\n")
    print("=" * 80 + "\n")