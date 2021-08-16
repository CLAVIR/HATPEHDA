#!/usr/bin/env python3

import hatpehda
from copy import deepcopy
from hatpehda import gui
#from hatpehda import ros



import time

### Helpers

def agent_plan_contains(plan, task_name):
    for p in plan:
        if p.name == task_name:
            return True
    return False

### Primitive tasks

def robot_pick_cube(agents, self_state, self_name, cube):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if cube in self_state.isHolding["human"] or cube in self_state.isPlaced:
        return False
    for ag in agents.values():
       ag.state.isHolding[self_name].append(cube)
    return agents

def robot_place_cube(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.isPlaced.append(ag.state.isHolding[self_name].pop())
    return agents

def robot_wait(agents, self_state, self_name):
    return agents


def human_pick_cube(agents, self_state, self_name, cube):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if cube in self_state.isHolding["robot"] or cube in self_state.isPlaced:
        return False
    for ag in agents.values():
       ag.state.isHolding[self_name].append(cube)
    return agents

def human_place_cube(agents, self_state, self_name):
    if self_state.isHolding[self_name] is None or self_state.isHolding[self_name] == []:
        return False
    for ag in agents.values():
        ag.state.isPlaced.append(ag.state.isHolding[self_name].pop())
    return agents


# As we don't know the agents name in advance, we store the operators here, until a ros plan call
ctrl_operators = [robot_pick_cube, robot_place_cube, robot_wait]
unctrl_operators = [human_pick_cube, human_place_cube]

#print(",\n".join(["\"{}\": 1.0".format(f.__name__) for f in ctrl_operators + unctrl_operators]))
cost_dict = {
    "robot_pick_cube": 1.0,
    "robot_place_cube": 1.0,
    "robot_wait": 0.0,
    "human_pick_cube": 1.0,
    "human_place_cube": 1.0,
    "IDLE": 0.0
}

### Abstract Tasks

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

@hatpehda.multi_decomposition
def human_build(agents, self_state, self_name):
    tasks=[]
    if "red_cube" not in self_state.isPlaced and "red_cube" not in self_state.isHolding[self_name] and "red_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "red_cube"), ("human_place_cube",), ("human_build",)])
    if "green_cube" not in self_state.isPlaced and "green_cube" not in self_state.isHolding[self_name] and "green_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "green_cube"), ("human_place_cube",), ("human_build",)])
    if "blue_cube" not in self_state.isPlaced and "blue_cube" not in self_state.isHolding[self_name] and "blue_cube" not in self_state.isHolding["robot"]:
        tasks.append([("human_pick_cube", "blue_cube"), ("human_place_cube",), ("human_build",)])
    return tasks

def human_picking(agents, self_state, self_name):
    if self_state.isHolding[self_name] is not None and self_state.isHolding[self_name] != []:
        return False
    if "red_cube" in self_state.isHolding["robot"] or "red_cube" in self_state.isPlaced:
        return []
    return [("human_pick_cube", "red_cube")]

# We don't know the agents name in advance so we store them here, until we can add the proper agents
ctrl_methods = [("robot_build", robot_build)]
unctrl_methods = [("human_build", human_build), ("human_picking", human_picking)]





if __name__ == "__main__":
    state = hatpehda.State("robot_init")
    state.types = {"Agent": ["isHolding"]}
    state.isHolding = {"human": [], "robot": []}
    state.isPlaced = []

    # ROBOT
    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    hatpehda.set_state("robot", state)
    hatpehda.add_tasks("robot", [("robot_build",)])
    # hatpehda.add_tasks("robot", [("robot_wait",), ("robot_build",)])

    # HUMAN
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    human_state = deepcopy(state)
    human_state.__name__ = "human_init"
    hatpehda.set_state("human", human_state)
    hatpehda.add_tasks("human", [("human_picking",)])
    # hatpehda.add_tasks("human", [("human_pick_cube","red_cube")])
    # hatpehda.add_tasks("human", [("human_build",)])


    sols = []
    fails = []
    hatpehda.seek_plan_robot(hatpehda.agents, "robot", sols, "human", fails)
    end = time.time()

    print(len(sols))

    gui.show_plan(sols, "robot", "human", with_abstract=True)
    #rosnode = ros.RosNode.start_ros_node("planner", lambda x: print("plop"))
    #time.sleep(5)
    #rosnode.send_plan(sols, "robot", "human")
    input()
    cost, plan_root = hatpehda.select_conditional_plan(sols, "robot", "human", cost_dict)

    gui.show_plan(hatpehda.get_last_actions(plan_root), "robot", "human", with_abstract=True)
    #n.send_plan(hatpehda.get_last_actions(plan_root), "robot", "human")
    print("policy cost", cost)

    # print(len(hatpehda.ma_solutions))
    # for ags in hatpehda.ma_solutions:
    #    print("Plan :", ags["robot"].global_plan, "with cost:", ags["robot"].global_plan_cost)
    # print("Took", end - start, "seconds")

    # regHandler.export_log("robot_planning")
    # regHandler.cleanup()
