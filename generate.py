import os
import re
import torch
import tiktoken
from model import Kynto, KyntoConfig


# -----------------------
# CONFIG
# -----------------------
_default_model = "kynto.pt" if os.path.exists("kynto_sft.pt") else "kynto.pt"

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

print(
    f"device: {device} | model: {MODEL_PATH} | mode: {'SFT' if IS_SFT else 'base'}",
    flush=True,
)


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

# Supports both:
# 1. model-only file: torch.save(model.state_dict(), "kynto.pt")
# 2. checkpoint file: {"model": model.state_dict(), ...}
if isinstance(state, dict) and "model" in state:
    state = state["model"]

model.load_state_dict(state, strict=False)
model.eval()

print("Kynto model loaded.")
print("Type your prompt. Type 'exit' or 'quit' to stop.\n")


# -----------------------
# HELPERS
# -----------------------
def build_prompt(user_prompt: str) -> str:
    user_prompt = user_prompt.strip()

    if IS_SFT:
        return (
            "<|user|>"
            f"{user_prompt}\n\n"
            "Answer clearly and directly. "
            "Use simple language. "
            "Keep the answer short. "
            "Stop after the answer. "
            "Do not continue into another article. "
            "Do not repeat the question. "
            "Do not invent unrelated steps. "
            "If a checklist is requested, use bullet points."
            "\n<|assistant|>"
        )

    return (
        f"Question: {user_prompt}\n"
        "Answer clearly in a short response. Stop after the answer.\n"
        "Answer:"
    )


def clean_output(text: str) -> str:
    text = text.strip()

    # Remove accidental special tags
    text = text.replace("<|assistant|>", "")
    text = text.replace("<|user|>", "")
    text = text.replace("<|endoftext|>", "")

    # Stop if model starts fake new turns or article sections
    stop_markers = [
        "\n<|user|>",
        "\nUser:",
        "\nQuestion:",
        "\nQ:",
        "\n###",
        "\n##",
        "\n2)",
        "\n3)",
        "\nWhat is ",
        "\nWhat are ",
        "\nHow does ",
        "\nThe use of ",
    ]

    for marker in stop_markers:
        if marker in text:
            text = text.split(marker)[0].strip()

    # Remove common noisy artifacts
    text = re.sub(r"\]\}+", "", text)
    text = re.sub(r"\$\{+", "", text)
    text = re.sub(r"#{4,}", "", text)
    text = re.sub(r"TEXTURE", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\\-", "-", text)

    # Collapse blank lines/spaces
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", " ", text)

    return text.strip()


def limit_answer(text: str, max_sentences: int = 3) -> str:
    text = text.strip()

    if not text:
        return text

    # Stop at second paragraph
    if "\n\n" in text:
        text = text.split("\n\n")[0].strip()

    # If bullet list, keep up to 8 bullets
    lines = text.splitlines()
    bullet_lines = [
        line for line in lines
        if line.strip().startswith(("-", "*", "•")) or re.match(r"^\s*\d+[\).\s]", line)
    ]

    if len(bullet_lines) >= 2:
        kept = []
        bullet_count = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("-", "*", "•")) or re.match(r"^\s*\d+[\).\s]", stripped):
                bullet_count += 1
                if bullet_count > 8:
                    break
            kept.append(line)

        return "\n".join(kept).strip()

    # Otherwise keep max_sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)

    if len(sentences) > max_sentences:
        text = " ".join(sentences[:max_sentences]).strip()

    return text.strip()


# -----------------------
# GENERATION
# -----------------------
@torch.no_grad()
def generate_text(
    prompt: str,
    max_new_tokens: int = 65,
    temperature: float = 0.18,
    top_k: int = 12,
    top_p: float = 0.65,
    repetition_penalty: float = 1.45,
    no_repeat_ngram_size: int = 3,
) -> str:
    prompt = prompt.strip()

    if not prompt:
        return "Please type something."

    input_text = build_prompt(prompt)

    prompt_tokens = enc.encode(
        input_text,
        allowed_special={"<|endoftext|>"},
    )

    if len(prompt_tokens) == 0:
        return "Please type something."

    idx = torch.tensor(prompt_tokens, dtype=torch.long, device=device).unsqueeze(0)
    prompt_len = idx.size(1)

    def get_banned_ngram_tokens(sequence, n):
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

        # Repetition penalty
        if repetition_penalty != 1.0:
            seen_tokens = set(idx[0].tolist())

            for token_id in seen_tokens:
                if logits[0, token_id] > 0:
                    logits[0, token_id] /= repetition_penalty
                else:
                    logits[0, token_id] *= repetition_penalty

        # Block repeated n-grams
        if no_repeat_ngram_size > 0:
            banned_tokens = get_banned_ngram_tokens(
                idx[0].tolist(),
                no_repeat_ngram_size,
            )

            for token_id in banned_tokens:
                logits[0, token_id] = -float("inf")

        if temperature <= 0:
            next_id = torch.argmax(logits, dim=-1, keepdim=True)
        else:
            logits = logits / temperature

            # Top-k filtering
            if top_k > 0:
                topk_vals, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < topk_vals[:, [-1]]] = -float("inf")

            # Top-p filtering
            if top_p < 1.0:
                sorted_logits, sorted_idx = torch.sort(logits, descending=True, dim=-1)
                sorted_probs = torch.softmax(sorted_logits, dim=-1)
                cumulative_probs = torch.cumsum(sorted_probs, dim=-1)

                remove = cumulative_probs - sorted_probs > top_p
                sorted_logits[remove] = -float("inf")

                logits = logits.scatter(dim=-1, index=sorted_idx, src=sorted_logits)

            probs = torch.softmax(logits, dim=-1)

            if torch.isnan(probs).any() or torch.isinf(probs).any():
                break

            next_id = torch.multinomial(probs, num_samples=1)

        idx = torch.cat((idx, next_id), dim=1)

        if next_id.item() == enc.eot_token:
            break

    generated_ids = idx[0, prompt_len:].tolist()
    output = enc.decode(generated_ids)

    output = clean_output(output)
    output = limit_answer(output, max_sentences=3)

    return output if output else "I could not generate a response."


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