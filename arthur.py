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
def move(agents, self_state, self_name, loc_from, loc_to):
    # NOT PRECONDITIONS
    if self_state.at[self_name] != loc_from or self_state.at[self_name] == loc_to:
        return False

    # EFFECTS
    for ag in agents.values():
       ag.state.at[self_name] = loc_to
    return agents, 1.0

def pick(agents, self_state, self_name, obj):
    # print("in pick operator {} {}".format(self_name, obj))
    # NOT PRECONDITIONS
    if self_state.at[self_name] != self_state.objLoc[obj]:
        return False
    # print("next pick")

    # EFFECTS
    for ag in agents.values():
        ag.state.holding[self_name].append(obj)
        ag.state.objLoc[obj] = self_name
        # print("{} : {} holding {}".format(ag.name, self_name, ag.state.holding[self_name]))

    return agents, 1.0

def build(agents, self_state, self_name, obj1, obj2):
    # print("in build operator")
    # print("obj1 = {} obj2 = {}".format(obj1, obj2))
    # print("robot : {}".format(self_state.holding[self_name]))
    # print("human : {}".format(agents["human"].state.holding[self_name]))
    if not(obj1 in self_state.holding[self_name] and obj2 in self_state.holding[self_name]):
        return False
    if not(self_state.at[self_name] == "l3"):
        return False
    # print("we are good")

    for ag in agents.values():
        ag.state.holding[self_name].remove(obj1)
        ag.state.holding[self_name].remove(obj2)
        ag.state.built["built"].append((obj1, obj2))

    return agents, 1.0


###########
## HUMAN ##
###########


ctrl_operators = [move, pick, build]
unctrl_operators = []

######################################################
################### Abstract Tasks ###################
######################################################

###########
## ROBOT ##
###########

def robot_build(agents, self_state, self_name, obj1, obj2):
    return [("get_obj", obj1), ("get_obj", obj2), ("building",)]

def get_obj(agents, self_state, self_name, obj):
    tasks = []

    if obj in self_state.holding[self_name]:
        return []

    if self_state.at[self_name] != self_state.objLoc[obj]:
        tasks.append(("move", self_state.at[self_name], self_state.objLoc[obj]))
    tasks.append(("pick", obj))

    return tasks

def building(agents, self_state, self_name):
    tasks = []
    if self_state.at[self_name] != "l3":
        tasks.append(("move", self_state.at[self_name], "l3"))
    tasks.append(("build", "a", "b"))
    return tasks

ctrl_methods = [("robot_build", robot_build), ("get_obj", get_obj), ("building", building)]
unctrl_methods = []

######################################################
######################## MAIN ########################
######################################################

if __name__ == "__main__":
    # Initial state
    initial_state = hatpehda.State("init")
    initial_state.locations = {"locations": ["l1", "l2", "l3"]} # constant
    initial_state.objLoc = {"a": "l1", "b": "l2"}
    initial_state.at = {"robot": "l1", "human": []}
    initial_state.holding = {"robot": [], "human": []}
    initial_state.built = {"built": []}
    initial_state.attributes = {    "at": initial_state.at,
                                    "holding": initial_state.holding,
                                    "objLoc": initial_state.objLoc,
                                    "built": initial_state.built}

    # Robot
    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    robot_state = deepcopy(initial_state)
    robot_state.__name__ = "robot_init"
    hatpehda.set_state("robot", robot_state)
    hatpehda.add_tasks("robot", [("robot_build", "a", "b")])

    # Human
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    human_state = deepcopy(initial_state)
    human_state.__name__ = "human_init"
    hatpehda.set_state("human", human_state)


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

    # gui.show_plan(sols, "robot", "human", with_abstract=True)
    # input()

    # Select the best plan from the ones found above #
    branches = []
    cost, plan_root = hatpehda.select_conditional_plan(sols, "robot", "human", branches=branches)
    # print("\npolicy cost", cost)
    # gui.show_plan(hatpehda.get_last_actions(plan_root), "robot", "human", with_abstract=False)
    #
    print("\n\nCall compute_casual_links:")
    # print(branches)
    supports, threats = compute_causal_links(hatpehda.agents, branches, initial_state.attributes)
    print("\n FINAL :")
    print("supports = ")
    for sup in supports:
        print("  {} => {}".format(sup.step.action, sup.target.action))
    print("threats = ")
    for threat in threats:
        print("  {} => {}".format(threat.step.action, threat.target.action))
