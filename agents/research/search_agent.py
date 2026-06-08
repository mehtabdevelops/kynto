# agents/research/search_agent.py
import requests
from agents.base_agent import BaseAgent

class WebSearchAgent(BaseAgent):
    name = "web_searcher"
    description = "Searches the web for latest security information"
    
    def can_handle(self, query: str) -> bool:
        search_kw = ['latest', 'recent', 'news', 'today', 'current', 
                     '2024', '2025', 'search', 'find']
        return any(kw in query.lower() for kw in search_kw)
    
    def search(self, query: str) -> str:
        try:
            # use DuckDuckGo instant answer API (free, no key)
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json", "no_html": 1}
            r = requests.get(url, params=params, timeout=5)
            data = r.json()
            
            results = []
            if data.get('AbstractText'):
                results.append(data['AbstractText'])
            for topic in data.get('RelatedTopics', [])[:3]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append(topic['Text'])
            
            return '\n'.join(results[:3]) if results else ""
        except:
            return ""
    
    def process(self, query: str, context: str = "") -> str:
        web_context = self.search(query)
        prompt = f"""<|user|>You are Kynto security researcher.
{f'Web search results: {web_context}' if web_context else ''}
Question: {query}
<|assistant|>"""
        return self._generate(prompt, max_tokens=400)


class SummarizeAgent(BaseAgent):
    name = "summarizer"
    description = "Summarizes security documents and reports"
    
    def can_handle(self, query: str) -> bool:
        return any(kw in query.lower() for kw in 
                   ['summarize', 'summary', 'tldr', 'brief', 'explain'])
    
    def process(self, query: str, context: str = "") -> str:
        prompt = f"""<|user|>Provide a clear, concise summary of:
{query}
<|assistant|>"""
        return self._generate(prompt, max_tokens=300)