#!/usr/bin/env python3
import sys
import hatpehda
from copy import deepcopy
from hatpehda import gui
import time
from hatpehda.causal_links_post_treatment import compute_causal_links


######################################################
################### Cost functions ###################
######################################################

# None

######################################################
################### Primitive tasks ##################
######################################################

def moveTo(agents, self_state, self_name, loc):
    for ag in agents.values():
        ag.state.at[self_name] = loc

    print("=== op> {}_moveTo={}".format(self_name[0], loc))
    return agents, 1.0

def pick(agents, self_state, self_name, obj):
    if not isReachable(self_state, self_name, obj):
        return False
    if self_state.holding[self_name] != None and self_state.holding[self_name] != []:
        return False
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        return False

    for ag in agents.values():
        ag.state.holding[self_name].append(obj)
        ag.state.at[obj] = self_name

    print("=== op> {}_pick={}".format(self_name[0], obj))
    return agents, 1.0

def place(agents, self_state, self_name, obj, loc):
    if self_state.at[self_name] != self_state.locStack[self_name]:
        return False
    if obj not in self_state.holding[self_name]:
        return False

    # Verif ordre stack
    if loc in self_state.locations["bridge"]:
        if not isBaseBuilt(self_state, self_name):
            return False
    if loc in self_state.locations["top"]:
        if not isBridgeBuilt(self_state, self_name):
            return False

    # S'il y a deja un objet placé à l'emplacement voulu dans la stack (mais pas de contrainte pour sur la table)
    for key, value in self_state.at.items():
        if value == loc and (loc not in self_state.locations["table"]):
            return False

    for ag in agents.values():
        ag.state.holding[self_name].remove(obj)
        ag.state.at[obj] = loc

    print("=== op> {}_place obj={} loc={}".format(self_name[0], obj, loc))
    return agents, 1.0

def wait(agents, sef_state, self_name):
    print("=== op> {}_wait".format(self_name[0]))
    return agents, 1.0

def r_askPonctualHelp(agents, self_state, self_name, obj):
    return False

def r_askSharedGoal(agents, self_state, self_name):
    return False

ctrl_operators =    [wait, moveTo, pick, place, r_askPonctualHelp, r_askSharedGoal]
unctrl_operators =  [wait, moveTo, pick, place]

######################################################
################### Abstract Tasks ###################
######################################################

def stack(agents, self_state, self_name):
    return [("buildBase",), ("buildBridge",), ("buildTop",)]

def buildBase(agents, self_state, self_name):
    return [("getAndPlace", "red", "base"), ("getAndPlace", "red", "base")]

def buildBridge(agents, self_state, self_name):
    # If already built
    if isBridgeBuilt(self_state, self_name):
        return []
    return [("getAndPlace", "green", "bridge")]

def buildTop(agents, self_state, self_name):
    return [("getAndPlace", "blue", "top"), ("getAndPlace", "yellow", "top")]

def getAndPlace(agents, self_state, self_name, color_obj, loc):
    print("start {}_getAndPlace {} {}".format(self_name[0], color_obj, loc))

    # Get obj
    obj = None
    possible_cubes = []
    for cube in self_state.cubes[color_obj]:
        print("cube={}".format(cube))
        print("cube at={}".format(self_state.at[cube]))
        if cube not in self_state.holding[self_state.otherAgent[self_name]]:
            if self_state.at[cube] not in self_state.locations["base"] and self_state.at[cube] not in self_state.locations["bridge"] and self_state.at[cube] not in self_state.locations["top"]:
                possible_cubes.append(cube)

    print("possible_cubes={}".format(possible_cubes))

    for cube in possible_cubes:
        if isReachable(self_state, self_name, cube):
            obj = cube
            break
    # If there are pickable cubes not none reachable from current position
    if obj == None and possible_cubes != []:
        obj = possible_cubes[0]

    print("getPlace color_obj={} loc={}".format(color_obj, loc))
    print("getPlace obj={}".format(obj))
    if obj == None:
        print("done")
        return []

    if self_name == "robot":
        tasks = [("r_makeReachable", obj)]
    elif self_name == "human":
        tasks = [("h_makeReachable", obj)]
    tasks = tasks + [("pick", obj), ("makeStackReachable",), ("placeUndef", obj,loc)]

    return tasks

def makeStackReachable(agents, self_state, self_name):
    if self_state.at[self_name] == self_state.locStack[self_name]:
        return []
    return [("moveTo", self_state.locStack[self_name])]

def placeUndef(agents, self_state, self_name, obj, loc):

    loc_found = None
    print("placeUndef obj={} loc={}".format(obj, loc))

    for l in self_state.locations[loc]:
        print("l={}".format(l))
        already = False
        for key, value in self_state.at.items():
            if value == l:
                already = True
                break
        if already:
            continue
        else:
            loc_found = l
            break

    if loc_found == None:
        return False

    return [("place", obj, loc_found)]

def r_askHelp(agents, self_state, self_name, obj):
    return False

def r_makeReachable(agents, self_state, self_name, obj):
    print("in r_makeReachable")
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        return False
    if isReachable(self_state, self_name, obj):
        return []
    print("reachable move to ={}".format(self_state.at[obj]))
    return [("moveTo", self_state.at[obj])]

def h_makeReachable(agents, self_state, self_name, obj):
    print("in h_makeReachable")
    if obj in self_state.holding[self_state.otherAgent[self_name]]:
        return False
    if isReachable(self_state, self_name, obj):
        return []
    print("reachable move to ={}".format(self_state.at[obj]))
    return [("moveTo", self_state.at[obj])]

ctrl_methods = [("stack", stack),
                ("buildBase", buildBase),
                ("buildBridge", buildBridge),
                ("buildTop", buildTop),
                ("getAndPlace", getAndPlace),
                ("r_makeReachable", r_makeReachable),
                ("makeStackReachable", makeStackReachable),
                ("placeUndef", placeUndef),
                ("r_askHelp", r_askHelp)]

unctrl_methods = [("stack", stack),
                ("buildBase", buildBase),
                ("buildBridge", buildBridge),
                ("buildTop", buildTop),
                ("getAndPlace", getAndPlace),
                ("h_makeReachable", h_makeReachable),
                ("makeStackReachable", makeStackReachable),
                ("placeUndef", placeUndef)]

######################################################
################## Helper functions ##################
######################################################

def isBaseBuilt(self_state, self_name):

    b1_placed = False
    for key, value in self_state.at.items():
        if value == "b1" and key in self_state.cubes["red"]:
            b1_placed = True

    b2_placed = False
    for key, value in self_state.at.items():
        if value == "b2" and key in self_state.cubes["red"]:
            b2_placed = True

    return b1_placed, b2_placed

def isBridgeBuilt(self_state, self_name):

    br_placed = False
    for key, value in self_state.at.items():
        if value == "br" and key in self_state.cubes["green"]:
            br_placed = True

    return br_placed

def isTopBuilt(self_state, self_name):

    t1_placed = False
    for key, value in self_state.at.items():
        if value == "t1" and key in self_state.cubes["blue"]:
            t1_placed = True

    t2_placed = False
    for key, value in self_state.at.items():
        if value == "t2" and key in self_state.cubes["yellow"]:
            t2_placed = True

    return t1_placed, t2_placed

def isReachable(self_state, self_name, obj):
    loc_obj = self_state.at[obj]
    loc_agent = self_state.at[self_name]

    reachable = False
    if loc_obj in self_state.locations["table"]:
        reachable = loc_obj=="middle" or loc_obj==loc_agent

    print("isReachable obj={} for={} {}".format(obj, self_name, reachable))

    return reachable


######################################################
######################## MAIN ########################
######################################################

if __name__ == "__main__":
    # Initial state
    initial_state = hatpehda.State("init")
    initial_state.locations = {"base":["b1", "b2"], "bridge":["br"], "top":["t1", "t2"], "table":["side_r", "side_h", "middle", "side_right"]}
    initial_state.cubes = {"red":["red1", "red2"], "green":["green1"], "blue":["blue1"], "yellow":["yellow1"]}
    initial_state.solution = {"b1":"red", "b2":"red", "br":"green", "t1":"blue", "t2":"yellow"}
    initial_state.otherAgent = {"robot": "human", "human": "robot"}
    initial_state.locStack = {"robot": "side_r", "human": "side_h"}

    initial_state.at = {"robot":"side_r", "human":"side_h", "red1":"side_right", "red2":"side_h", "green1":"middle", "blue1":"middle", "yellow1":"middle"}
    initial_state.holding = {"robot":[], "human":[]}

    # Robot
    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    robot_state = deepcopy(initial_state)
    robot_state.__name__ = "robot_init"
    hatpehda.set_state("robot", robot_state)
    hatpehda.add_tasks("robot", [("stack",)])
    # hatpehda.add_tasks("robot", [("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",)])

    # Human
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    human_state = deepcopy(initial_state)
    human_state.__name__ = "human_init"
    hatpehda.set_state("human", human_state)
    hatpehda.add_tasks("human", [("stack",)])

    # Problem #
    # Agenda :  ("robot", [("r_getAndPlace", "red", "base"), ("r_getAndPlace", "red", "base")])
    #           ("human", [("h_getAndPlace", "red", "base")])
    # at = {"robot":"side_r", "human":"side_h", "red1":"side_h", "red2":"side_h", "green1":"middle", "blue1":"middle", "yellow1":"middle"}
    # R start moving to side_h and then tries to pick obj, but human picks it first => pick fails
    # Maybe add abstract task "TryPick", if obj already in human's hands return [] => task done


    # Seek all possible plans #
    sols = []
    fails = []
    print("Seek all possible plans")
    hatpehda.seek_plan_robot(hatpehda.agents, "robot", sols, "human", fails)
    if len(sys.argv) >= 3 :
        with_begin_p = sys.argv[1].lower()
        with_abstract_p = sys.argv[2].lower()
        gui.show_all(sols, "robot", "human", with_begin=with_begin_p, with_abstract=with_abstract_p, causal_links="without")
    else:
        gui.show_all(sols, "robot", "human", with_begin="false", with_abstract="true", causal_links="without")
