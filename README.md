# Kynto — 416M Parameter Language Model Trained From Scratch

Kynto is a custom language model built and trained from scratch using PyTorch.
The project started as a full pretraining experiment on general knowledge data and is now evolving into a cybersecurity-focused AI assistant with fine-tuning, LoRA training, agent systems, and security-domain knowledge.

This repository contains the source code, training scripts, generation script, fine-tuning scripts, and dataset preparation tools used to build Kynto.

> Note: Model weight files such as `kynto.pt`, `kynto_sft.pt`, and checkpoints are not pushed to GitHub because they are large files.

---

## Project Overview

Kynto was trained as a custom transformer-based language model with approximately:

```text
416.4M parameters
```

The model was trained in stages:

```text
Stage 1: Base language pretraining
Stage 2: Security data preparation
Stage 3: Security tokenization
Stage 4: LoRA supervised fine-tuning
Stage 5: Future full fine-tuning and agent integration
```

The main goal is to build a personal AI model that can later power:

```text
Cybersecurity agents
Website security monitoring
Code security review
CVE explanation
OWASP analysis
Log review
Encryption/security recommendations
Ethical hacking education
```

---

## Training Summary

### Base Model Training

The base Kynto model was trained from scratch on approximately:

```text
3.08B FineWeb-Edu tokens
```

Final base model training reached:

```text
step: 183,000
tokens: ~3.00B
final train loss: ~3.16
final val loss: ~3.00
```

The final base model was saved as:

```text
kynto.pt
```

Model size:

```text
~1.6GB
```

---

## Hardware Used

Training was performed on RunPod using high-end NVIDIA GPUs.

Example GPU used:

```text
NVIDIA H200
VRAM: ~140GB
```

The model trained at around:

```text
0.28 sec/step
```

With the training configuration:

```text
batch_size = 4
block_size = 1024
accum_steps = 4
tokens/update = 16,384
```

This means:

```text
183,000 steps × 16,384 tokens/update ≈ 3.0B tokens
```

---

## Base Training Process

The base model was trained on RunPod using:

```bash
cd /workspace/kynto

nohup python -u train.py > training_log.txt 2>&1 &
echo "PID: $!"
tail -f training_log.txt
```

Important training configuration inside `train.py`:

```python
batch_size = 4
block_size = 1024
max_iters = 183000
accum_steps = 4
max_lr = 1.5e-4
min_lr = 2e-5
save_every = 2500
```

The model automatically resumed from the latest numbered checkpoint:

```text
checkpoints/kynto_step*.pt
```

Example checkpoint:

```text
checkpoints/kynto_step182500.pt
```

The final model was saved as:

```text
kynto.pt
```

---

## Checkpoint Strategy

Each full training checkpoint was around:

```text
4.7GB
```

The final model-only file was around:

```text
1.6GB
```

During training, only the latest 1–2 checkpoints were kept to avoid storage issues.

Example cleanup command:

```bash
rm -f checkpoints/kynto_step177500.pt
rm -f checkpoints/kynto_step180000.pt
```

Recommended rule:

```text
Keep the latest checkpoint for future training.
Keep kynto.pt for inference.
Do not push .pt files to GitHub.
```

---

## Running the Model Locally

Create and activate a Python virtual environment:

```bash
python3 -m venv ai-env
source ai-env/bin/activate
```

Install dependencies:

```bash
python -m pip install torch tiktoken numpy
```

Run inference:

```bash
python generate.py
```

Example:

```text
You: What is cybersecurity?

Kynto:
Cybersecurity is the practice of protecting computer systems, networks, and data from unauthorized access, attacks, and damage...
```

---

## Security Dataset Collection

After base training, security and ethical hacking data was collected from public repositories and documentation.

Collected categories included:

```text
CVE and vulnerability data
OWASP documentation
CTF writeups
Bug bounty writeups
Penetration testing notes
Red team references
Blue team detection rules
Forensics tools
Cloud security tools
OSINT tools
Mobile security tools
```

Example repositories used:

```text
google/security-research
trickest/cve
OWASP/CheatSheetSeries
OWASP/wstg
daffainfo/AllAboutBugBounty
KathanP19/HowToHunt
ctf-wiki/ctf-wiki
Naetw/CTF-pwn-tips
apsdehal/awesome-ctf
orangetw/My-CTF-Web-Challenges
Neo23x0/sigma
elastic/detection-rules
volatilityfoundation/volatility3
nccgroup/ScoutSuite
prowler-cloud/prowler
MobSF/Mobile-Security-Framework-MobSF
offensive-security/exploitdb
danielmiessler/SecLists
carlospolop/PEASS-ng
```

Repositories were cloned using shallow clones where possible:

```bash
git clone --depth 1 <repo-url>
```

---

## Building the Security Corpus

The raw security repositories were converted into a cleaned JSONL dataset using:

```bash
python build_security_corpus.py
```

Output:

```text
data_security/clean/security_corpus.jsonl
```

Example final corpus size:

```text
security_corpus.jsonl: ~415MB+
documents: 183,000+
```

After adding more security data, the corpus reached:

```text
docs: 219,655
```

---

## Tokenizing Security Data

The cleaned security corpus was tokenized using:

```bash
python tokenize_security.py
```

Output files:

```text
data/security_tokens_train.bin
data/security_tokens_val.bin
```

Final tokenized security dataset:

```text
train tokens: 182,075,684
val tokens:     962,780
```

This gives approximately:

```text
182M security tokens
```

With:

```text
tokens/update = 16,384
```

One full pass over the security dataset is about:

```text
182,075,684 / 16,384 ≈ 11,113 steps
```

---

## Security Fine-Tuning Plan

The base model already has:

```text
3B general training tokens
```

The security dataset adds:

```text
182M cybersecurity tokens
```

Recommended fine-tuning strategy:

```text
1 pass  ≈ 182M security tokens
3 passes ≈ 546M security-token exposure
```

A safe fine-tuning target:

```text
Base completed at: 183,000 steps
Security 3-pass target: around 216,500 steps
```

Example command:

```bash
MAX_ITERS=216500 \
TRAIN_PATH=data/security_tokens_train.bin \
VAL_PATH=data/security_tokens_val.bin \
MAX_LR=8e-5 \
MIN_LR=2e-5 \
SAVE_EVERY=2500 \
nohup python -u train.py > security_training_log.txt 2>&1 &
```

---

## LoRA Fine-Tuning

LoRA fine-tuning was used to make the model better at instruction following without training all 416M parameters.

Example LoRA training stats:

```text
trainable params: 1,277,952
all params: 417,695,744
trainable%: 0.3060
```

This means only about:

```text
0.3% of the model
```

was trained during LoRA fine-tuning.

Run LoRA SFT:

```bash
nohup python -u sft_lora.py > sft_log.txt 2>&1 &
echo "PID: $!"
tail -f sft_log.txt
```

Example healthy training loss:

```text
epoch 1 step 43600/137001 loss 1.4672
epoch 1 step 44000/137001 loss 1.1895
epoch 1 step 45400/137001 loss 1.2658
```

LoRA checkpoint examples:

```text
kynto_sft_lora_step50000.pt
kynto_sft_lora_step100000.pt
```

Final fine-tuned model:

```text
kynto_sft.pt
```

---

## Model Versions

Recommended model version strategy:

```text
kynto.pt                      = original 3B base model
kynto_sft.pt                  = fine-tuned assistant model
kynto_sft_lora_step50000.pt   = LoRA checkpoint backup
kynto_sft_lora_step100000.pt  = newer LoRA checkpoint backup
kynto_sft_v2.pt               = future full fine-tuned model
```

For normal chatting, use the newest stable fine-tuned model:

```python
MODEL_PATH = "kynto_sft.pt"
```

If the fine-tuned model behaves badly, fall back to:

```python
MODEL_PATH = "kynto.pt"
```

---

## Future Agent Network

Kynto is planned to support a multi-agent cybersecurity system.

Planned agents:

```text
Recon Agent
CVE Agent
OWASP Agent
Log Analysis Agent
Code Review Agent
Dependency Vulnerability Agent
Encryption Agent
Report Agent
Patch Suggestion Agent
Human Approval Agent
```

The future goal is to build:

```text
Kynto Security Agent Network
```

A 24/7 AI-powered security monitoring and analysis system for websites, applications, and infrastructure.

Important safety design:

```text
Agents should monitor, report, and suggest fixes.
Risky actions should require human approval.
The system should only be used on owned or authorized targets.
```

---

## Important Safety Note

Kynto is intended for ethical cybersecurity education, defensive security, secure coding, vulnerability analysis, and authorized testing only.

This project should not be used for:

```text
Unauthorized access
Credential theft
Malware deployment
Phishing
Ransomware
Botnets
Attacking systems without permission
```

The long-term goal is to build a responsible cybersecurity assistant that helps users understand, detect, and fix security issues.

---

## Current Status

Completed:

```text
Built model architecture
Trained 416M model from scratch
Completed 3B-token FineWeb-Edu pretraining
Saved final base model as kynto.pt
Collected public cybersecurity data
Built security corpus JSONL
Tokenized security corpus
Started LoRA SFT
Generated LoRA checkpoints
```

In progress:

```text
Instruction tuning
Security specialization
Agent network architecture
Better chat behavior
Versioned model releases
```

Planned:

```text
Kynto v1: base model
Kynto v2: instruction-tuned model
Kynto v3: cybersecurity specialist
Kynto v4: multi-agent security assistant
Kynto v5: RAG + internet knowledge + monitoring tools
```

---

## Notes for GitHub

Do not push large files:

```text
*.pt
checkpoints/
data/*.bin
data_security/raw/
data_security/clean/
training logs
```

Large files should be stored externally, such as:

```text
RunPod volume
Google Drive
Hugging Face model repository
External object storage
```

Recommended files to keep in GitHub:

```text
model.py
train.py
generate.py
sft_lora.py
sft_train.py
build_security_corpus.py
tokenize_security.py
agents/
README.md
```

---

## Author

Built by Mehtab Warn as a custom AI language model and cybersecurity assistant project.

Kynto is a from-scratch AI model experiment focused on learning, research, cybersecurity, and building practical AI agents.


~MEHTAB WARN FELL FREE TO USE THE REPO

