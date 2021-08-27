#!/usr/bin/env python3


from copy import deepcopy
import hatpehda

## Parcours le plan avec algo, a chaque step compute effet de l'operator ##

# Variable declaration
steps = []
class Step:
    def __init__(self, action):
        self.action = action
        self.state = None
        self.effects = None #effects = {"rm":[], "add":[]}

supports = []
threats = []
class Link:
    def __init__(self, step=None, target=None):
        self.step = step
        self.target = target

# Functions

def set_link(links, step, target):
    link = Link(step, target)
    # check if the link doesn't already exist
    if link not in links:
        links.append(link)

def get_app_steps(agents, step, steps):
    applicable_steps = None

    # agent_name = step.action.agent
    # operator = agents[agent_name].operators[step.action.name]
    # newagents = deepcopy(agents)
    # for agent in newagents:
    #     agent.state = state
    # result = operator(newagents, newagents[agent_name].state, agent_name, False, *step.action.parameters)

    return applicable_steps

# TO BE DONE
def compute_new_app_steps(applicable_steps, previous_applicable_steps):
    new_applicable_steps = None
    return new_applicable_steps

def apply_step(agents, step, state):
    # applies the given step on the given state
    newagents = deepcopy(agents)
    if step.action.name != "IDLE":
        agent_name = step.action.agent
        operator = agents[agent_name].operators[step.action.name]
        for agent in newagents:
            agent_state = deepcopy(state)
            newagents[agent].state = agent_state
        result = operator(newagents, newagents[agent_name].state, agent_name, False, *step.action.parameters)
    return newagents, newagents["robot"].state

def apply_effect(agents, step, state):
    # only applies the effects of the given step on the given state
    return None

def compute_effects(previous_state, current_state, attributes):
    modifs = {"remove": [], "append": []}
    for attribute in attributes:
        if current_state.attributes[attribute] != previous_state.attributes[attribute]:
            # creation of new key in operators is forbidden
            for key in current_state.attributes[attribute]:
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
                            modifs["remove"].append((attribute, key, x))

                    # for each element in next state key
                    # if not present in previous state key
                    # then add apprend
                    for x in curr_elem:
                        if x not in previous_elem:
                            # print("{} element {} not in previous state key {}".format(attribute, x, key))
                            modifs["append"].append((attribute, key, x))
    return modifs

def compute_causal_links(agents, branches, initial_state, attributes):
    global supports
    global threats
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
    #First action in plan must be Init or begin, without any effects
    state = deepcopy(initial_state)
    for action in plan:
        print("")
        print(action)
        step = Step(action)

        previous_state = deepcopy(state)
        agents, state = apply_step(agents, step, state)  ## <========= MAYBE use agents and not state
        state_step = deepcopy(state)
        step.state = state_step

        effects = compute_effects(previous_state, state_step, attributes)
        print("effects=")
        print("  rm ={}".format(effects["remove"]))
        print("  add={}".format(effects["append"]))
        step.effects = effects

        steps.append(step)

    # print(steps)

    ######################## STOP ########################
    if True:                                            ##
        return supports, threats                        ##
    ######################## STOP ########################

##### Core algorithm
    previous_app_steps = []
    for step in steps:
        state = step.state
        app_steps = get_app_steps(agents, step)
        new_app_steps = compute_new_app_steps(app_steps, previous_app_steps)
        for new_app_step in new_app_steps:
            # Add step as support of new_app_step
            set_link(supports, step, new_app_step)
            # virtually_apply(new_app_step)
            state_indep = deepcopy(step.state)
            indep_agents, state_indep = apply_step(agents, new_app_step, state_indep)

            # get list indep_applicable_actions
            indep_app_steps = get_app_steps(indep_agents, new_app_step)
            # from currently_applicable_actions and indep_applicable_actions compute indep_new_applicable_actions and indep_no_longer_applicable_actions
            indep_new_app_steps, indep_no_longer_app_steps = compute_app_changes(app_steps, indep_app_steps)
            for indep_new_app_step in indep_new_app_steps:
                # set new_app_step as support of indep_new_app_step
                set_link(supports, new_app_step, indep_new_app_step)
            for indep_no_longer_app_step in indep_no_longer_app_steps:
                # set new_app_step as threat for indep_no_longer_app_step
                set_link(threats, new_app_step, indep_no_longer_app_step)
        previous_app_steps = app_steps


##### Post traitement, check si step_i est une threat pour step_j mais que step_i est support de step_i+1 et
    # que step_i+1 est un support de step_j alors rm lien de support s(s_i+i, s_j) et threat t(s_i, s_j)

    for threat in threats:
        next_step = steps[steps.index(step)+1]
        if Link(threat.step, next_step) in supports and Link(next_step, threat.target) in supports :
            supports.remove(Link(next_step, threat.target))
            threats.remove(threat)

    return supports, threats


# check pour chaque action en appliquant les effets de chaque supports trouvé si applicable => si non alors manque des supports
# => retro applique
# Check si Step_i a tous ses supports : Se placer dans State0 (init) et apply effects de tous les supports connus de Step_i sup_i(S0). Si Step_i applicable Alors ok on a deja tous, Sinon:
# Se placer dans State0 est appliquer effets des supports de i (sup_i) + effets de step_i-2 (i-1 ? sauf si deja un support). Si step_i devient applicable alors step_i-2 est un support et on recommence
# (ou continue on ajoutant step_i-2 dans les effets support ?), sinon on recul i-3, jusqu'à init
#
# # Check si Step_i a tous ses supports
# state = State_0
# apply_effect()
#
#
# on pourrait verifier si depuis state0 les operator ont les meme effets avec forced, bof en fait car sur que non pour des actions utilisant des pop()
