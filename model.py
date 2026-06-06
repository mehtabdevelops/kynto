from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F


# -----------------------
# CONFIG
# -----------------------
@dataclass
class KyntoConfig:
    block_size: int = 1024
    vocab_size: int = 50257

    n_embd:    int = 1280
    n_head:    int = 16
    n_kv_head: int = 4
    n_layer:   int = 36

    dropout: float = 0.0
    bias:    bool  = False


# -----------------------
# ROPE
# -----------------------
def precompute_rope(head_dim, block_size, device, theta=10000.0):
    freqs = 1.0 / (
        theta ** (torch.arange(0, head_dim, 2, device=device).float() / head_dim)
    )
    pos   = torch.arange(block_size, device=device).float()
    freqs = torch.outer(pos, freqs)
    return torch.cos(freqs), torch.sin(freqs)


def apply_rope(x, cos, sin):
    B, H, T, D = x.shape
    cos = cos[:T].unsqueeze(0).unsqueeze(0)
    sin = sin[:T].unsqueeze(0).unsqueeze(0)
    x1  = x[..., ::2]
    x2  = x[..., 1::2]
    out1 = x1 * cos - x2 * sin
    out2 = x1 * sin + x2 * cos
    return torch.stack([out1, out2], dim=-1).flatten(-2)


# -----------------------
# RMSNORM
# -----------------------
class RMSNorm(nn.Module):
    def __init__(self, dim, eps=1e-6):
        super().__init__()
        self.eps   = eps
        self.scale = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = x.pow(2).mean(-1, keepdim=True).clamp(min=self.eps)
        return x * torch.rsqrt(norm) * self.scale


# -----------------------
# ATTENTION (GQA)
# -----------------------
class MultiheadAttention(nn.Module):
    def __init__(self, config: KyntoConfig):
        super().__init__()
        assert config.n_embd % config.n_head == 0

        self.n_head    = config.n_head
        self.n_kv_head = config.n_kv_head
        self.head_dim  = config.n_embd // config.n_head
        self.dropout   = config.dropout

        self.q_proj = nn.Linear(config.n_embd, config.n_head    * self.head_dim, bias=config.bias)
        self.k_proj = nn.Linear(config.n_embd, config.n_kv_head * self.head_dim, bias=config.bias)
        self.v_proj = nn.Linear(config.n_embd, config.n_kv_head * self.head_dim, bias=config.bias)
        self.c_proj = nn.Linear(config.n_embd, config.n_embd,                    bias=config.bias)
        self.c_proj.KYNTO_SCALE_INIT = 1  # ✅

        cos, sin = precompute_rope(self.head_dim, config.block_size, device="cpu")
        self.register_buffer("cos", cos)
        self.register_buffer("sin", sin)

    def forward(self, x):
        B, T, C = x.shape

        q = self.q_proj(x).view(B, T, self.n_head,    self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(B, T, self.n_kv_head, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(B, T, self.n_kv_head, self.head_dim).transpose(1, 2)

        q = apply_rope(q, self.cos, self.sin)
        k = apply_rope(k, self.cos, self.sin)

        groups = self.n_head // self.n_kv_head
        k = k.repeat_interleave(groups, dim=1)
        v = v.repeat_interleave(groups, dim=1)

        y = F.scaled_dot_product_attention(
            q, k, v,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=True
        )

        y = y.transpose(1, 2).contiguous().view(B, T, C)
        y = self.c_proj(y)
        y = F.dropout(y, p=self.dropout, training=self.training)
        return y


# -----------------------
# MLP (SwiGLU)
# -----------------------
class MLP(nn.Module):
    def __init__(self, config: KyntoConfig):
        super().__init__()
        hidden     = 4 * config.n_embd
        self.gate  = nn.Linear(config.n_embd, hidden,        bias=config.bias)
        self.up    = nn.Linear(config.n_embd, hidden,        bias=config.bias)
        self.down  = nn.Linear(hidden,        config.n_embd, bias=config.bias)
        self.down.KYNTO_SCALE_INIT = 1  # ✅
        self.dropout = config.dropout

    def forward(self, x):
        x = F.silu(self.gate(x)) * self.up(x)
        x = self.down(x)
        return F.dropout(x, p=self.dropout, training=self.training)


# -----------------------
# TRANSFORMER BLOCK
# -----------------------
class Block(nn.Module):
    def __init__(self, config: KyntoConfig):
        super().__init__()
        self.ln_1 = RMSNorm(config.n_embd)
        self.ln_2 = RMSNorm(config.n_embd)
        self.attn = MultiheadAttention(config)
        self.mlp  = MLP(config)

    def forward(self, x):
        x = x + self.attn(self.ln_1(x))
        x = x + self.mlp(self.ln_2(x))
        return x


# -----------------------
# MODEL
# -----------------------
class Kynto(nn.Module):
    def __init__(self, config: KyntoConfig):
        super().__init__()
        self.config = config

        self.transformer = nn.ModuleDict(dict(
            wte  = nn.Embedding(config.vocab_size, config.n_embd),
            drop = nn.Dropout(config.dropout),
            h    = nn.ModuleList([Block(config) for _ in range(config.n_layer)]),
            ln_f = RMSNorm(config.n_embd),
        ))

        self.lm_head = nn.Linear(config.n_embd, config.vocab_size, bias=False)
        self.lm_head.weight = self.transformer.wte.weight  # weight tying

        self.apply(self._init_weights)

    def _init_weights(self, module):
        std = 0.02
        if isinstance(module, nn.Linear):
            if hasattr(module, 'KYNTO_SCALE_INIT'):
                std *= (2 * self.config.n_layer) ** -0.5  # ✅ scaled init
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=std)

    def forward(self, idx, targets=None):
        B, T = idx.size()
        assert T <= self.config.block_size

        x = self.transformer.drop(self.transformer.wte(idx))

        for block in self.transformer.h:
            x = block(x)

        x      = self.transformer.ln_f(x)
        logits = self.lm_head(x)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                targets.view(-1)
            )

        return logits, loss