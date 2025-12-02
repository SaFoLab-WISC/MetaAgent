import sys

from baseclass.MultiAgent import MultiAgentSystem
import json
import os

def run_mas_test(mas_json_path, test):
    with open(mas_json_path, "r") as f:
        mas_dict = json.load(f)
    
    agent_json = mas_dict['agents']
    states_json = mas_dict['states']
    
    mas = MultiAgentSystem(agent_json, states_json)
    
    result = mas.start(test)
    
    return result

