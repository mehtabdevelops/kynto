import torch
import numpy as np
import math
import os
from model import Kynto, KyntoConfig

# config
device     = 'cuda'
batch_size = 32
block_size = 1024
max_iters  = 10000
eval_every = 250
max_lr     = 3e-4
min_lr     = 3e-5
warmup     = 300
accum_steps = 8

os.makedirs('checkpoints', exist_ok=True)

# load binary data
train_data = np.memmap('data/tokens_train.bin', dtype=np.uint16, mode='r')
val_data   = np.memmap('data/tokens_val.bin',   dtype=np.uint16, mode='r')

print(f'train tokens: {len(train_data)/1e9:.2f}B')
print(f'val tokens:   {len(val_data)/1e6:.2f}M')

def get_batch(split):
    data = train_data if split == 'train' else val_data
    ix   = torch.randint(len(data) - block_size, (batch_size,))
    x    = torch.stack([torch.from_numpy(data[i:i+block_size].astype(np.int64))     for i in ix])
    y    = torch.stack([torch.from_numpy(data[i+1:i+block_size+1].astype(np.int64)) for i in ix])
    return x.to(device), y.to(device)

# model
config = KyntoConfig()
model  = Kynto(config).to(device)
model =model.to(torch.float16)
total  = sum(p.numel() for p in model.parameters()) / 1e6
print(f'kynto — {total:.1f}M parameters')

# optimizer
decay_params   = [p for n, p in model.named_parameters() if p.dim() >= 2]
nodecay_params = [p for n, p in model.named_parameters() if p.dim() < 2]
optimizer = torch.optim.AdamW([
    {'params': decay_params,   'weight_decay': 0.1},
    {'params': nodecay_params, 'weight_decay': 0.0}
], lr=max_lr, betas=(0.9, 0.95), eps=1e-8)

# resume from checkpoint if exists
def get_lr(step):
    if step < warmup:
        return max_lr * step / warmup
    decay = (step - warmup) / (max_iters - warmup)
    return min_lr + 0.5 * (max_lr - min_lr) * (1 + math.cos(math.pi * decay))


start_step = 0
latest = [f for f in os.listdir('checkpoints') if f.endswith('.pt')]
if latest:
    ckpt = torch.load(f'checkpoints/{latest[-1]}', map_location=device)
    model.load_state_dict(ckpt['model'])
    optimizer.load_state_dict(ckpt['optimizer'])
    start_step = ckpt['step']
    print(f'resumed from {latest[-1]} at step {start_step}')

# training loop
for step in range(start_step, max_iters):
    model.train()
    optimizer.zero_grad()
    loss_accum = 0.0

    for micro_step in range(accum_steps):              # ✅ grad accumulation
        xb, yb = get_batch('train')
        with torch.autocast(device_type='cuda', dtype=torch.bfloat16):  # ✅ bf16
            logits, loss = model(xb, yb)
        loss = loss / accum_steps
        loss_accum += loss.item()
        loss.backward()

    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

    lr = get_lr(step)
    for g in optimizer.param_groups:
        g['lr'] = lr

    optimizer.step()

    if step % eval_every == 0:
        model.eval()
        with torch.no_grad():
            with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                _, val_loss = model(*get_batch('val'))
        print(f'step {step:>6} | train {loss_accum:.4f} | val {val_loss.item():.4f} | lr {lr:.2e}')

    if step % 1000 == 0 and step > 0:
        torch.save({
            'step':      step,
            'model':     model.state_dict(),
            'optimizer': optimizer.state_dict(),
            'loss':      loss_accum,
        }, f'checkpoints/kynto_step{step}.pt')
        print(f'✅ checkpoint saved at step {step}')

# -----------------------
# SAVE FINAL
# -----------------------
torch.save(model.state_dict(), 'kynto.pt')
print('saved kynto.pt')