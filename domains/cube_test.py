#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui
import time


######################################################
################### Cost functions ###################
######################################################

def cost_idle():
    return 0.5

def cost_pickup(weight):
    return weight*2

######################################################
################### Primitive tasks ##################
######################################################

###########
## ROBOT ##
###########
def robot_pick_cube(agents, self_state, self_name, cube):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if cube in self_state.isHolding["human"] or cube in self_state.isPlaced:
        return False
    for ag in agents.values():
       ag.state.isHolding[self_name].append(cube)
    return agents, cost_pickup(self_state.weights[cube])

def robot_place_cube(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.isPlaced.append(ag.state.isHolding[self_name].pop())
    if "red_cube" in self_state.isPlaced:
        for ag in agents.values():
            ag.state.weights["blue_cube"] += 3
    return agents, 1.0

def robot_wait(agents, self_state, self_name):
    return agents, 1.0

###########
## HUMAN ##
###########
def human_pick_cube(agents, self_state, self_name, cube):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if cube in self_state.isHolding["robot"] or cube in self_state.isPlaced:
        return False
    for ag in agents.values():
       ag.state.isHolding[self_name].append(cube)
    return agents, 1.0

def human_place_cube(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.isPlaced.append(ag.state.isHolding[self_name].pop())
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
    if "red_cube" not in self_state.isPlaced and "red_cube" not in self_state.isHolding[self_name] and "red_cube" not in self_state.isHolding["human"]:
        tasks.append([("robot_pick_cube", "red_cube"), ("robot_place_cube",), ("robot_build",)])
    if "green_cube" not in self_state.isPlaced and "green_cube" not in self_state.isHolding[self_name] and "green_cube" not in self_state.isHolding["human"]:
        tasks.append([("robot_pick_cube", "green_cube"), ("robot_place_cube",), ("robot_build",)])
    if "blue_cube" not in self_state.isPlaced and "blue_cube" not in self_state.isHolding[self_name] and "blue_cube" not in self_state.isHolding["human"]:
        tasks.append([("robot_pick_cube", "blue_cube"), ("robot_place_cube",), ("robot_build",)])
    return tasks

###########
## HUMAN ##
###########
@hatpehda.multi_decomposition
def human_build(agents, self_state, self_name):
    tasks=[]
    if "red_cube" not in self_state.isPlaced and "red_cube" not in self_state.isHolding[self_name] and "red_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "red_cube"), ("human_place_cube",), ("human_build",)])
    if "green_cube" not in self_state.isPlaced and "green_cube" not in self_state.isHolding[self_name] and "green_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "green_cube"), ("human_place_cube",), ("human_build",)])
    # if "blue_cube" not in self_state.isPlaced and "blue_cube" not in self_state.isHolding[self_name] and "blue_cube" not in self_state.isHolding["robot"]:
        # tasks.append([("human_pick_cube", "blue_cube"), ("human_place_cube",), ("human_build",)])
    return tasks

def human_picking(agents, self_state, self_name):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if "red_cube" in self_state.isHolding["robot"] or "red_cube" in self_state.isPlaced:
        return []
    return [("human_pick_cube", "red_cube")]

ctrl_methods = [("robot_build", robot_build)]
unctrl_methods = [("human_build", human_build), ("human_picking", human_picking)]

######################################################
######################## MAIN ########################
######################################################

if __name__ == "__main__":
    # Initial state
    state = hatpehda.State("robot_init")
    state.types = {"Agent": ["isHolding"]}
    state.isHolding = {"human": [], "robot": []}
    state.isPlaced = []
    state.individuals = {"Cube": ["red_cube", "green_cube", "blue_cube"]}
    state.weights = {"red_cube": 1, "green_cube": 2, "blue_cube": 3}

    # Set idle cost function
    hatpehda.set_idle_cost_function(cost_idle)

    # Robot
    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    hatpehda.set_state("robot", state)
    hatpehda.add_tasks("robot", [("robot_build",)])

    # Human
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    human_state = deepcopy(state)
    human_state.__name__ = "human_init"
    hatpehda.set_state("human", human_state)
    hatpehda.add_tasks("human", [("human_build",)])


    # Planning #
    sols = []
    fails = []
    hatpehda.seek_plan_robot(hatpehda.agents, "robot", sols, "human", fails)
    end = time.time()

    print("len sols = {}".format(len(sols)))
    for i, s in enumerate(sols):
        print("\n({})".format(i+1))
        while s is not None:
            print("{} : {}{}".format(s.id, s.name, s.parameters), end='')
            if s.previous is not None:
                print(", previous :{}{}".format(s.previous.name, s.previous.parameters), end='')
            if s.next is not None:
                print(", next:{}".format(s.next))
            s = s.previous

    gui.show_plan(sols, "robot", "human", with_abstract=True)
    input()
    cost, plan_root = hatpehda.select_conditional_plan(sols, "robot", "human")

    gui.show_plan(hatpehda.get_last_actions(plan_root), "robot", "human", with_abstract=True)
    print("policy cost", cost)
