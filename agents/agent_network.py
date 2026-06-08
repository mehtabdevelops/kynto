# agents/agent_network.py
import torch
from model import Kynto, KyntoConfig
from agents.rag import SecurityRAG
from agents.security.vulnerability_agent import (
    VulnerabilityAgent, CVEAgent, PentestAgent, CodeAuditAgent
)
from agents.research.search_agent import WebSearchAgent, SummarizeAgent
from agents.tools.day_tracker_agent import DayTrackerAgent
from agents.tools.memory_agent import MemoryAgent

class KyntoAgentNetwork:
    """
    Routes queries to the most appropriate agent.
    Falls back to general Kynto response if no agent matches.
    """
    
    def __init__(self, model_path='kynto.pt', device=None):
        if device is None:
            if torch.cuda.is_available():
                device = 'cuda'
            elif torch.backends.mps.is_available():
                device = 'mps'
            else:
                device = 'cpu'
        
        self.device = device
        print(f"Loading Kynto on {device}...")
        
        self.config = KyntoConfig()
        self.model  = Kynto(self.config).to(device)
        state = torch.load(model_path, map_location=device, weights_only=False)
        if isinstance(state, dict) and 'model' in state:
            state = state['model']
        self.model.load_state_dict(state, strict=False)
        self.model.eval()
        print("✅ Kynto loaded!")
        
        # init RAG
        self.rag = SecurityRAG()
        
        # init all agents
        args = (self.model, self.config, device)
        self.memory    = MemoryAgent(*args)
        self.day       = DayTrackerAgent(*args)
        self.agents    = [
            CVEAgent(*args),
            CodeAuditAgent(*args),
            PentestAgent(*args),
            VulnerabilityAgent(*args),
            WebSearchAgent(*args),
            SummarizeAgent(*args),
            self.day,
            self.memory,
        ]
        
        print(f"✅ {len(self.agents)} agents ready!")
    
    def route(self, query: str) -> tuple:
        """Find best agent for query"""
        for agent in self.agents:
            if agent.can_handle(query):
                return agent, agent.name
        return None, "general"
    
    def chat(self, query: str) -> str:
        # recall memory context
        memory_context = self.memory.recall(query)
        
        # get RAG context for security queries
        rag_context = self.rag.format_context(query)
        
        context = "\n".join(filter(None, [memory_context, rag_context]))
        
        # route to best agent
        agent, agent_name = self.route(query)
        
        if agent:
            print(f"[{agent_name}] handling query...")
            response = agent.process(query, context)
        else:
            # general response
            import tiktoken
            enc = tiktoken.get_encoding('gpt2')
            prompt = f"""<|user|>{f'Context: {context}' if context else ''}{query}
<|assistant|>"""
            tokens = enc.encode(prompt, allowed_special={"<|endoftext|>"})
            idx = torch.tensor(tokens, dtype=torch.long, 
                             device=self.device).unsqueeze(0)
            prompt_len = len(tokens)
            
            with torch.no_grad():
                for _ in range(300):
                    logits, _ = self.model(idx[:, -1024:])
                    logits = logits[:, -1, :] / 0.7
                    probs = torch.softmax(logits, dim=-1)
                    next_id = torch.multinomial(probs, 1)
                    idx = torch.cat([idx, next_id], dim=1)
                    if next_id.item() == enc.eot_token:
                        break
            
            response = enc.decode(idx[0, prompt_len:].tolist()).strip()
        
        # save to memory
        self.memory.add_conversation(query, response)
        
        return response


# -----------------------
# CLI chat
# -----------------------
if __name__ == "__main__":
    network = KyntoAgentNetwork()
    print("\nKynto Security Agent Network")
    print("Agents: vulnerability, cve, pentest, code audit, search, summarize, tasks, memory")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            user = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        
        if not user:
            continue
        if user.lower() in ['exit', 'quit']:
            break
        
        response = network.chat(user)
        print(f"\nKynto: {response}\n")
        print("=" * 60 + "\n")