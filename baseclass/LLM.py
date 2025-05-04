import os
from openai import OpenAI, AzureOpenAI
import json
# export AZURE_OPENAI_API_KEY="d56bd868ff56401595c6e74357c02f04"
# export AZURE_OPENAI_API_BASE="https://yaolun-west.openai.azure.com/"
class LLM():
    def __init__(self, system_prompt="You are a helpful assistant", use_azure=True):
        self.use_azure = use_azure
        if self.use_azure:
            self.client = AzureOpenAI(
                api_key="d56bd868ff56401595c6e74357c02f04",
                #os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint="https://yaolun-west.openai.azure.com/",
                #os.getenv("AZURE_OPENAI_API_BASE"),
                api_version="2024-07-01-preview"
                #os.getenv("API_VERSION")
            )
        else:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                #base_url=os.getenv("OPENAI_API_BASE")
            )
        self.messages = [{"role": "system", "content": system_prompt}]
        self.system_prompt = system_prompt
        self.token_cost = 0

    def chat(self, message, temperature=0.2,model="gpt-4o"):
        self.messages.append({"role": "user", "content": message})
        if self.use_azure:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                messages=self.messages,
                    temperature=temperature,
                    timeout = 30
                )
            except Exception as e:
                print(self.messages[-1])
                print(e)
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.messages,
                    temperature=temperature
                )
        else:
            response = self.client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=self.messages,
                temperature=temperature
            )
        rsp = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": rsp})
        self.token_cost += response.usage.total_tokens
        return rsp

    def add_message(self, message):
        self.messages.append({"role": "user", "content": message})

    def add_tool_message(self, message):
        self.messages.append({"role": "user", "content": "[INFO] This is a tool message:\n" + message})

    def get_whole_message(self):
        return self.messages

    def get_token_cost(self):
        return self.token_cost

    def recount_token(self):
        self.token_cost = 0