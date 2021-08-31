#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui
import time
from causal_links_post_treatment import compute_causal_links


######################################################
################### Cost functions ###################
######################################################

def cost_idle():
    return 0.0

def cost_wait():
    return 0.0

def cost_pickup(weight):
    return weight*2

def undesired_state_1(agents):
    penalty = 0.0

    # if green and blue cube held at the same time, even by different agents
    if(("blue_cube" in agents["robot"].state.isHolding["robot"] or "blue_cube" in agents["robot"].state.isHolding["human"])
        and ("green_cube" in agents["robot"].state.isHolding["robot"] or "green_cube" in agents["robot"].state.isHolding["human"])):
        penalty += 10.0
        # print("STATE PENALTY !")

    return penalty

def undesired_sequence_1(first_action):
    penalty = 0.0
    action = first_action

    # Penalty if robot picks red and human picks after
    while action.next is not None:
        # print("seq check action : {}".format(action))
        if action.agent is "robot" and action.name is "robot_pick_cube" and action.parameters[0] is "red_cube":
            if action.next.agent is "human" and action.next.name is "human_pick_cube":
                # print("SEQ PENALTY !")
                penalty += 8.0
        action = action.next

    return penalty

######################################################
################### Primitive tasks ##################
######################################################

###########
## ROBOT ##
###########
def robot_pick_cube(agents, self_state, self_name, cube):
    # NOT PRECONDITIONS
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if cube in self_state.isHolding["human"] or cube in self_state.isPlaced["zone"] or cube not in self_state.available["zone"]:
        return False

    # EFFECTS
    for ag in agents.values():
       ag.state.isHolding[self_name].append(cube)
       ag.state.available["zone"].remove(cube)
    return agents, cost_pickup(self_state.weights[cube])


def robot_place_cube(agents, self_state, self_name):
    # NOT PRECONDITIONS
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False

    # EFFECTS
    for ag in agents.values():
        cube = ag.state.isHolding[self_name].pop()
        ag.state.isPlaced["zone"].append(cube)
    if cube == "red_cube":
        for ag in agents.values():
            ag.state.weights["blue_cube"] *= 2

    return agents, 1.0

def robot_wait(agents, self_state, self_name):
    return agents, 1.0

###########
## HUMAN ##
###########
def human_pick_cube(agents, self_state, self_name, cube):
    # NOT PRECONDITIONS
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if cube in self_state.isHolding["robot"] or cube in self_state.isPlaced["zone"] or cube not in self_state.available["zone"]:
        return False

    # EFFECTS
    for ag in agents.values():
       ag.state.isHolding[self_name].append(cube)
       ag.state.available["zone"].remove(cube)

    return agents, 1.0

def human_place_cube(agents, self_state, self_name):
    # NOT PRECONDITIONS
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False

    # EFFECTS
    for ag in agents.values():
        cube = ag.state.isHolding[self_name].pop()
        ag.state.isPlaced["zone"].append(cube)
    if cube == "red_cube":
        for ag in agents.values():
            ag.state.weights["blue_cube"] *= 2

    return agents, 1.0


ctrl_operators = [robot_pick_cube, robot_place_cube, robot_wait]
unctrl_operators = [human_pick_cube, human_place_cube]

######################################################
################### Abstract Tasks ###################
######################################################

###########
## ROBOT ##
###########
@hatpehda.multi_decomposition
def robot_build(agents, self_state, self_name):
    tasks=[]
    if "red_cube" not in self_state.isPlaced["zone"] and "red_cube" not in self_state.isHolding[self_name] and "red_cube" not in self_state.isHolding["human"]:
        tasks.append([("robot_pick_cube", "red_cube"), ("robot_place_cube",), ("robot_build",)])
    if "green_cube" not in self_state.isPlaced["zone"] and "green_cube" not in self_state.isHolding[self_name] and "green_cube" not in self_state.isHolding["human"]:
        tasks.append([("robot_pick_cube", "green_cube"), ("robot_place_cube",), ("robot_build",)])
    if "blue_cube" not in self_state.isPlaced["zone"] and "blue_cube" not in self_state.isHolding[self_name] and "blue_cube" not in self_state.isHolding["human"]:
        tasks.append([("robot_pick_cube", "blue_cube"), ("robot_place_cube",), ("robot_build",)])
    return tasks

###########
## HUMAN ##
###########
@hatpehda.multi_decomposition
def human_build(agents, self_state, self_name):
    tasks=[]
    if "red_cube" not in self_state.isPlaced["zone"] and "red_cube" not in self_state.isHolding[self_name] and "red_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "red_cube"), ("human_place_cube",), ("human_build",)])
    if "green_cube" not in self_state.isPlaced["zone"] and "green_cube" not in self_state.isHolding[self_name] and "green_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "green_cube"), ("human_place_cube",), ("human_build",)])
    if "blue_cube" not in self_state.isPlaced["zone"] and "blue_cube" not in self_state.isHolding[self_name] and "blue_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "blue_cube"), ("human_place_cube",), ("human_build",)])
    return tasks

def human_picking(agents, self_state, self_name):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if "red_cube" in self_state.isHolding["robot"] or "red_cube" in self_state.isPlaced["zone"]:
        return []
    return [("human_pick_cube", "red_cube")]

ctrl_methods = [("robot_build", robot_build)]
unctrl_methods = [("human_build", human_build), ("human_picking", human_picking)]

######################################################
######################## MAIN ########################
######################################################

if __name__ == "__main__":
    # Initial state
    initial_state = hatpehda.State("init")
    initial_state.isHolding = {"human": [], "robot": []}
    initial_state.isPlaced = {"zone": []}
    initial_state.available = {"zone": ["red_cube", "green_cube", "blue_cube"]}
    initial_state.individuals = {"Cube": ["red_cube", "green_cube", "blue_cube"]}
    initial_state.weights = {"red_cube": 1, "green_cube": 2, "blue_cube": 3}
    initial_state.attributes = {    "isHolding": initial_state.isHolding,
                                    "isPlaced": initial_state.isPlaced,
                                    "individuals": initial_state.individuals,
                                    "weights": initial_state.weights,
                                    "available": initial_state.available}

    # state.isHolding["robot"] = ["red_cube"]
    # next_state = deepcopy(state)
    # next_state.isHolding["robot"] = []
    # next_state.isPlaced["zone"] = ["red_cube"]
    #
    # modifs = compute_effects(state, next_state, state.attributes)
    # print(modifs)

    # Set cost functions
    hatpehda.set_idle_cost_function(cost_idle)
    hatpehda.set_wait_cost_function(cost_wait)
    hatpehda.set_undesired_state_functions([undesired_state_1])
    hatpehda.set_undesired_sequence_functions([undesired_sequence_1])

    # Robot
    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    robot_state = deepcopy(initial_state)
    robot_state.__name__ = "robot_init"
    hatpehda.set_state("robot", robot_state)
    hatpehda.add_tasks("robot", [("robot_build",)])

    # Human
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    human_state = deepcopy(initial_state)
    human_state.__name__ = "human_init"
    hatpehda.set_state("human", human_state)
    hatpehda.add_tasks("human", [("human_build",)])


    # Seek all possible plans #
    sols = []
    fails = []
    hatpehda.seek_plan_robot(hatpehda.agents, "robot", sols, "human", fails)
    # debug
    # print("len sols = {}".format(len(sols)))
    # for i, s in enumerate(sols):
    #     print("\n({})".format(i+1))
    #     while s is not None:
    #         print("{} : {}{}".format(s.id, s.name, s.parameters), end='')
    #         if s.previous is not None:
    #             print(", previous :{}{}".format(s.previous.name, s.previous.parameters), end='')
    #         if s.next is not None:
    #             print(", next:{}".format(s.next))
    #         s = s.previous
    # print("")

    # gui.show_plan(sols, "robot", "human", with_abstract=False)
    # input()

    # Select the best plan from the ones found above #
    branches = []
    cost, plan_root = hatpehda.select_conditional_plan(sols, "robot", "human", branches=branches)
    # print("\npolicy cost", cost)
    gui.show_plan(hatpehda.get_last_actions(plan_root), "robot", "human", with_abstract=False)

    # print("\n\nCall compute_casual_links:")
    # print(branches)
    # supports, threats = compute_causal_links(hatpehda.agents, branches, initial_state, initial_state.attributes)
    # print("\n FINAL :")
    # print("supports = ")
    # for sup in supports:
    #     print("  {} => {}".format(sup.step.action, sup.target.action))
    # print("threats = ")
    # for threat in threats:
    #     print("  {} => {}".format(threat.step.action, threat.target.action))
