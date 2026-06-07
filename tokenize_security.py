import json
import random
from pathlib import Path

import numpy as np
import tiktoken


INPUT = Path("data_security/clean/security_corpus.jsonl")
OUT_DIR = Path("data")

TRAIN_OUT = OUT_DIR / "security_tokens_train.bin"
VAL_OUT = OUT_DIR / "security_tokens_val.bin"

VAL_RATIO = 0.002
SEED = 42

random.seed(SEED)
OUT_DIR.mkdir(parents=True, exist_ok=True)

enc = tiktoken.get_encoding("gpt2")
eot = enc.eot_token

train_tokens = []
val_tokens = []

docs = 0

with INPUT.open("r", encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
            text = obj.get("text", "").strip()
        except Exception:
            continue

        if len(text) < 100:
            continue

        ids = enc.encode_ordinary(text)
        ids.append(eot)

        if random.random() < VAL_RATIO:
            val_tokens.extend(ids)
        else:
            train_tokens.extend(ids)

        docs += 1

        if docs % 10000 == 0:
            print(
                f"docs={docs:,} "
                f"train_tokens={len(train_tokens):,} "
                f"val_tokens={len(val_tokens):,}",
                flush=True,
            )

train_arr = np.array(train_tokens, dtype=np.uint16)
val_arr = np.array(val_tokens, dtype=np.uint16)

train_arr.tofile(TRAIN_OUT)
val_arr.tofile(VAL_OUT)

print("DONE")
print(f"docs: {docs:,}")
print(f"train tokens: {len(train_arr):,}")
print(f"val tokens:   {len(val_arr):,}")
print(f"train file: {TRAIN_OUT}")
print(f"val file:   {VAL_OUT}")