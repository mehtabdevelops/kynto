import torch
import json
import tiktoken
from model import Kynto, KyntoConfig

device = 'mps'
enc = tiktoken.get_encoding('gpt2')
EOT = enc.eot_token

MAX_LEN = 512   # ✅ shorter to save memory

def build_example(user, assistant):
    prompt_part = f"<|user|>{user}\n<|assistant|>"
    answer_part = f"{assistant}"
    prompt_ids = enc.encode(prompt_part, allowed_special={"<|endoftext|>"})
    answer_ids = enc.encode(answer_part) + [EOT]
    input_ids = prompt_ids + answer_ids
    labels = [-100] * len(prompt_ids) + answer_ids
    return input_ids[:MAX_LEN], labels[:MAX_LEN]

config = KyntoConfig()
model = Kynto(config).to(device)
state = torch.load('kynto.pt', map_location=device, weights_only=False)
if isinstance(state, dict) and 'model' in state:
    state = state['model']
model.load_state_dict(state, strict=False)
print('base model loaded')

data = []
with open('data_sft/combined_sft.jsonl') as f:
    for line in f:
        try:
            ex = json.loads(line)
            m = ex['messages']
            inp, lab = build_example(m[0]['content'], m[1]['content'])
            if 5 < len(inp) <= MAX_LEN:   # ✅ skip too-long examples
                data.append((inp, lab))
        except:
            continue
print(f'loaded {len(data)} examples')

optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5)

model.train()
for epoch in range(3):
    total = 0
    for step, (inp, lab) in enumerate(data):
        x = torch.tensor(inp[:-1], dtype=torch.long).unsqueeze(0).to(device)
        y = torch.tensor(lab[1:], dtype=torch.long).unsqueeze(0).to(device)

        with torch.autocast(device_type='mps', dtype=torch.bfloat16):
            _, loss = model(x, y)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)   # ✅ frees memory
        total += loss.item()

        if step % 200 == 0:
            print(f'epoch {epoch} step {step}/{len(data)} loss {loss.item():.4f}')
            torch.mps.empty_cache()   # ✅ clear MPS cache

    print(f'epoch {epoch} avg loss {total/len(data):.4f}')
    torch.save(model.state_dict(), f'kynto_sft_epoch{epoch}.pt')

torch.save(model.state_dict(), 'kynto_sft.pt')
print('saved kynto_sft.pt')