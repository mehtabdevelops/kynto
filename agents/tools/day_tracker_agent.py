# agents/tools/day_tracker_agent.py
import json
import os
from datetime import datetime
from agents.base_agent import BaseAgent

TASKS_FILE = "data/tasks.json"

class DayTrackerAgent(BaseAgent):
    name = "day_tracker"
    description = "Manages tasks, schedule, and daily productivity"
    
    def __init__(self, model, config, device='mps'):
        super().__init__(model, config, device)
        self.tasks = self._load_tasks()
    
    def _load_tasks(self):
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE) as f:
                return json.load(f)
        return {"tasks": [], "schedule": []}
    
    def _save_tasks(self):
        os.makedirs("data", exist_ok=True)
        with open(TASKS_FILE, 'w') as f:
            json.dump(self.tasks, f, indent=2)
    
    def can_handle(self, query: str) -> bool:
        day_kw = ['task', 'todo', 'schedule', 'remind', 'plan', 
                  'today', 'tomorrow', 'meeting', 'deadline', 'add task']
        return any(kw in query.lower() for kw in day_kw)
    
    def add_task(self, task: str, priority: str = "medium"):
        self.tasks["tasks"].append({
            "task": task,
            "priority": priority,
            "done": False,
            "created": datetime.now().isoformat()
        })
        self._save_tasks()
        return f"✅ Task added: {task}"
    
    def list_tasks(self):
        if not self.tasks["tasks"]:
            return "No tasks yet!"
        pending = [t for t in self.tasks["tasks"] if not t["done"]]
        result = f"📋 Tasks ({len(pending)} pending):\n"
        for i, t in enumerate(pending, 1):
            result += f"{i}. [{t['priority'].upper()}] {t['task']}\n"
        return result
    
    def process(self, query: str, context: str = "") -> str:
        q = query.lower()
        
        if any(kw in q for kw in ['add', 'create', 'new task']):
            task = query.replace('add task', '').replace('add', '').strip()
            return self.add_task(task)
        
        if any(kw in q for kw in ['list', 'show', 'what', 'tasks']):
            return self.list_tasks()
        
        prompt = f"""<|user|>You are Kynto day planner assistant.
Current tasks: {json.dumps(self.tasks['tasks'][:5])}
User request: {query}
<|assistant|>"""
        return self._generate(prompt, max_tokens=200)