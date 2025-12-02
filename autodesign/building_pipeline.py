# Step 1. Initial Build
import sys

from baseclass.FSM_Gen import gen as generate_MAS 
from baseclass.MultiAgent import MultiAgentSystem
from baseclass.prompts import *
import json
from autodesign.CaseGen import case_gen
from autodesign.evolution.general_evolve import update_mas
from autodesign.Optimization import optimize_fsm
#from evaluate.test_writing import test_writing
#mas_path = "/Users/a11/Desktop/MetaAgent/MetaAgent/MetaAgent/sde/sde_round1.json"
# Step 1. Initial MAS Generation, clarify the Multi-Agent System Saving Path and Cases Saving Path
mas_saving_path = "test_mas.json"
cases_saving_path = "test_cases_debug.jsonl"
mas_description = "come up with a comprehensive national transport policy"
generate_MAS(mas_description,mas_saving_path) #  Initial MAS Generation
# Step 2. Optimize
new_fsm = optimize_fsm(mas_saving_path) # Cases Generation

print(new_fsm)

