# self optimization method, iterative ask whether two stage can be merged
# example input path: C:\zhangyaolun\桌面\ICML\MetaAgent\examples\mlbench\ml_round1.json
# example calling LLM: C:\zhangyaolun\桌面\ICML\MetaAgent\baseclass\LLM.py
# example code:
'''
Algorithm 1 FSM State Optimization
Require: State set S
Ensure: Optimized state set S
1: function LLM(state1, state2)
2: return true if state1 and state2 can be merged, false
otherwise
3: end function
4: procedure OptimizeFSM(S)
5: repeat
6: merged ← f alse
7: for each pair (si
, sj ) in S do
8: if LLM(si
, sj ) then
9: Merge si and sj into a new state sij
10: Update S by replacing si and sj with sij
11: merged ← true
12: break
13: end if
14: end for
15: until merged = f alse
16: end procedure
'''

import json
import os
import sys
import itertools
from pathlib import Path

# Add the parent directory to sys.path to be able to import baseclass module
from baseclass.LLM import LLM

def analyze_fsm_structure(fsm_data):
    """
    Analyze the FSM structure and identify potential optimizations
    
    Args:
        fsm_data (dict): The full FSM data including agents and states
        
    Returns:
        str: Analysis of the FSM structure
    """
    agents = fsm_data.get("agents", [])
    
    if "states" in fsm_data and isinstance(fsm_data["states"], dict):
        # Nested format
        states = fsm_data["states"].get("states", [])
        transitions = fsm_data["states"].get("transitions", [])
    else:
        states = fsm_data.get("states", [])
        transitions = fsm_data.get("transitions", [])
    
    # Map state_id to agent_id
    state_to_agent = {state["state_id"]: state["agent_id"] for state in states}
    
    # Map agent_id to agent info
    agent_info = {agent["agent_id"]: agent for agent in agents}
    
    # Analyze workflow
    workflow_analysis = []
    for transition in transitions:
        from_state_id = transition["from_state"]
        to_state_id = transition["to_state"]
        from_agent_id = state_to_agent.get(from_state_id)
        to_agent_id = state_to_agent.get(to_state_id)
        
        if from_agent_id and to_agent_id:
            from_agent = agent_info.get(from_agent_id, {}).get("name", f"Agent {from_agent_id}")
            to_agent = agent_info.get(to_agent_id, {}).get("name", f"Agent {to_agent_id}")
            workflow_analysis.append(f"- {from_agent} (State {from_state_id}) → {to_agent} (State {to_state_id}): {transition.get('condition', 'No condition')}")
    
    # Analyze potential merges based on sequential workflows
    agent_usage = {}
    for agent in agents:
        agent_id = agent["agent_id"]
        agent_states = [state for state in states if state["agent_id"] == agent_id]
        agent_usage[agent_id] = {
            "name": agent["name"],
            "states": [state["state_id"] for state in agent_states],
            "tools": agent.get("tools", [])
        }
    
    # Format the analysis
    analysis = f"""
FSM Structure Analysis:
- Total Agents: {len(agents)}
- Total States: {len(states)}
- Total Transitions: {len(transitions)}

Agent Usage:
{json.dumps(agent_usage, indent=2)}

Workflow Analysis:
{"".join(workflow_analysis)}
"""
    return analysis

def can_states_and_agents_be_merged(state1, state2, agent1, agent2, fsm_data, llm):
    """
    Function to determine if two states and their corresponding agents can be merged
    
    Args:
        state1 (dict): First state to compare
        state2 (dict): Second state to compare
        agent1 (dict): First agent to compare
        agent2 (dict): Second agent to compare
        fsm_data (dict): Full FSM data for context
        llm (LLM): LLM instance to use for the determination
        
    Returns:
        bool: True if states and agents can be merged, False otherwise
    """
    # Avoid comparing initial with non-initial or final with non-final states
    if state1['is_initial'] != state2['is_initial'] or state1['is_final'] != state2['is_final']:
        return False
    
    # Get FSM structure analysis for context
    fsm_analysis = analyze_fsm_structure(fsm_data)
    
    # Format the states for LLM to evaluate
    prompt = f"""
You are a Multi-Agent System Optimizer tasked with reducing unnecessary complexity in a finite state machine (FSM).

Your goal is to analyze if two states and their corresponding agents can be merged to create a more efficient system with fewer agents and states.

FSM CONTEXT:
{fsm_analysis}

STATE 1:
{json.dumps(state1, indent=2)}

STATE 2:
{json.dumps(state2, indent=2)}

AGENT 1:
{json.dumps(agent1, indent=2)}

AGENT 2:
{json.dumps(agent2, indent=2)}

Task: Determine if these states and their agents can be merged while maintaining system functionality.

Think step by step:
1. Are these states sequential in the workflow or closely related?
2. Are the agents' responsibilities complementary or part of the same logical process?
3. Would combining these states/agents reduce unnecessary communication overhead?
4. Can the tools used by both agents be effectively combined?
5. Would merging maintain or improve the overall system's coherence and functionality?

Answer with 'Yes' if they can be merged, or 'No' if they cannot.
If 'Yes', explain your reasoning in detail and suggest a name for the merged agent.
"""
    
    response = llm.chat(message=prompt, temperature=0.2)
    
    # Determine if the response indicates states can be merged
    if response.lower().startswith('yes'):
        print(f"Analysis indicates states {state1['state_id']} and {state2['state_id']} with agents {agent1['name']} and {agent2['name']} can be merged.")
        print(f"Reasoning: {response}")
        return True
    return False

def create_merged_agent(agent1, agent2, llm):
    """
    Create a merged agent from two existing agents
    
    Args:
        agent1 (dict): First agent to merge
        agent2 (dict): Second agent to merge
        llm (LLM): LLM instance to use for creating merged agent
        
    Returns:
        dict: New merged agent
    """
    # Combine tools without duplicates
    combined_tools = list(set(agent1.get('tools', []) + agent2.get('tools', [])))
    
    # Prompt LLM to create a merged agent
    prompt = f"""
You are a Multi-Agent System Optimizer tasked with creating a more efficient agent by merging two existing agents.

AGENT 1:
{json.dumps(agent1, indent=2)}

AGENT 2:
{json.dumps(agent2, indent=2)}

Create a new agent that effectively combines the responsibilities, capabilities, and tools of both agents.

Follow these guidelines:
1. Create a descriptive name that reflects the combined responsibilities
2. Write a comprehensive system prompt that covers all functions of both original agents
3. Preserve all instructions and special formatting from both original agents
4. Ensure the merged agent maintains all transition conditions of both original agents
5. Preserve any special commands or formatting (like <STATE_TRANS>, <|submit|>, etc.)

Return the merged agent in JSON format:
{{
  "name": "MergedAgentName",
  "system_prompt": "Comprehensive system prompt covering both agents' responsibilities",
  "tools": ["list", "of", "combined", "tools"]
}}
"""
    
    response = llm.chat(message=prompt, temperature=0.3)
    
    # Extract JSON from response
    try:
        # Find JSON content
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            merged_agent_json = response[json_start:json_end]
            merged_agent_data = json.loads(merged_agent_json)
            
            # Create the merged agent with the next available ID
            merged_agent = {
                "agent_id": agent1["agent_id"],  # We'll use agent1's ID and update references
                "name": merged_agent_data["name"],
                "system_prompt": merged_agent_data["system_prompt"],
                "tools": merged_agent_data.get("tools", combined_tools)
            }
            return merged_agent
        else:
            raise ValueError("Could not find JSON content in LLM response")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error creating merged agent: {e}")
        print(f"LLM response: {response}")
        # Fallback to a simple merge
        return {
            "agent_id": agent1["agent_id"],
            "name": f"{agent1['name']}And{agent2['name']}",
            "system_prompt": f"Combined agent with responsibilities of {agent1['name']} and {agent2['name']}. {agent1.get('system_prompt', '')} {agent2.get('system_prompt', '')}",
            "tools": combined_tools
        }

def merge_states(state1, state2, merged_agent_id, llm, new_state_id):
    """
    Function to merge two states into a new state
    
    Args:
        state1 (dict): First state to merge
        state2 (dict): Second state to merge
        merged_agent_id (str): ID of the merged agent
        llm (LLM): LLM instance to use for creating merged state
        new_state_id (str): ID for the new merged state
        
    Returns:
        dict: New merged state
    """
    # Combine listeners without duplicates
    combined_listeners = list(set(state1.get('listener', []) + state2.get('listener', [])))
    
    # Prompt LLM to merge the instructions
    prompt = f"""
You are a Multi-Agent System Optimizer tasked with creating a more efficient state by merging two existing states.

STATE 1:
{json.dumps(state1, indent=2)}

STATE 2:
{json.dumps(state2, indent=2)}

Create a new state instruction that effectively combines the responsibilities of both states.
The new state will be assigned to a merged agent that handles both original states' tasks.

Guidelines:
1. Instruction should cover ALL functionalities from both states
2. Be concise but comprehensive
3. Preserve any special formatting or commands (like <|submit|>)
4. Maintain the overall workflow logic

Return ONLY the new instruction text.
"""
    
    new_instruction = llm.chat(message=prompt, temperature=0.2)
    
    # Create and return the merged state
    merged_state = {
        "state_id": str(new_state_id),
        "agent_id": merged_agent_id,
        "instruction": new_instruction.strip(),
        "is_initial": state1['is_initial'],  # Both states should have same is_initial
        "is_final": state1['is_final'],      # Both states should have same is_final
        "listener": combined_listeners
    }
    
    return merged_state

def update_transitions(transitions, old_state_ids, new_state_id):
    """
    Update transitions after states have been merged
    
    Args:
        transitions (list): List of all transitions
        old_state_ids (list): List of state IDs that were merged
        new_state_id (str): ID of the new merged state
        
    Returns:
        list: Updated transitions
    """
    updated_transitions = []
    
    for transition in transitions:
        # Replace old state IDs with the new one
        from_state = transition['from_state']
        to_state = transition['to_state']
        
        if from_state in old_state_ids and to_state in old_state_ids:
            # Skip self-loops between merged states
            continue
        elif from_state in old_state_ids:
            # Update from_state to the new merged state
            updated_transition = transition.copy()
            updated_transition['from_state'] = str(new_state_id)
            updated_transitions.append(updated_transition)
        elif to_state in old_state_ids:
            # Update to_state to the new merged state
            updated_transition = transition.copy()
            updated_transition['to_state'] = str(new_state_id)
            updated_transitions.append(updated_transition)
        else:
            # No changes needed for this transition
            updated_transitions.append(transition)
    
    # Remove duplicate transitions after merging
    unique_transitions = []
    transition_keys = set()
    
    for t in updated_transitions:
        key = (t['from_state'], t['to_state'])
        if key not in transition_keys:
            transition_keys.add(key)
            unique_transitions.append(t)
    
    return unique_transitions

def update_agent_references(states, old_agent_ids, new_agent_id):
    """
    Update agent references in states after agents have been merged
    
    Args:
        states (list): List of all states
        old_agent_ids (list): List of agent IDs that were merged
        new_agent_id (str): ID of the new merged agent
        
    Returns:
        list: Updated states with new agent references
    """
    for state in states:
        # Update agent_id if it's one of the merged agents
        if state['agent_id'] in old_agent_ids:
            state['agent_id'] = new_agent_id
        
        # Update listener references
        if 'listener' in state:
            state['listener'] = [
                new_agent_id if listener in old_agent_ids else listener
                for listener in state['listener']
            ]
    
    return states

def optimize_fsm(fsm_path):
    """
    Main function to optimize FSM by merging similar states and their corresponding agents
    
    Args:
        fsm_path (str): Path to the FSM JSON file
        
    Returns:
        dict: Optimized FSM
    """
    # Load the FSM from file
    with open(fsm_path, 'r') as f:
        fsm_data = json.load(f)
    
    # Initialize LLM
    llm = LLM(system_prompt="""You are an AI designed to optimize multi-agent systems by identifying opportunities to merge agents and states, reducing complexity while maintaining functionality. 

Your goal is to:
1. Identify agents that can be combined into a more efficient single agent
2. Merge sequential or related states to reduce unnecessary transitions
3. Minimize overall system complexity to reduce token costs
4. Maintain the overall functionality and workflow of the system
5. Preserve special handling in final states (use <|submit|> format). That is output after a <|submit|> identifier.

The most effective optimization is often reducing the number of agents by merging those with related or sequential responsibilities.
""")
    
    # Extract agents, states and transitions
    agents = fsm_data.get("agents", [])
    
    if "states" in fsm_data and isinstance(fsm_data["states"], dict):
        # Nested format like ml_round1.json
        states = fsm_data["states"]["states"]
        transitions = fsm_data["states"]["transitions"]
        nested_format = True
    else:
        # Direct format
        states = fsm_data.get("states", [])
        transitions = fsm_data.get("transitions", [])
        nested_format = False
    
    # Create mappings for easier reference
    agent_map = {agent["agent_id"]: agent for agent in agents}
    
    print(f"Starting optimization with {len(agents)} agents and {len(states)} states")
    
    # First, get an overall analysis of the system
    print("Analyzing FSM structure...")
    analysis = analyze_fsm_structure(fsm_data)
    print(analysis)
    
    # Implementation of the optimization algorithm
    iteration = 0
    while True:
        iteration += 1
        merged = False
        
        # Generate all unique pairs of states
        state_pairs = list(itertools.combinations(states, 2))
        
        print(f"Iteration {iteration}: Checking {len(state_pairs)} possible state pairs for merging...")
        
        for state1, state2 in state_pairs:
            # Get corresponding agents
            agent1_id = state1["agent_id"]
            agent2_id = state2["agent_id"]
            
            # Skip if agents are the same (already same agent)
            if agent1_id == agent2_id:
                continue
            
            agent1 = agent_map.get(agent1_id)
            agent2 = agent_map.get(agent2_id)
            
            if not agent1 or not agent2:
                print(f"Warning: Could not find agent for ID {agent1_id} or {agent2_id}")
                continue
            
            # Check if these states and their agents can be merged
            if can_states_and_agents_be_merged(state1, state2, agent1, agent2, fsm_data, llm):
                print(f"Merging states {state1['state_id']} and {state2['state_id']} with agents {agent1['name']} and {agent2['name']}")
                
                # Create a merged agent
                merged_agent = create_merged_agent(agent1, agent2, llm)
                print(f"Created merged agent: {merged_agent['name']}")
                
                # Remember the state and agent IDs to be removed
                removed_state_ids = [state1['state_id'], state2['state_id']]
                removed_agent_ids = [agent1_id, agent2_id]
                
                # Keep the merged agent ID the same as agent1's ID for simplicity
                merged_agent_id = agent1_id
                
                # Update agent map
                agent_map[merged_agent_id] = merged_agent
                
                # Remove the old agents and add the merged one
                agents = [a for a in agents if a["agent_id"] not in removed_agent_ids]
                agents.append(merged_agent)
                
                # Remove the old states
                states = [s for s in states if s['state_id'] not in removed_state_ids]
                
                # Create a new merged state
                next_state_id = len(states)
                merged_state = merge_states(state1, state2, merged_agent_id, llm, next_state_id)
                
                # Add the new merged state
                states.append(merged_state)
                
                # Update transitions
                transitions = update_transitions(transitions, removed_state_ids, next_state_id)
                
                # Update agent references in all states
                states = update_agent_references(states, removed_agent_ids, merged_agent_id)
                
                # Update the FSM data to reflect changes for next iteration
                if nested_format:
                    fsm_data["agents"] = agents
                    fsm_data["states"]["states"] = states
                    fsm_data["states"]["transitions"] = transitions
                else:
                    fsm_data["agents"] = agents
                    fsm_data["states"] = states
                    fsm_data["transitions"] = transitions
                
                merged = True
                break
        
        # If no states were merged in this iteration, we're done
        if not merged:
            print(f"No more states or agents can be merged. Optimization complete after {iteration} iterations.")
            break
    
    # Renumber all agent IDs and state IDs to be sequential (0, 1, 2...)
    print("Renumbering agent and state IDs to be sequential...")
    
    # Renumber agent IDs
    agent_id_map = {}
    for i, agent in enumerate(agents):
        old_id = agent["agent_id"]
        new_id = str(i)
        agent_id_map[old_id] = new_id
        agent["agent_id"] = new_id
    
    # Renumber state IDs and update agent references
    state_id_map = {}
    for i, state in enumerate(states):
        old_id = state["state_id"]
        new_id = str(i+1)  # Start state IDs from 1 to match example
        state_id_map[old_id] = new_id
        state["state_id"] = new_id
        
        # Update agent ID reference
        state["agent_id"] = agent_id_map.get(state["agent_id"], state["agent_id"])
        
        # Update listener references
        if "listener" in state:
            state["listener"] = [agent_id_map.get(listener, listener) for listener in state["listener"]]
    
    # Update transitions with new state IDs
    for transition in transitions:
        transition["from_state"] = state_id_map.get(transition["from_state"], transition["from_state"])
        transition["to_state"] = state_id_map.get(transition["to_state"], transition["to_state"])
    
    # Prepare the optimized FSM with the same structure as the input
    if nested_format:
        optimized_fsm = fsm_data
    else:
        optimized_fsm = {
            "agents": agents,
            "states": states,
            "transitions": transitions
        }
    
    # Save the optimized FSM
    output_path = fsm_path.replace('.json', '_optimized.json')
    with open(output_path, 'w') as f:
        json.dump(optimized_fsm, f, indent=2)
    
    print(f"Optimized FSM saved to {output_path}")
    print(f"Reduced from original: {len(fsm_data['agents'])} agents to {len(agents)} agents")
    print(f"Reduced from original: {len(fsm_data['states']['states']) if nested_format else len(fsm_data['states'])} states to {len(states)} states")
    
    return optimized_fsm

if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        fsm_path = sys.argv[1]
    
    optimized_fsm = optimize_fsm(fsm_path)
    print("Optimization complete.")
    print(optimized_fsm)