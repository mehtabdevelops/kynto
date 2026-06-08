# agents/base_agent.py
import torch
import tiktoken
from abc import ABC, abstractmethod
from typing import Optional

class BaseAgent(ABC):
    """
    Base class for all Kynto agents.
    Every agent has a name, description, and can process a query.
    """
    
    name: str = "base"
    description: str = "Base agent"
    
    def __init__(self, model, config, device='mps'):
        self.model  = model
        self.config = config
        self.device = device
        self.enc    = tiktoken.get_encoding('gpt2')
    
    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """Returns True if this agent should handle the query"""
        pass
    
    @abstractmethod  
    def process(self, query: str, context: str = "") -> str:
        """Process the query and return response"""
        pass
    
    def _generate(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.3,
    ) -> str:
        self.model.eval()
        tokens = self.enc.encode(prompt, allowed_special={"<|endoftext|>"})
        idx = torch.tensor(tokens, dtype=torch.long, device=self.device).unsqueeze(0)
        prompt_len = idx.size(1)
        
        with torch.no_grad():
            for _ in range(max_tokens):
                idx_cond = idx[:, -self.config.block_size:]
                logits, _ = self.model(idx_cond)
                logits = logits[:, -1, :]
                
                # repetition penalty
                seen = set(idx[0].tolist())
                for tid in seen:
                    if logits[0, tid] > 0:
                        logits[0, tid] /= repetition_penalty
                    else:
                        logits[0, tid] *= repetition_penalty
                
                logits = logits / temperature
                if top_k > 0:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = -float('inf')
                
                probs   = torch.softmax(logits, dim=-1)
                next_id = torch.multinomial(probs, 1)
                idx = torch.cat([idx, next_id], dim=1)
                
                if next_id.item() == self.enc.eot_token:
                    break
        
        return self.enc.decode(idx[0, prompt_len:].tolist()).strip()