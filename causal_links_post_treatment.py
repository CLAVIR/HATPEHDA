#!/usr/bin/env python3


from copy import deepcopy
import hatpehda
from hatpehda.hatpehda import Operator

## Parcours le plan avec algo, a chaque step compute effet de l'operator ##

# Variable declaration
steps = []
class Step:
    def __init__(self, action):
        self.action = action
        self.agents = None
        self.effects = [] # effets = [Modif(attribute, key, val)]
class Modif:
    def __init__(self, attribute, key, val):
        self.attribute = attribute
        self.key = key
        self.val = val

supports = []
threats = []
class Link:
    def __init__(self, step=None, target=None):
        self.step = step
        self.target = target

g_attributes = []

# DEBUG #
def print_states(agents):
    for ag in agents:
        agent = agents[ag]
        print("state {} agent :".format(agent.name))
        for attr in g_attributes:
            print("  {} = {}".format(attr, agent.state.attributes[attr]))
        return None

# Functions
def set_link(links, step, target):
    global supports
    global threats

    new_link = Link(step, target)

    # if step.action.name == "IDLE" or target.action.name == "IDLE":
    #     return None

    # prevent link with itself
    if step.action == target.action:
        return None

    # check if the link doesn't already exist
    for l in links:
        if new_link.step.action == l.step.action and new_link.target.action == l.target.action:
            return None

    if links is supports:
        print("support ", end='')
    if links is threats:
        print("threat ", end='')
    print("set_link : {} => {}".format(new_link.step.action, new_link.target.action))
    links.append(new_link)

def get_app_steps(agents, other_steps):

    applicable_steps = []

    for other_step in other_steps:
        newagents = deepcopy(agents)
        # print("step={}".format(other_step.action))
        # print_states(newagents)
        if other_step.action.name == "BEGIN":
            continue
        elif other_step.action.name == "IDLE":
            applicable_steps.append(other_step)
            # print("added")
        else:
            operator = newagents[other_step.action.agent].operators[other_step.action.name]
            result = operator(newagents, newagents[other_step.action.agent].state, other_step.action.agent, *other_step.action.parameters)

            if result != False:
                applicable_steps.append(other_step)
                # print("added")

    return applicable_steps

def compute_new_app_steps(applicable_steps, previous_applicable_steps):
    new_applicable_steps = []
    no_longer_applicable_steps = []

    print("\nCompute new applicable")

    print("applicable_steps:")
    for step in applicable_steps:
        print("  {}".format(step.action))
    print("previous_applicable_steps:")
    for step in previous_applicable_steps:
        print("  {}".format(step.action))

    for step in applicable_steps:
        if step not in previous_applicable_steps:
            new_applicable_steps.append(step)

    for step in previous_applicable_steps:
        if step not in applicable_steps:
            no_longer_applicable_steps.append(step)

    print("new applicable steps :")
    for new_app_step in new_applicable_steps:
        print("  {}".format(new_app_step.action))
    print("no longer applicable steps :")
    for no_long_app_steps in no_longer_applicable_steps:
        print("  {}".format(no_long_app_steps.action))

    return new_applicable_steps, no_longer_applicable_steps

def apply_step(agents, step):
    # applies the given step on the given state in agents
    newagents = deepcopy(agents)
    if step.action.name != "IDLE":
        agent_name = step.action.agent
        operator = agents[agent_name].operators[step.action.name]
        result = operator(newagents, newagents[agent_name].state, agent_name, *step.action.parameters)
    return newagents

def apply_effect(agents, step):
    # only applies the effects of the given step on the given state

    newagents = deepcopy(agents)
    state = newagents["robot"].state

    # append
    for add in step.effects["append"]:
        state.attributes[add.attribute][add.key].append(add.val)

    # remove
    for rm in step.effects["remove"]:
        try:
            state.attributes[rm.attribute][rm.key].remove(rm.val)
        except:
            print("value not there")

    return newagents

def compute_effects(previous_agents, current_agents, attributes):
    previous_state = previous_agents["robot"].state
    current_state = current_agents["robot"].state
    modifs = {"remove": [], "append": []}
    for attribute in attributes:
        # print("attr {}".format(attribute))
        if current_state.attributes[attribute] != previous_state.attributes[attribute]:
            # creation of new key in operators is forbidden
            for key in current_state.attributes[attribute]:
                # print("  key {}".format(key))
                # print("    prev val {}".format(previous_state.attributes[attribute][key]))
                # print("    curr val {}".format(current_state.attributes[attribute][key]))

                # if the key has been modified
                if previous_state.attributes[attribute][key] != current_state.attributes[attribute][key]:

                    previous_elem = previous_state.attributes[attribute][key]
                    if not isinstance(previous_state.attributes[attribute][key], list):
                        previous_elem = [previous_elem]

                    curr_elem = current_state.attributes[attribute][key]
                    if not isinstance(current_state.attributes[attribute][key], list):
                        curr_elem = [curr_elem]

                    # for each element in previous state key
                    # if not present in next state key
                    # then add remove
                    for x in previous_elem:
                        if x not in curr_elem:
                            # print("{} element {} not in next state key {}".format(attribute, x, key))
                            modif = Modif(attribute, key, x)
                            modifs["remove"].append(modif)

                    # for each element in next state key
                    # if not present in previous state key
                    # then add apprend
                    for x in curr_elem:
                        if x not in previous_elem:
                            # print("{} element {} not in previous state key {}".format(attribute, x, key))
                            modif = Modif(attribute, key, x)
                            modifs["append"].append(modif)
    return modifs

def initialize(initial_agents, branches, attributes):
    global steps

##### Treat plans
    plans = []
    for branch in branches:
        plan = []
        action = branch
        while action is not None:
            plan.append(action)
            action = action.next
        plans.append(plan)
    plan = plans[0]
    print("plan:")
    for action in plan:
        print("  {}".format(action))

##### Initialize steps
    print("\nINIT")
    #First action in plan must be Init or begin, without any effects
    begin_action = Operator("BEGIN", [], "human", None, None, None)
    first_step = Step(begin_action)
    first_step.agents = initial_agents
    first_step.effects = {"remove":[], "append":[]}
    steps.append(first_step)
    # Actions of the plan
    step_agents = deepcopy(initial_agents)
    for action in plan:
        if action.name == "IDLE":
            continue
        print("\nstep {}".format(action))
        step = Step(action)

        previous_agents = deepcopy(step_agents)
        step_agents = apply_step(step_agents, step)
        # print_states(step_agents)
        step.agents = step_agents

        effects = compute_effects(previous_agents, step_agents, attributes)
        print("effects=")
        print("  rm  =", end="")
        for rm in effects["remove"]:
            print(" ({}, {}, {})".format(rm.attribute, rm.key, rm.val), end="")
        print("\n  add =", end='')
        for add in effects["append"]:
            print(" ({}, {}, {})".format(add.attribute, add.key, add.val), end="")
        print("")
        step.effects = effects

        steps.append(step)

# Main algo
def compute_causal_links(agents, branches, attributes):
    global supports
    global threats
    global steps

    # for debug, print_state
    global g_attributes
    g_attributes = attributes

    initial_agents = deepcopy(agents)

#### Initialization
    initialize(initial_agents, branches, attributes)

    print("initial state:")
    print_states(initial_agents)
    print("")

    # Go back from the end in the plan
    for i in range(len(steps)-1, 0, -1): # sauf BEGIN
        step = steps[i]
        newagents = deepcopy(initial_agents)
        print("\n==> step {} : {} <==".format(i, step.action))

        # Apply effects of all the supports of step from the initial state
        for sup in supports:
            if sup.target.action == step.action:
                print("support {}".format(sup.step.action))
                newagents = apply_effect(newagents, sup.step)
        print_states(newagents)

        # Check if step is applicable
        applicable_steps =  get_app_steps(newagents, steps)

        print("applicable_steps :")
        for app_step in applicable_steps:
            print("  {}".format(app_step.action))

        if step in applicable_steps:
            print("A tous ses supports !")
        else:
            print("hum il en manque")
            ok = False
            j = i - 1
            while not ok and j>=0:
                print("\nj={}".format(j))

                # Apply effect of all supports in state of step j-1
                newagents = deepcopy(steps[j-1].agents)
                for sup in supports:
                    if sup.target.action == step.action:
                        print("known support {}".format(sup.step.action))
                        newagents = apply_effect(newagents, sup.step)

                # Apply effects of step j in state j-1, once effects of supports have been applied
                before_applicable_steps = get_app_steps(steps[j-1].agents, steps)
                newagents = apply_effect(newagents, steps[j])
                after_applicable_steps = get_app_steps(newagents, steps)

                new_applicable_steps, no_longer_app_steps = compute_new_app_steps(after_applicable_steps, before_applicable_steps)

                # If step i is appicable, step j is a support of step i (step)
                if step in new_applicable_steps:
                    print(steps[j].action, end='')
                    print(" is a support !")
                    set_link(supports, steps[j], step)

                # Check if step has all its supports
                # Apply effects of all the supports of step from the initial state
                check_all_agents = deepcopy(initial_agents)
                for sup in supports:
                    if sup.target.action == step.action:
                        print("support {}".format(sup.step.action))
                        check_all_agents = apply_effect(check_all_agents, sup.step)
                # Check if step is applicable
                applicable_steps =  get_app_steps(check_all_agents, steps)
                if step in applicable_steps:
                    print("A Finalement tous ses supports !")
                    ok = True
                else:
                    j -= 1

    return supports, threats
