import json
from openai import OpenAI
from lib.database import Database
from lib.terminal import Terminal

class Core:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.client = OpenAI(
            api_key=self.config['openai']['api_key'],
            base_url=self.config['openai']['base_url']
        )
        
        self.database = Database()
        self.terminal = Terminal()
    
    def get_chat_response(self, user_input):
        context = self.database.get_context()
        memory = self.database.get_memory()
        
        messages = [
            {"role": "system", "content": self.config['system_prompt']},
            {"role": "system", "content": f"Memory: {memory}"}
        ] + context + [
            {"role": "user", "content": user_input}
        ]
        
        response = self.client.chat.completions.create(
            model=self.config['openai']['model'],
            messages=messages
        )
        
        assistant_response = response.choices[0].message.content
        self.database.add_to_context("user", user_input)
        self.database.add_to_context("assistant", assistant_response)
        
        return assistant_response
    
    def execute_command(self, command):
        return self.terminal.execute(command)
    
    def summarize_context(self):
        context = self.database.get_context()
        if not context:
            return "No context to summarize."
        
        messages = [
            {"role": "system", "content": "Please summarize the following conversation in a concise way."},
            {"role": "user", "content": str(context)}
        ]
        
        response = self.client.chat.completions.create(
            model=self.config['openai']['model'],
            messages=messages
        )
        
        summary = response.choices[0].message.content
        self.database.summarize_context(summary)
        return summary
    
    def clear_context(self):
        self.database.clear_context()
        return "Context cleared."
    
    def add_to_memory(self, content):
        self.database.add_to_memory(content)
        return "Added to memory."