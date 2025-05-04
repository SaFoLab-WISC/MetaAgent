# Step 1. Initial Build
import sys
sys.path.append("../baseclass")
sys.path.append(".")
import argparse
import json
from colorama import init, Fore, Style
from FSM_Gen import gen as generate_MAS 
from MultiAgent import MultiAgentSystem
from prompts import *
from Optimization import optimize_fsm

# 初始化 colorama
init(autoreset=True)

def log(message, level="info"):
    if level == "info":
        print(Fore.CYAN + message)
    elif level == "success":
        print(Fore.GREEN + message)
    elif level == "warning":
        print(Fore.YELLOW + message)
    elif level == "error":
        print(Fore.RED + message)
    else:
        print(message)

def main(mas_saving_path, task_description):
    try:
        log("=== Step 1: Initial Multi-Agent System Generation ===", "info")
        agent_dict, fsm, token_cost = generate_MAS(task_description, mas_saving_path)
        if agent_dict is None or fsm is None:
            log("MAS Generation failed.", "error")
            sys.exit(1)
        log(f"MAS Generation completed. Token Cost: {token_cost}", "success")
        
        
        log("== Step 2: Optimizing the Multi-Agent System ==",'info')
        optimized_fsm = optimize_fsm(mas_saving_path)
        #with open("optimized_mas.json",'w') as f:
        #    json.dump(f,optimize_fsm)
        #print(optimized_fsm)
        log("Optimized!")


            
    except Exception as e:
        log(f"An unexpected error occurred: {e}", "error")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MetaAgent pipeline.")
    parser.add_argument(
        "--mas_path",
        type=str,
        default="test_mas.json",
        help="Path to save the Multi-Agent System JSON file."
    )
    parser.add_argument(
        "--task_description",
        type=str,
        default='''Build a Multi-Agent system which can train machine learning model based on given dataset. 
And report the expected metrics (like F-1 score, RMSE and etc. ) on test dataset to user.''',

    help="Path to save the generated test cases."  
    )
    
    args = parser.parse_args()
    main(args.mas_path, args.task_description)
'''Build a Multi-Agent system which can train machine learning model based on given dataset. 
And report the expected metrics (like F-1 score, RMSE and etc. ) on test dataset to user.''',

'''Design a Multi-Agent System that can answer sciencific multiple-choice questions. The Agent system should verify each concept and calculate the precious result. It should also contain self-refine and self reflection structures that can improve the answer quality.''',

'''Build a multi-agent system that develops software. The multi-agent
system could also save the developed software to a local file system and write a README for the
user.'''


'''Build a Multi-Agent System for write Python Functions. 
        The input is the function description,
          and the Multi-Agent System should consider the Edge cases of function input 
          (different type of data, edge values) and design the most robust function possible. 
          I need only 2 different agents. The first agent is the code generator, it would generate the initial version of the function. 
          For the code generator, it should obey the following instructions:
           - Use a Chain-of-Thought approach to break down the problem, create pseudocode, and then write the code in Python language.
           - **Understand and Clarify**: Make sure you understand the task. 
           - **Algorithm/Method Selection**: Decide on the most efficient way.
           - **Pseudocode Creation**: Write down the steps you will follow in pseudocode. 
           - **Code Generation**: Translate your pseudocode into executable Python code. 

          The second agent is the code validator, it would generate several edge unit tests to validate the function by the code interpreter tool and provide the feedback to the code generator.
          here are some instruction that the code validator should obey:  
                **1. Basic Test Cases**:
        - **Objective**: To verify the fundamental functionality of the `has_close_elements` function under normal conditions.

        **2. Edge Test Cases**:
        - **Objective**: To evaluate the function's behavior under extreme or unusual conditions.

        **3. Large Scale Test Cases**:
        - **Objective**: To assess the function’s performance and scalability with large data samples.

        **Instructions**:
        - Implement a comprehensive set of test cases following the guidelines above.
        - Ensure each test case is well-documented with comments explaining the scenario it covers.
        - Pay special attention to edge cases as they often reveal hidden bugs.
         - For large-scale tests, focus on the function's efficiency and performance under heavy loads.  
    And I need only two states: 
    The first state is the code generator write the python function code. (After complete the code, the state should transit to the second one)
    The second state is the code validator write the unit test cases and validate the function.  
    If the code does not pass the test cases, the code validator should provide the feedback to the code generator. (state transit to the first one)
'''