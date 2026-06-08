# agents/tools/memory_agent.py
import json
import os
from agents.base_agent import BaseAgent

MEMORY_FILE = "data/memory.json"

class MemoryAgent(BaseAgent):
    name = "memory"
    description = "Remembers past conversations and user preferences"
    
    def __init__(self, model, config, device='mps'):
        super().__init__(model, config, device)
        self.memory = self._load()
    
    def _load(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE) as f:
                return json.load(f)
        return {"conversations": [], "facts": {}}
    
    def _save(self):
        os.makedirs("data", exist_ok=True)
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def remember(self, key: str, value: str):
        self.memory["facts"][key] = value
        self._save()
    
    def recall(self, query: str) -> str:
        facts = self.memory.get("facts", {})
        relevant = []
        for k, v in facts.items():
            if any(word in k.lower() for word in query.lower().split()):
                relevant.append(f"{k}: {v}")
        return "\n".join(relevant[:5]) if relevant else ""
    
    def add_conversation(self, user: str, assistant: str):
        self.memory["conversations"].append({
            "user": user,
            "assistant": assistant
        })
        # keep last 50 conversations
        self.memory["conversations"] = self.memory["conversations"][-50:]
        self._save()
    
    def can_handle(self, query: str) -> bool:
        return any(kw in query.lower() for kw in 
                   ['remember', 'recall', 'forget', 'memory', 'what did'])
    
    def process(self, query: str, context: str = "") -> str:
        recalled = self.recall(query)
        prompt = f"""<|user|>You are Kynto memory assistant.
{f'Recalled memories: {recalled}' if recalled else ''}
{query}
<|assistant|>"""
        return self._generate(prompt, max_tokens=200)