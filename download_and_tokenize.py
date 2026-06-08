import tiktoken
import numpy as np
from datasets import load_dataset

enc = tiktoken.get_encoding('gpt2')

ds = load_dataset(
    'HuggingFaceFW/fineweb-edu',
    name='sample-10BT',
    split='train',
    streaming=True
)

fout_train = open('data/tokens_train.bin', 'wb')
fout_val   = open('data/tokens_val.bin', 'wb')

total = 0
for i, ex in enumerate(ds):
    tokens = enc.encode_ordinary(ex['text'])
    arr    = np.array(tokens, dtype=np.uint16)

    if i < 5000:
        arr.tofile(fout_val)
    else:
        arr.tofile(fout_train)

    total += len(tokens)
    if i % 10000 == 0:
        print(f'{i:,} docs | {total/1e9:.2f}B tokens')

    if i >= 3000000:
        break

fout_train.close()
fout_val.close()
print(f'done — {total/1e9:.2f}B total tokens')
