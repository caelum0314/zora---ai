import json
import os

class Database:
    def __init__(self, context_file="database/context.json", memory_file="home/MEMORY.md"):
        self.context_file = context_file
        self.memory_file = memory_file
        self._ensure_files()
    
    def _ensure_files(self):
        if not os.path.exists(self.context_file):
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        
        if not os.path.exists(self.memory_file):
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                f.write("# Memory\n\n")
    
    def get_context(self):
        with open(self.context_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def add_to_context(self, role, content):
        context = self.get_context()
        context.append({"role": role, "content": content})
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
    
    def clear_context(self):
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    def get_memory(self):
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def add_to_memory(self, content):
        with open(self.memory_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{content}\n")
    
    def summarize_context(self, summary):
        self.clear_context()
        self.add_to_context("system", f"Previous conversation summary: {summary}")