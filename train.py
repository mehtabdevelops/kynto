import glob
import math
import os
import re
import time

import numpy as np
import torch

from model import Kynto, KyntoConfig


# -----------------------
# CONFIG
# -----------------------
device = "cuda" if torch.cuda.is_available() else "cpu"

batch_size = int(os.getenv("BATCH_SIZE", "4"))
block_size = int(os.getenv("BLOCK_SIZE", "1024"))

# ✅ UPDATED TO 50,000 STEPS
max_iters = int(os.getenv("MAX_ITERS", "50000"))

eval_every = int(os.getenv("EVAL_EVERY", "10"))
save_every = int(os.getenv("SAVE_EVERY", "250"))

max_lr = float(os.getenv("MAX_LR", "3e-4"))
min_lr = float(os.getenv("MIN_LR", "3e-5"))
warmup = int(os.getenv("WARMUP", "300"))
accum_steps = int(os.getenv("ACCUM_STEPS", "4"))

train_path = os.getenv("TRAIN_PATH", "data/tokens_train.bin")
val_path = os.getenv("VAL_PATH", "data/tokens_val.bin")
checkpoint_dir = os.getenv("CHECKPOINT_DIR", "checkpoints")

os.makedirs(checkpoint_dir, exist_ok=True)

if device == "cuda":
    torch.set_float32_matmul_precision("high")
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
else:
    print("WARNING: CUDA not found. Training will run on CPU and will be very slow.", flush=True)


# -----------------------
# LOAD DATA
# -----------------------
if not os.path.exists(train_path):
    raise FileNotFoundError(f"Missing training file: {train_path}")

if not os.path.exists(val_path):
    raise FileNotFoundError(f"Missing validation file: {val_path}")

train_data = np.memmap(train_path, dtype=np.uint16, mode="r")
val_data = np.memmap(val_path, dtype=np.uint16, mode="r")

if len(train_data) <= block_size + 1:
    raise ValueError("Training data is too small for the selected block_size.")

if len(val_data) <= block_size + 1:
    raise ValueError("Validation data is too small for the selected block_size.")

print(f"train tokens: {len(train_data) / 1e9:.2f}B", flush=True)
print(f"val tokens:   {len(val_data) / 1e6:.2f}M", flush=True)

print(
    f"batch_size={batch_size}, block_size={block_size}, accum_steps={accum_steps}, "
    f"tokens/update={batch_size * block_size * accum_steps:,}",
    flush=True,
)


def get_batch(split):
    data = train_data if split == "train" else val_data
    ix = torch.randint(len(data) - block_size - 1, (batch_size,))

    x = torch.stack([
        torch.from_numpy(data[i:i + block_size].astype(np.int64, copy=True))
        for i in ix
    ])

    y = torch.stack([
        torch.from_numpy(data[i + 1:i + block_size + 1].astype(np.int64, copy=True))
        for i in ix
    ])

    if device == "cuda":
        x = x.pin_memory().to(device, non_blocking=True)
        y = y.pin_memory().to(device, non_blocking=True)
    else:
        x = x.to(device)
        y = y.to(device)

    return x, y


# -----------------------
# MODEL
# -----------------------
config = KyntoConfig(block_size=block_size)
model = Kynto(config).to(device)

total = sum(p.numel() for p in model.parameters()) / 1e6
print(f"kynto — {total:.1f}M parameters", flush=True)


# -----------------------
# OPTIMIZER
# -----------------------
decay_params = [p for n, p in model.named_parameters() if p.dim() >= 2]
nodecay_params = [p for n, p in model.named_parameters() if p.dim() < 2]

optimizer = torch.optim.AdamW(
    [
        {"params": decay_params, "weight_decay": 0.1},
        {"params": nodecay_params, "weight_decay": 0.0},
    ],
    lr=max_lr,
    betas=(0.9, 0.95),
    eps=1e-8,
)


# -----------------------
# LR SCHEDULE
# -----------------------
def get_lr(step):
    if step < warmup:
        return max_lr * (step + 1) / warmup

    decay = min(1.0, (step - warmup) / max(1, max_iters - warmup))

    return min_lr + 0.5 * (max_lr - min_lr) * (
        1 + math.cos(math.pi * decay)
    )


# -----------------------
# CHECKPOINTS
# -----------------------
def checkpoint_step(path):
    name = os.path.basename(path)
    match = re.search(r"step(\d+)\.pt$", name)

    if match:
        return int(match.group(1))

    return -1


def save_checkpoint(step, loss_accum):
    ckpt = {
        "step": step,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "loss": loss_accum,
        "config": config,
    }

    step_path = os.path.join(checkpoint_dir, f"kynto_step{step}.pt")
    latest_path = os.path.join(checkpoint_dir, "latest.pt")

    torch.save(ckpt, step_path)
    torch.save(ckpt, latest_path)

    print(f"✅ checkpoint saved: {step_path}", flush=True)


# -----------------------
# RESUME FROM LATEST CHECKPOINT
# -----------------------
start_step = 0

latest_path = os.path.join(checkpoint_dir, "latest.pt")
step_checkpoints = glob.glob(os.path.join(checkpoint_dir, "kynto_step*.pt"))

resume_path = None

if os.path.exists(latest_path):
    resume_path = latest_path
elif step_checkpoints:
    resume_path = max(step_checkpoints, key=checkpoint_step)

if resume_path:
    print(f"loading checkpoint: {resume_path}", flush=True)

    ckpt = torch.load(resume_path, map_location=device)

    model.load_state_dict(ckpt["model"])
    optimizer.load_state_dict(ckpt["optimizer"])

    # ✅ Start from next step so it does not repeat same checkpoint step
    start_step = int(ckpt["step"]) + 1

    print(f"resumed from {resume_path} at next step {start_step}", flush=True)
else:
    print("no checkpoint found, starting from step 0", flush=True)


# -----------------------
# TRAINING LOOP
# -----------------------
for step in range(start_step, max_iters):
    t0 = time.time()

    model.train()
    optimizer.zero_grad(set_to_none=True)

    loss_accum = 0.0

    for micro_step in range(accum_steps):
        xb, yb = get_batch("train")

        if device == "cuda":
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                logits, loss = model(xb, yb)
        else:
            logits, loss = model(xb, yb)

        loss = loss / accum_steps
        loss_accum += loss.item()

        loss.backward()

    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

    lr = get_lr(step)

    for g in optimizer.param_groups:
        g["lr"] = lr

    optimizer.step()

    if step % eval_every == 0:
        model.eval()

        with torch.no_grad():
            xb, yb = get_batch("val")

            if device == "cuda":
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    _, val_loss = model(xb, yb)
            else:
                _, val_loss = model(xb, yb)

        dt = time.time() - t0

        print(
            f"step {step:>6} | train {loss_accum:.4f} | "
            f"val {val_loss.item():.4f} | lr {lr:.2e} | {dt:.2f}s/step",
            flush=True,
        )

    if step % save_every == 0 and step > 0:
        save_checkpoint(step, loss_accum)


# -----------------------
# SAVE FINAL
# -----------------------
torch.save(model.state_dict(), "kynto.pt")
print("saved kynto.pt", flush=True)