import json  
# No tool here is ok
# A battle between Case Generator and Finite State Machine Generator
# Given the task description and the generated FSM, generate the test cases.
# For several terms.
import sys

import json
import os
from baseclass.LLM import LLM
def extract_substrings(string, s_start, s_end):
    results = []
    start_len = len(s_start)
    end_len = len(s_end)
    start_idx = 0

    while True:
        # Find the start index of the next occurrence of s_start
        start_idx = string.find(s_start, start_idx)
        if start_idx == -1:
            break  # No more occurrences of s_start, exit the loop

        # Move the index to the end of s_start
        start_idx += start_len

        # Find the end index of the next occurrence of s_end
        end_idx = string.find(s_end, start_idx)
        if end_idx == -1:
            break  # No more occurrences of s_end, exit the loop

        # Extract the substring between s_start and s_end
        substring = string[start_idx:end_idx]
        results.append(substring)

        # Move the index to the end of s_end for the next search
        start_idx = end_idx + end_len

    return results


case_generator_prompts='''

You are a QA Engineer. Your goal is to identify the shortcomings of the Finite State Machine (FSM) designed for the task.

You should consider the following:

You should always follow this format:

Reasoning: 
    What specific skills or abilities does this task primarily assess?
    What are the edge cases?
    What scenarios are not covered by the existing FSM?

Tests:
<Test>
<fill in Test input 1>
</Test>

<Test>
<fill in Test input 2>
</Test> 
...

'''
runing_prompt='''
Now, the task the FSM need to solve is: {task} \n
and the designed FSM is:\n {FSM}. Please Generate 3 tests to test the FSM.
Example Test(For software development task):
<Test>
Build a snack game via Vue.js
</Test>
Example Test(For story writing task):
<Test>
Write a story containing the answer of these questions:  
["What type of animal is the star of the 2005 film Racing Stripes?", "Author Dick Francis is famous for writing novels based around which sport?", "Which Scottish newspaper features the Broons and Oor Wullie?", "Which Christmas song includes the line It seems so long since I could say 'sister Susie sitting on a thistle'?", "Which British footballer has the most number of International caps?", "Who holds a trumpet on the album cover of Sgt. Pepper's Lonely Hearts Club Band by The Beatles?", "Which song begins with the line The taxman's taken all my dough?", "The Kray twins were convicted of the murder of George Cornell in the East End of London in 1966. What was the name of the pub in which he was shot?", "Who composed the musical theme for the Pink Panther?", "Which actress married Dennis Quaid on Valentine's Day in 1991?"]
<\Test>

Example Test(For machine learning task):
<Test>
Train a SVM model to classify the sentiment of a text as positive or negative. 
<\Test>

if need example dataset(for machine learning task), here is an example dataset path:
/Users/a11/Desktop/MetaAgent/MetaAgent/ml_benchmark/04_titanic/split_train.csv
'''



def case_gen(task,fsm_path):
    llm=LLM(system_prompt=case_generator_prompts)
    fsm=json.loads(open(fsm_path).read())
    prompt=runing_prompt.format(task=task,FSM=fsm)
    test_rsp=llm.chat(prompt)
    #print(test_rsp)
    tests=extract_substrings(test_rsp,"<Test>","</Test>")
    print(tests)
    print(type(tests))
    return tests
    #cases=['build a blog website,and save it to a new folder']
    #print(cases)
    #return cases

#case_gen("A Multi-Agent System for software development","/Users/a11/Desktop/MetaAgent/MetaAgent_release/examples/sde/sde_round2.json")













