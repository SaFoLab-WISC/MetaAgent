import os
from openai import OpenAI
import json
import sys

from baseclass.LLM import LLM
from tools import TOOL_MAPPING

class MultiAgentSystem:
    def __init__(self, agents_json, states_json):
        self.agents = {agent['agent_id']: agent for agent in agents_json}
        self.states = {state['state_id']: state for state in states_json['states']}
        self.transitions = states_json['transitions']
        #print("Transitions:\n",self.transitions,"\n======")
        self.listeners = {state['state_id']: state.get('listener', []) for state in states_json['states']}
        self.agents_json = agents_json
        self.states_json = states_json
        self.llms = {}
        self.initialize_agents()
        self.codeinterpreter = TOOL_MAPPING['execute_code']
        self.file_writer = '''
        When you want to write the result to a file, use the following format:
    <file_write>
    FILE_PATH: <the path to the file you want to write to>
    CONTENT:
    <the content you want to write to the file>
    <\\file_write>

    Here is an example:
    <file_write>
    FILE_PATH: game.py
    CONTENT:
    import pygame
    import sys

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption('My Game')

    # Game loop
    <\\file_write>
    '''
        self.running_log = ""
        self.current_state_id = None  # 添加当前状态id

    def reset(self):
        self.llms = {}
        self.initialize_agents()

    def initialize_agents(self):
        for agent_id, agent in self.agents.items():
            updated_agent = self.update_system_prompt(agent)
            #print("=========check agent==========",agent_id,updated_agent,"\n==========")
            self.llms[agent_id] = LLM(system_prompt=updated_agent['system_prompt'], use_azure=True)

    def update_system_prompt(self, agent):
        tools_description = ""
        if agent.get('tools'):
            tools_description = " You can use the following tools:\n"
            for tool in agent['tools']:
                if tool == "code_interpreter":
                    tools_description += f"- {tool}: Use it with <execute>```python <Your Code> ```<\\execute>. and you will got the stdout or error message\n WARNING: 1. Thses enironment is not a jupyter notebook. Please use print(df.head()) instead of df.head(), other jupyer outputs  also need print out. 2. Put the code you want to execute in only one snippet!!!  "
                if tool == "search_engine":
                    tools_description += '''- search_engine: Use it with <execute>```python 
                    import json
                    import os
                    import requests
                os.environ['BING_SEARCH_V7_SUBSCRIPTION_KEY']="e5ac2ebcba064af1830740a2a270fb74"
                subscription_key = os.environ['BING_SEARCH_V7_SUBSCRIPTION_KEY']
                endpoint = "https://api.bing.microsoft.com/v7.0/search"
                # Query term(s) to search for.
                queries = ["Insert your query list here"]

                headers = { 'Ocp-Apim-Subscription-Key': subscription_key }
                # Call the API
                for query in queries:
                    try:
                        params = { 'q': query }
                        response = requests.get(endpoint, headers=headers, params=params)
                        response.raise_for_status()
                        print("The search results are:")
                        print(response.json()['webPages']['value'][0]['snippet'])
                    except Exception as ex:
                        raise ex
                    ```<\\execute>. and you will got the search result
                    WARNING: 1. Thses enironment is not a jupyter notebook. Please use print(df.head()) instead of df.head(), other jupyer outputs  also need print out. 2. Put the code you want to execute in only one snippet!!!'''
    
        transition_conditions = ""
        for transition in self.transitions:
            if transition['from_state'] in self.states and self.states[transition['from_state']]['agent_id'] == agent['agent_id']:
                transition_conditions += f"- If {transition['condition']}, output `<STATE_TRANS>: {transition['to_state']}`.\n"

        transition_conditions += "- If no conditions are met, output `<STATE_TRANS>: None`.\n DO NOT WRITE THIS IN THE CODE SNIPPET!"

        agent['system_prompt'] += tools_description + "\n" + transition_conditions
        #agent['system_prompt'] += "\nWhen transitioning state, format the information for the next agent as <INFO>xxxx</INFO> and specify the next agent's role."
        #print(agent)
        return agent

    def get_next_state(self, current_state, output):
        for transition in self.transitions:
            if transition['from_state'] == current_state and f"<STATE_TRANS>: {transition['to_state']}" in output:
                return transition['to_state']
        return None

    def run_agent(self, state_id, input_data=None, max_transitions=10, transition_count=0, ini_flag=0):
        # get the current state and agent
        self.running_log += f"\n\n\nCurrent state id: {state_id}\n"
        self.current_state_id = state_id  # 更新当前状态id
        self.write_current_state()  # 写入当前状态id
        self.write_log()  # 自动保存日志
        state = self.states[state_id]
        agent = self.agents[state['agent_id']]
        self.running_log += f"\n\n\nCurrent agent: {agent['name']}\n"
        self.write_log()  # 自动保存日志
        llm = self.llms[agent['agent_id']]
        if state['is_initial'] and ini_flag == 0:
            instruction = state['instruction'] + "The user input is:\n" + input_data
            for all_llm in self.llms.values():
                all_llm.add_message("The user input is:\n" + input_data)
        elif ini_flag == 0:
            instruction = state['instruction']
        self.running_log += f"\n\n\nCurrent instruction: {instruction}\n"
        self.write_log()  # 自动保存日志
        instruction += "Add <STATE_TRANS>: <fill in id> after complete the task and make sure the tool is executed successfully"
        if "code_interpreter" in agent['tools']:
            instruction +="- code_interpreter: Use it with <execute>```python <Your Code> ```<\\execute>. and you will got the stdout or error message\n WARNING: 1. Thses enironment is not a jupyter notebook. Please use print(df.head()) or print(x) instead of direct use df.head() or x, other jupyer outputs  also need print out. 2. Put the code you want to execute in one snippet"
        conversation_count = 0
        while conversation_count < 4:
            output = llm.chat(instruction)
            print("========INSTRUCTION==============")
            print(instruction)
            print("======================")
            print(agent['name'],":\n",output)
            #if state['is_final']:
            #    return output
            if not output:
                output = " "
            if "<|submit|>" in output or state['is_final']:
                self.running_log += f"\n\n\n<|completed|>\nComplete final state. Task completed, result is:\n {output}\n"
                self.current_state_id = None  # 测试完成，清空当前状态
                self.write_current_state()  # 写入当前状态
                self.write_log()  # 自动保存日志
                try:
                    return output.split("<|submit|>")[1]
                except:
                    return output
            next_state_id = self.get_next_state(state_id, output)
            self.running_log += f"\n\n{output}\n\n"
            #print("=======CheckPoint=======")
            #print(next_state_id)
            action = self.extract_action(output)
            if action:
                result = self.codeinterpreter(action)
                instruction = f"Action result is :\n {result}\n(notice: If the result for a code is blank, make sure you use print(x) to print the result, notice you can not use direct x to get the result) If the result is synax error, consider use \' instead of  \" , After completed current step task, please use <STATE_TRANS>: <fill in states id>  and pass necessary information to next agent"
                self.running_log += f"\n\n\nAction result is :\n {result}\n"
                self.write_log()  # 自动保存日志
                self.current_state_id = state_id  # 保持当前状态id不变
                self.write_current_state()  # 写入当前状态id
                conversation_count += 1
                self.write_log()  # 自动保存日志
                continue
            if next_state_id:
                self.running_log += f"\n\n\nTransition to next state: {next_state_id}\n"
                self.write_log()  # 自动保存日志
                self.current_state_id = next_state_id  # 更新当前状态id
                self.write_current_state()  # 写入当前状态id
                transition_count += 1
                self.write_log()  # 自动保存日志
                if transition_count >= max_transitions:
                    return output
                info = self.extract_info(output)
                for listener_id in self.listeners[state_id]:
                    listener_llm = self.llms[listener_id]
                    listener_llm.add_message("Message from " + agent["name"] + "\n" + info)
                return self.run_agent(next_state_id, info, max_transitions, transition_count)
            else:
                instruction = "After completed current step task, please use <STATE_TRANS>: <fill in states id> "
                self.running_log += f"\n\n\nNo next state detected, instruction updated to: {instruction}\n"
                self.write_log()  # 自动保存日志
            conversation_count += 1
            # What about Memroy? Any Method to arrange the memory? sometimes too long. 
            # Maybe we can use the tool to clear the memory?
            # Or some RAG method?

        return output
    

    def extract_info(self, output):
        start_tag = "<INFO>"
        end_tag = "</INFO>"
        start_index = output.find(start_tag) + len(start_tag)
        end_index = output.find(end_tag)
        return output#[start_index:end_index]

    def extract_action(self, output):
        try:
            if "<execute>" in output:
                action = output.split("<execute>")[-1]
                action= action.split("```")[-2]
                action = action.replace("python", "")
                if "<STATE_TRANS>" in action:
                    action=action.split("<STATE_TRANS>")[0]
            else:
                action = None
            if "<file_write>" in output:
                file_writes = output.split("<file_write>")[1:]
                for file_write in file_writes:
                    file_write = file_write.split("</file_write>")[0]
                    file_path_content = file_write.split("CONTENT:", 1)
                    if len(file_path_content) == 2:
                        file_path = file_path_content[0].split("FILE_PATH:")[-1].strip()
                        file_content = file_path_content[1].rstrip()  # 使用 rstrip() 去掉结尾的换行符
                        with open(file_path, "w") as f:
                            f.write(file_content)
                action = None
        except:
            action = None
        return action

    def save(self, filename):
        data = {
            "agents": self.agents_json,
            "states": self.states_json
        }
        with open(filename, 'w') as f:
            json.dump(data, f)

    @classmethod
    def load_from_file(cls, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return cls(data['agents'], data['states'])

    def start(self, user_input, max_transitions=10):
        # 重置运行日志
        self.running_log = ""
        # 清空之前的日志文件
        self.clear_log()
        
        # 记录任务开始前的token消耗
        initial_costs = {agent_id: llm.get_token_cost() for agent_id, llm in self.llms.items()}
        
        initial_state = [state for state in self.states.values() if state['is_initial']][0]
        self.running_log += f"Task to be solved:\n{user_input}\n"
        self.write_log()  # 自动保存日志
        
        # 运行任务
        result = self.run_agent(initial_state['state_id'], user_input, max_transitions)
        
        # 计算总成本 (任务结束后的成本 - 开始前的成本)
        total_cost = 0
        for agent_id, llm in self.llms.items():
            final_cost = llm.get_token_cost()
            cost_diff = final_cost - initial_costs[agent_id]
            total_cost += cost_diff
        
        print("----------Total cost:----------", total_cost)
        return result, total_cost

    def load(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)

        self.agents_json = data['agents']
        self.states_json = data['states']
        self.agents = {agent['agent_id']: agent for agent in self.agents_json}
        self.states = {state['state_id']: state for state in self.states_json['states']}
        self.transitions = self.states_json['transitions']
        self.listeners = {state['state_id']: state.get('listener', []) for state in self.states_json['states']}

        self.llms = {}
        self.initialize_agents()

    def get_running_log(self):
        return self.running_log

    def write_current_state(self):
        state_path = os.path.join('workspace', 'current_state.json')
        state_data = {'state_id': self.current_state_id}
        try:
            with open(state_path, 'w') as f:
                json.dump(state_data, f)
        except Exception as e:
            print(f'Error writing current state: {e}')

    def write_log(self):
        """
        自动将当前的运行日志保存到 running_log.log 文件中
        """

        # Now this will be from the current path since we're running it from the main directory
        log_path = os.path.join('workspace', 'running_log.log')
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(self.running_log)
        except Exception as e:
            print(f'写入日志时出错: {e}')

    def clear_log(self):
        """
        清空 running_log.log 文件内容
        """
        log_path = os.path.join('workspace', 'running_log.log')
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            print(f'清空日志时出错: {e}')