import json
import sys
sys.path.append("../baseclass")
sys.path.append("..")
from baseclass.LLM import LLM

#Direct = ''''''  
def direct(task):
    llm = LLM()
    return llm.chat(task)

def COT(task):
    llm = LLM(use_azure=True)
    COT='''Please think step by step and then solve the task. \n''' 
    return llm.chat(COT+task)


def COT_SC(task):
    COT_SC = '''Please think step by step and then solve the task. \n'''
    ans = []
    
    #ans.append(llm.chat(COT_SC+task, temperature=0.8))  
    for i in range(3):
        llm = LLM(use_azure=True)
        ans.append(llm.chat(COT_SC+task, temperature=0.8))  
    SC = '''Please select the most convincing answer from the following options: \n'''
    llm = LLM(use_azure=True)
    return llm.chat(SC+str(ans), temperature=0)

llm_debate = ''''''
def llm_debate(task):
    # Initialize agents with separate LLM instances
    num_agents = 2
    num_rounds = 3
    agents = [LLM(system_prompt="You are an intelligent agent participating in a debate. Consider other viewpoints carefully and provide clear, reasoned responses.",use_azure=True) for _ in range(num_agents)]
    
    # Initial responses from all agents
    for agent in agents:
        agent.chat(task, temperature=0.7)
    
    # Multiple rounds of discussion
    for _ in range(num_rounds - 1):  # -1 because we already had initial round
        for i, current_agent in enumerate(agents):
            # Collect other agents' latest opinions
            other_opinions = []
            for j, other_agent in enumerate(agents):
                if j != i:
                    messages = other_agent.get_whole_message()
                    other_opinions.append(messages[-1]['content'])
            
            # Construct prompt with other opinions
            prompt = f"""Consider these perspectives from other participants:
            {str(other_opinions)}
            
            Based on these viewpoints, please reconsider the original question:
            {task}
            
            Provide your updated analysis and answer."""
            
            current_agent.chat(prompt, temperature=0.7)
    
    # Final synthesis by a new agent
    final_agent = LLM(system_prompt="You are a judge tasked with analyzing multiple viewpoints and providing a final, well-reasoned conclusion.",use_azure=True)
    
    # Collect final opinions from all agents
    final_opinions = []
    for agent in agents:
        messages = agent.get_whole_message()
        final_opinions.append(messages[-1]['content'])
    
    final_prompt = f"""Review these final perspectives from multiple agents:
    {str(final_opinions)}
    
    Please analyze these viewpoints and provide a final, definitive answer to the original question:
    {task}"""
    
    return final_agent.chat(final_prompt, temperature=0)

def self_refine(task):
    llm = LLM(use_azure=True)
    ans = llm.chat(task) 
    SELF_REFINE = f'''Please add some feedback to the answer. \n Task is {task}, answer is {ans}.'''
    feedback = llm.chat(SELF_REFINE)
    REFINE = f'''Please refine the answer based on the feedback. And give a finial answer \nTask is {task}, \nanswer is {ans}.\nFeedback is {feedback}.'''  

    return llm.chat(REFINE+ans+feedback, temperature=0.8)

def spp(task):
    llm = LLM(use_azure=True)
    SPP = f'''When faced with a task, begin by identifying the participants who will contribute to solving the task. Then, initiate a multi-round collaboration process until a final solution is reached. The participants will give critical comments and detailed suggestions whenever necessary.

Here is one example:
---
Example Task: Use numbers and basic arithmetic operations (+ - * /) to obtain 24. You need to use all numbers, and each number can only be used once.
Input: 6 12 1 1

Participants: AI Assistant (you); Math Expert

Start collaboration!

Math Expert: Let's analyze the task in detail. You need to make sure that you meet the requirement, that you need to use exactly the four numbers (6 12 1 1) to construct 24. To reach 24, you can think of the common divisors of 24 such as 4, 6, 8, 3 and try to construct these first. Also you need to think of potential additions that can reach 24, such as 12 + 12.
AI Assistant (you): Thanks for the hints! Here's one initial solution: (12 / (1 + 1)) * 6 = 24
Math Expert: Let's check the answer step by step. (1+1) = 2, (12 / 2) = 6, 6 * 6 = 36 which is not 24! The answer is not correct. Can you fix this by considering other combinations? Please do not make similar mistakes.
AI Assistant (you): Thanks for pointing out the mistake. Here is a revised solution considering 24 can also be reached by 3 * 8: (6 + 1 + 1) * (12 / 4) = 24.
Math Expert: Let's first check if the calculation is correct. (6 + 1 + 1) = 8, 12 / 4 = 3, 8 * 3 = 24. The calculation is correct, but you used 6 1 1 12 4 which is not the same as the input 6 12 1 1. Can you avoid using a number that is not part of the input?
AI Assistant (you): You are right, here is a revised solution considering 24 can be reached by 12 + 12 and without using any additional numbers: 6 * (1 - 1) + 12 = 24.
Math Expert: Let's check the answer again. 1 - 1 = 0, 6 * 0 = 0, 0 + 12 = 12. I believe you are very close, here is a hint: try to change the "1 - 1" to "1 + 1".
AI Assistant (you): Sure, here is the corrected answer:  6 * (1+1) + 12 = 24
Math Expert: Let's verify the solution. 1 + 1 = 2, 6 * 2 = 12, 12 + 12 = 12. You used 1 1 6 12 which is identical to the input 6 12 1 1. Everything looks good!

Finish collaboration!

Final answer: 6 * (1 + 1) + 12 = 24

---
Now, identify the participants and collaboratively solve the following task step by step. Remember to present your final solution with the prefix "Final answer is:".

Task: \n{task}
'''
    #SPP = f'''Please solve the task step by step. \n Task is {task}.'''
    return llm.chat(SPP)

def debate_refine(task):
    # First use the debate approach to get a comprehensive answer
    debate_answer = llm_debate(task)
    
    # Then use self-refinement on the debate answer
    llm = LLM(use_azure=True)
    SELF_REFINE = f'''Please add some feedback to this debate-generated answer. 
Task is: {task}
Debate-generated answer is: {debate_answer}'''
    
    feedback = llm.chat(SELF_REFINE)
    
    REFINE = f'''Please refine the answer based on the feedback. Give a final, definitive answer.
Task is: {task}
Debate-generated answer is: {debate_answer}
Feedback is: {feedback}'''  

    return llm.chat(REFINE, temperature=0.7)


