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

###########
## ROBOT ##
###########

def r_moveTo(agents, self_state, self_name, loc):
    for ag in agents.values():
        ag.state.at[self_name] = loc

    print("=== op> r_moveTo={}".format(loc))
    return agents, 1.0

def r_pick(agents, self_state, self_name, obj):
    if not isReachable(self_state, self_name, obj):
        return False
    if self_state.holding[self_name] != None and self_state.holding[self_name] != []:
        return False
    if obj in self_state.holding["human"]:
        return False

    for ag in agents.values():
        ag.state.holding[self_name].append(obj)
        ag.state.at[obj] = self_name

    print("=== op> r_pick={}".format(obj))
    return agents, 1.0

def r_place(agents, self_state, self_name, obj, loc):
    if self_state.at[self_name] != "side_r":
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

    print("=== op> r_place obj={} loc={}".format(obj, loc))
    return agents, 1.0

def r_askPonctualHelp(agents, self_state, self_name, obj):
    return False

def r_askSharedGoal(agents, self_state, self_name):
    return False

def r_wait(agents, sef_state, self_name):
    print("=== op> r_wait")
    return agents, 1.0

###########
## HUMAN ##
###########

def h_moveTo(agents, self_state, self_name, loc):
    for ag in agents.values():
        ag.state.at["human"] = loc

    print("=== op> h_moveTo={}".format(loc))
    return agents, 1.0

def h_pick(agents, self_state, self_name, obj):
    if not isReachable(self_state, "human", obj):
        return False
    if self_state.holding["human"] != None and self_state.holding["human"] != []:
        return False
    if obj in self_state.holding["robot"]:
        return False

    for ag in agents.values():
        ag.state.holding["human"].append(obj)
        ag.state.at[obj] = "human"

    print("=== op> h_pick={}".format(obj))
    return agents, 1.0

def h_place(agents, self_state, self_name, obj, loc):
    if self_state.at["human"] != "side_h":
        return False
    if obj not in self_state.holding["human"]:
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
        ag.state.holding["human"].remove(obj)
        ag.state.at[obj] = loc

    print("=== op> h_place obj={} loc={}".format(obj, loc))
    return agents, 1.0

def h_wait(agents, sef_state, self_name):
    print("=== op> h_wait")
    return agents, 1.0


ctrl_operators = [r_wait, r_moveTo, r_pick, r_place, r_askPonctualHelp, r_askSharedGoal]
unctrl_operators = [h_wait, h_moveTo, h_pick, h_place]

######################################################
################### Abstract Tasks ###################
######################################################

###########
## ROBOT ##
###########

def r_stack(agents, self_state, self_name):
    return [("r_buildBase",), ("r_buildBridge",), ("r_buildTop",)]

def r_buildBase(agents, self_state, self_name):
    b1_placed, b2_placed = isBaseBuilt(self_state, self_name)
    if not b1_placed or not b2_placed:
        return [("r_getAndPlace", "red", "base"), ("r_buildBase",)]
    return []

def r_buildBridge(agents, self_state, self_name):
    # If already built
    if isBridgeBuilt(self_state, self_name):
        return []
    return [("r_getAndPlace", "green", "bridge")]

def r_buildTop(agents, self_state, self_name):
    return [("r_getAndPlace", "blue", "top"), ("r_getAndPlace", "yellow", "top")]

def r_getAndPlace(agents, self_state, self_name, color_obj, loc):
    print("start r_getAndPlace")

    # Get obj
    obj = None
    possible_cubes = []
    for cube in self_state.cubes[color_obj]:
        print("cube={}".format(cube))
        print("cube at={}".format(self_state.at[cube]))
        if cube not in self_state.holding["human"]:
            if self_state.at[cube] not in self_state.locations["base"] and self_state.at[cube] not in self_state.locations["bridge"] and self_state.at[cube] not in self_state.locations["top"]:
                possible_cubes.append(cube)

    print("possible_cubes={}".format(possible_cubes))

    for cube in possible_cubes:
        if isReachable(self_state, self_name, cube):
            obj = cube
            break
    if obj == None and possible_cubes != []:
        obj = possible_cubes[0]

    print("getPlace color_obj={} loc={}".format(color_obj, loc))
    print("getPlace obj={}".format(obj))
    if obj == None:
        print("done")
        return []

    return [("r_makeReachable", obj), ("r_pick", obj), ("r_makeStackReachable",), ("r_placeUndef", obj,loc)]

def r_makeReachable(agents, self_state, self_name, obj):
    print("in r_makeReachable")
    if obj in self_state.holding["human"]:
        return False
    if isReachable(self_state, self_name, obj):
        return []
    print("reachable move to ={}".format(self_state.at[obj]))
    return [("r_moveTo", self_state.at[obj])]

def r_makeStackReachable(agents, self_state, self_name):
    if self_state.at["robot"] == "side_r":
        return []
    return [("r_moveTo", "side_r")]

def r_askHelp(agents, self_state, self_name, obj):
    return False

def r_placeUndef(agents, self_state, self_name, obj, loc):

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

    return [("r_place", obj, loc_found)]

ctrl_methods = [("r_stack", r_stack),
                ("r_buildBase", r_buildBase),
                ("r_buildBridge", r_buildBridge),
                ("r_buildTop", r_buildTop),
                ("r_getAndPlace", r_getAndPlace),
                ("r_makeReachable", r_makeReachable),
                ("r_makeStackReachable", r_makeStackReachable),
                ("r_placeUndef", r_placeUndef),
                ("r_askHelp", r_askHelp)]

###########
## HUMAN ##
###########

def h_stack(agents, self_state, self_name):
    return [("h_buildBase",), ("h_buildBridge",), ("h_buildTop",)]

def h_buildBase(agents, self_state, self_name):
    b1_placed, b2_placed = isBaseBuilt(self_state, self_name)
    if not b1_placed or not b2_placed:
        return [("h_getAndPlace", "red", "base"), ("h_buildBase",)]
    return []

def h_buildBridge(agents, self_state, self_name):
    # If already built
    if isBridgeBuilt(self_state, self_name):
        return []
    return [("h_getAndPlace", "green", "bridge")]

def h_buildTop(agents, self_state, self_name):
        return [("h_getAndPlace", "blue", "top"), ("h_getAndPlace", "yellow", "top")]

def h_getAndPlace(agents, self_state, self_name, color_obj, loc):
    print("start h_getAndPlace")

    # Get obj
    obj = None
    possible_cubes = []
    for cube in self_state.cubes[color_obj]:
        print("cube={}".format(cube))
        if cube not in self_state.holding["robot"]:
            if self_state.at[cube] not in self_state.locations["base"] and self_state.at[cube] not in self_state.locations["bridge"] and self_state.at[cube] not in self_state.locations["top"]:
                possible_cubes.append(cube)

    print("possible_cubes={}".format(possible_cubes))

    for cube in possible_cubes:
        if isReachable(self_state, self_name, cube):
            obj = cube
            break
    if obj == None and possible_cubes != []:
        obj = possible_cubes[0]

    print("getPlace color_obj={} loc={}".format(color_obj, loc))
    print("getPlace obj={}".format(obj))
    if obj == None:
        return []

    return [("h_makeReachable", obj), ("h_pick", obj), ("h_makeStackReachable",), ("h_placeUndef", obj,loc)]

def h_makeReachable(agents, self_state, self_name, obj):
    print("in h_makeReachable")
    if obj in self_state.holding["robot"]:
        return False
    if isReachable(self_state, self_name, obj):
        return []
    print("reachable move to ={}".format(self_state.at[obj]))
    return [("h_moveTo", self_state.at[obj])]

def h_makeStackReachable(agents, self_state, self_name):
    if self_state.at["human"] == "side_h":
        return []
    return [("h_moveTo", "side_r")]

def h_placeUndef(agents, self_state, self_name, obj, loc):

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

    return [("h_place", obj, loc_found)]


unctrl_methods = [("h_stack", h_stack),
                ("h_buildBase", h_buildBase),
                ("h_buildBridge", h_buildBridge),
                ("h_buildTop", h_buildTop),
                ("h_getAndPlace", h_getAndPlace),
                ("h_makeReachable", h_makeReachable),
                ("h_makeStackReachable", h_makeStackReachable),
                ("h_placeUndef", h_placeUndef)]

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

    initial_state.at = {"robot":"side_r", "human":"side_h", "red1":"side_r", "red2":"side_h", "green1":"middle", "blue1":"middle", "yellow1":"middle"}
    initial_state.holding = {"robot":[], "human":[]}

    # Robot
    hatpehda.declare_operators("robot", *ctrl_operators)
    for me in ctrl_methods:
        hatpehda.declare_methods("robot", *me)
    robot_state = deepcopy(initial_state)
    robot_state.__name__ = "robot_init"
    hatpehda.set_state("robot", robot_state)
    hatpehda.add_tasks("robot", [("r_stack",)])
    # hatpehda.add_tasks("robot", [("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",), ("r_wait",)])

    # Human
    hatpehda.declare_operators("human", *unctrl_operators)
    for me in unctrl_methods:
        hatpehda.declare_methods("human", *me)
    human_state = deepcopy(initial_state)
    human_state.__name__ = "human_init"
    hatpehda.set_state("human", human_state)
    hatpehda.add_tasks("human", [("h_stack",)])

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

    # input()
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

    # Select the best plan from the ones found above #
    # print("Select plan with costs")
    # best_plan, best_cost, all_branches, all_costs = hatpehda.select_conditional_plan(sols, "robot", "human")
    # gui.show_all(hatpehda.get_last_actions(best_plan), "robot", "human", with_begin="true", with_abstract="false", causal_links="without")
    # input()

    # print("Compute_casual_links")
    # supports, threats = compute_causal_links(hatpehda.agents, best_plan)
    # if len(sys.argv) >= 4 :
    #     with_begin_p = sys.argv[1].lower()
    #     with_abstract_p = sys.argv[2].lower()
    #     causal_links_p = sys.argv[3].lower()
    #     constraint_causal_edges_p = sys.argv[4].lower() if len(sys.argv) >= 5 else "true"
    #     gui.show_all(hatpehda.get_last_actions(best_plan), "robot", "human", supports=supports, threats=threats,
    #         with_begin=with_begin_p, with_abstract=with_abstract_p, causal_links=causal_links_p, constraint_causal_edges=constraint_causal_edges_p)
