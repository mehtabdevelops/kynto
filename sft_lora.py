import torch
import json
import tiktoken
from peft import get_peft_model, LoraConfig, TaskType
from model import Kynto, KyntoConfig

device = 'cuda'
enc    = tiktoken.get_encoding('gpt2')
EOT    = enc.eot_token
MAX_LEN = 256   # very short to save memory

def build_example(user, assistant):
    prompt_ids = enc.encode(f"<|user|>{user}\n<|assistant|>", allowed_special={"<|endoftext|>"})
    answer_ids = enc.encode(assistant) + [EOT]
    inp = prompt_ids + answer_ids
    lab = [-100] * len(prompt_ids) + answer_ids
    return inp[:MAX_LEN], lab[:MAX_LEN]

# load base model
config = KyntoConfig()
model  = Kynto(config).to(device)
state  = torch.load('kynto.pt', map_location=device, weights_only=False)
if isinstance(state, dict) and 'model' in state:
    state = state['model']
model.load_state_dict(state, strict=False)

# ✅ freeze most params — only train LoRA adapters
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],   # only attention projections
    lora_dropout=0.05,
    bias="none",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# should show: ~0.5% trainable parameters

# load data
data = []
with open('data_sft/combined_sft.jsonl') as f:
    for line in f:
        try:
            ex  = json.loads(line)
            m   = ex['messages']
            inp, lab = build_example(m[0]['content'], m[1]['content'])
            if 5 < len(inp) <= MAX_LEN:
                data.append((inp, lab))
        except:
            continue
print(f'loaded {len(data)} examples')

optimizer = torch.optim.AdamW(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=3e-4   # higher LR ok for LoRA
)

model.train()
for epoch in range(3):
    total = 0
    for step, (inp, lab) in enumerate(data):
        x = torch.tensor(inp[:-1], dtype=torch.long).unsqueeze(0).to(device)
        y = torch.tensor(lab[1:], dtype=torch.long).unsqueeze(0).to(device)

        with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
            _, loss = model(x, y)

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        total += loss.item()

        if step % 200 == 0:
            print(f'epoch {epoch} step {step}/{len(data)} loss {loss.item():.4f}')
            torch.cuda.empty_cache()

    print(f'epoch {epoch} avg loss {total/len(data):.4f}')

# save merged model
model = model.merge_and_unload()   # merge LoRA back into base weights
torch.save(model.state_dict(), 'kynto_sft.pt')
print('saved kynto_sft.pt')