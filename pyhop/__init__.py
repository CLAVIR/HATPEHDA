"""
Pyhop, version 1.2.2 -- a simple SHOP-like planner written in Python.
Author: Dana S. Nau, 2013.05.31

Copyright 2013 Dana S. Nau - http://www.cs.umd.edu/~nau

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

Pyhop should work correctly in both Python 2.7 and Python 3.2.
For examples of how to use it, see the example files that come with Pyhop.

Pyhop provides the following classes and functions:

- foo = State('foo') tells Pyhop to create an empty state object named 'foo'.
  To put variables and values into it, you should do assignments such as
  foo.var1 = val1

- bar = Goal('bar') tells Pyhop to create an empty goal object named 'bar'.
  To put variables and values into it, you should do assignments such as
  bar.var1 = val1

- print_state(foo) will print the variables and values in the state foo.

- print_goal(foo) will print the variables and values in the goal foo.

- declare_operators(o1, o2, ..., ok) tells Pyhop that o1, o2, ..., ok
  are all of the planning operators; this supersedes any previous call
  to declare_operators.

- print_operators() will print out the list of available operators.

- declare_methods('foo', m1, m2, ..., mk) tells Pyhop that m1, m2, ..., mk
  are all of the methods for tasks having 'foo' as their taskname; this
  supersedes any previous call to declare_methods('foo', ...).

- print_methods() will print out a list of all declared methods.

- pyhop(state1,tasklist) tells Pyhop to find a plan for accomplishing tasklist
  (a list of tasks), starting from an initial state state1, using whatever
  methods and operators you declared previously.

- In the above call to pyhop, you can add an optional 3rd argument called
  'verbose' that tells pyhop how much debugging printout it should provide:
- if verbose = 0 (the default), pyhop returns the solution but prints nothing;
- if verbose = 1, it prints the initial parameters and the answer;
- if verbose = 2, it also prints a message on each recursive call;
- if verbose = 3, it also prints info about what it's computing.
"""

# Pyhop's planning algorithm is very similar to the one in SHOP and JSHOP
# (see http://www.cs.umd.edu/projects/shop). Like SHOP and JSHOP, Pyhop uses
# HTN methods to decompose tasks into smaller and smaller subtasks, until it
# finds tasks that correspond directly to actions. But Pyhop differs from
# SHOP and JSHOP in several ways that should make it easier to use Pyhop
# as part of other programs:
#
# (1) In Pyhop, one writes methods and operators as ordinary Python functions
#     (rather than using a special-purpose language, as in SHOP and JSHOP).
#
# (2) Instead of representing states as collections of logical assertions,
#     Pyhop uses state-variable representation: a state is a Python object
#     that contains variable bindings. For example, to define a state in
#     which box b is located in room r1, you might write something like this:
#     s = State()
#     s.loc['b'] = 'r1'
#
# (3) You also can define goals as Python objects. For example, to specify
#     that a goal of having box b in room r2, you might write this:
#     g = Goal()
#     g.loc['b'] = 'r2'
#     Like most HTN planners, Pyhop will ignore g unless you explicitly
#     tell it what to do with g. You can do that by referring to g in
#     your methods and operators, and passing g to them as an argument.
#     In the same fashion, you could tell Pyhop to achieve any one of
#     several different goals, or to achieve them in some desired sequence.
#
# (4) Unlike SHOP and JSHOP, Pyhop doesn't include a Horn-clause inference
#     engine for evaluating preconditions of operators and methods. So far,
#     I've seen no need for it; I've found it easier to write precondition
#     evaluations directly in Python. But I could consider adding such a
#     feature if someone convinces me that it's really necessary.
#
# Accompanying this file are several files that give examples of how to use
# Pyhop. To run them, launch python and type "import blocks_world_examples"
# or "import simple_travel_example".


from __future__ import print_function

import copy
import sys
from collections import namedtuple
from enum import Enum
############################################################
# States and goals
from typing import Dict


class HumanPredictionType(Enum):
    FIRST_APPLICABLE_ACTION = 0
    ALL_APPLICABLE_ACTIONS = 1

human_prediction_type = HumanPredictionType.ALL_APPLICABLE_ACTIONS

Plan = namedtuple("Plan", ["plan", "cost"])

class Task():
    __ID = 0
    def __init__(self, name, parameters, why, decompo_number, agent):
        self.id = Task.__ID
        Task.__ID += 1
        self.name = name
        self.parameters = parameters
        self.agent = agent
        self.why = why  # From which task it is decomposed
        self.decompo_number = decompo_number  # The number of the decomposition from the abstract task (self.why)
        self.applicable = True
        self.previous = None
        self.next = None

    def assign_next_id(self):
        self.id = Task.__ID
        Task.__ID += 1


class Operator(Task):
    def __init__(self, name, parameters, agent, why, decompo_number, function):
        super().__init__(name, parameters, why, decompo_number, agent)
        self.function = function
        self.cost = 0

    @staticmethod
    def copy_new_id(other):
        new = copy.deepcopy(other)
        new.assign_next_id()
        return new



    def __repr__(self):
        return str((self.name, *self.parameters))

class AbstractTask(Task):
    def __init__(self, name, parameters, agent, why, decompo_number, how, number_of_decompo):
        super().__init__(name, parameters, why, decompo_number, agent)
        self.how = how  # List of task networks this task has been decomposed into (after each decompo function has been called)
        self.number_of_decompo = number_of_decompo  # How many decomposition this task has (maybe not successful ones)



class State():
    """A state is just a collection of variable bindings."""

    def __init__(self, name):
        self.__name__ = name


class Goal():
    """A goal is just a collection of variable bindings."""

    def __init__(self, name):
        self.__name__ = name


### print_state and print_goal are identical except for the name

def print_state(state, indent=4):
    """Print each variable in state, indented by indent spaces."""
    if state != False:
        for (name, val) in vars(state).items():
            if name != '__name__':
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(state.__name__ + '.' + name)
                print(' =', val)
    else:
        print('False')


def print_goal(goal, indent=4):
    """Print each variable in goal, indented by indent spaces."""
    if goal != False:
        for (name, val) in vars(goal).items():
            if name != '__name__':
                for x in range(indent): sys.stdout.write(' ')
                sys.stdout.write(goal.__name__ + '.' + name)
                print(' =', val)
    else:
        print('False')


############################################################
# Helper functions that may be useful in domain models

def forall(seq, cond):
    """True if cond(x) holds for all x in seq, otherwise False."""
    for x in seq:
        if not cond(x): return False
    return True


def find_if(cond, seq):
    """
    Return the first x in seq such that cond(x) holds, if there is one.
    Otherwise return None.
    """
    for x in seq:
        if cond(x): return x
    return None


############################################################
# Commands to tell Pyhop what the operators and methods are
class Agent:
    def __init__(self, name):
        self.name = name
        self.operators = {}
        self.methods = {}
        self.state = None
        self.goal = None
        self.tasks = []
        self.plan = []
        self.triggers = []


agents = {}  # type: Dict[str, Agent]


def declare_operators(agent, *op_list):
    """
    Call this after defining the operators, to tell Pyhop what they are.
    op_list must be a list of functions, not strings.
    """
    if agent not in agents:
        agents[agent] = Agent(agent)

    agents[agent].operators.update({op.__name__: op for op in op_list})
    return agents


def declare_methods(agent, task_name, *method_list):
    """
    Call this once for each task, to tell Pyhop what the methods are.
    task_name must be a string.
    method_list must be a list of functions, not strings.
    """
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].methods.update({task_name: list(method_list)})
    return agents


def set_state(agent, state):
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].state = state


def set_goal(agent, goal):
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].goal = goal


def add_tasks(agent, tasks, to_agents=None):
    if to_agents is None:
        to_agents = agents
    if agent not in to_agents:
        to_agents[agent] = Agent(agent)
    for t in tasks:
        if t[0] in to_agents[agent].operators:
            to_agents[agent].tasks.append(Operator(t[0], t[1:], agent, None, None, to_agents[agent].operators[t[0]]))
        elif t[0] in to_agents[agent].methods:
            to_agents[agent].tasks.append(AbstractTask(t[0], t[1:], agent, None, None, [], len(to_agents[agent].methods[t[0]])))
        else:
            raise TypeError("Asked to add task '{}' to agent '{}' but it is not defined "
                            "neither in its operators nor methods.".format(t[0], agent))

def declare_trigger(agent, trigger):
    if agent not in agents:
        agents[agent] = Agent(agent)
    agents[agent].triggers.append(trigger)

def reset_agents_tasks():
    for agent in agents:
        agents[agent].tasks = []

def reset_planner():
    global agents
    agents = {}


############################################################
# Commands to find out what the operators and methods are

def print_operators(agent=None):
    """Print out the names of the operators"""
    if agent is None:
        print("==OPERATORS==")
        for a, ag in agents.items():
            print("Agent:", a)
            print("\t", ', '.join(ag.operators))
    else:
        print('OPERATORS:', ', '.join(agents[agent].operators))


def print_methods(agent=None):
    """Print out a table of what the methods are for each task"""
    print("==METHODS==")
    print('\t{:<14}{}'.format('TASK:', 'METHODS:'))
    if agent is None:
        for a, ag in agents.items():
            print("Agent:", a)
            for task in ag.methods:
                print('\t{:<14}'.format(task) + ', '.join([f.__name__ for f in ag.methods[task]]))
    else:
        ag = agents[agent]
        for task in ag.methods:
            print('\t{:<14}'.format(task) + ', '.join([f.__name__ for f in ag.methods[task]]))


############################################################
# Cost related functions
# Cost functions must be able to take agents before action, agents after action,
# cost-linked arguments and arguments of the action

def fixed_cost(cost):
    return cost


############################################################
# The actual planner

def seek_plan_robot(agents: Dict[str, Agent], agent_name, sols, uncontrollable_agent_name = "human", fails=None, previous_action=None):
    if fails is None:
        fails = []
    if agents[agent_name].tasks == []:
        sols.append(agents)
        return True
    task = agents[agent_name].tasks[0]
    if task.name in agents[agent_name].operators:
        operator = agents[agent_name].operators[task.name]
        newagents = copy.deepcopy(agents)
        result = operator(newagents, newagents[agent_name].state, agent_name, *task.parameters)
        if result == False:
            return False
        newagents[agent_name].tasks = newagents[agent_name].tasks[1:]
        action = Operator.copy_new_id(task)
        action.previous = previous_action
        newagents[agent_name].plan.append(action)
        new_possible_agents = get_human_next_actions(newagents, uncontrollable_agent_name, previous_action=action)
        if new_possible_agents == False:
            # No action is feasible for the human
            print("No action feasible for the human")
            return False
        for ag in new_possible_agents:
            seek_plan_robot(ag, agent_name, sols, uncontrollable_agent_name, fails, previous_action=ag[uncontrollable_agent_name].plan[-1])
        print("robot plan:", newagents[agent_name].plan, "human plan:", newagents[uncontrollable_agent_name].plan)
        return True
    if task.name in agents[agent_name].methods:
        decompos = agents[agent_name].methods[task.name]
        reachable_agents = []
        for i, decompo in enumerate(decompos):
            newagents = copy.deepcopy(agents)
            subtasks = decompo(newagents, newagents[agent_name].state, agent_name, *task.parameters)
            if subtasks is None:
                raise TypeError(
                    "Error: the decomposition function: {} of task {} has returned None. It should return a list or False.".format(decompo.__name__,  task.name))
            if subtasks != False:
                subtasks_obj = []
                for sub in subtasks:
                    if sub[0] in agents[agent_name].methods:
                        subtasks_obj.append(AbstractTask(sub[0], sub[1:], agent_name, task, i, [], len(agents[agent_name].methods[sub[0]])))
                    elif sub[0] in agents[agent_name].operators:
                        subtasks_obj.append(Operator(sub[0], sub[1:], agent_name, task, i, agents[agent_name].operators[sub[0]]))
                    else:
                        raise TypeError(
                            "Error: the decomposition function '{}' of task '{}' "
                            "returned a subtask '{}' which is neither in the methods nor in the operators "
                            "of agent '{}'".format(decompo.__name__, task.name, sub[0], agent_name)
                        )

                newagents[agent_name].tasks = subtasks_obj + newagents[agent_name].tasks[1:]
                reachable_agents.append(newagents)
        if reachable_agents == []:
            # No decomposition is achievable for this task
            print("No decompo found for the robot for task:", task.name)
            print("robot plan:", newagents[agent_name].plan, "human plan:", newagents[uncontrollable_agent_name].plan)
            print_state(newagents[agent_name].state)
            return False
        else:
            for ag in reachable_agents:
                seek_plan_robot(ag, agent_name, sols, uncontrollable_agent_name, fails, previous_action)
            return True
    return False




def get_human_next_actions(agents, agent_name, previous_action):
    global human_prediction_type
    if human_prediction_type == HumanPredictionType.FIRST_APPLICABLE_ACTION:
        sols = []
        next_actions = get_first_applicable_action(agents, agent_name, sols)
        if next_actions is False:
            newagents = copy.deepcopy(agents)
            newagents[agent_name].plan.append(Operator("WAIT", [], agent_name,  None, 0, None))  # Default action
            return [newagents]
        else:
            return sols
    elif human_prediction_type == HumanPredictionType.ALL_APPLICABLE_ACTIONS:
        sols = []
        result = get_all_applicable_actions(agents, agent_name, sols, previous_action=previous_action)
        if result is False:
            raise Exception("Error during human HTN exploration")
        if sols == []:
            newagents = copy.deepcopy(agents)
            newagents[agent_name].plan.append(Operator("WAIT", [], agent_name, None, 0, None))  # Default action
            return [newagents]
        else:
            return sols




def get_all_applicable_actions(agents, agent_name, solutions, previous_action):
    if agents[agent_name].tasks == []:
        newagents = copy.deepcopy(agents)
        idle = Operator("IDLE", [], agent_name, None, 0, None)
        idle.previous = previous_action
        newagents[agent_name].plan.append(idle)
        solutions.append(newagents)
        return
    task = agents[agent_name].tasks[0]
    if task.name in agents[agent_name].operators:
        operator = agents[agent_name].operators[task.name]
        newagents = copy.deepcopy(agents)
        result = operator(newagents, newagents[agent_name].state, agent_name, *task.parameters)
        if result == False:
            return
        newagents[agent_name].tasks = newagents[agent_name].tasks[1:]
        action = Operator.copy_new_id(task)
        action.previous = previous_action
        newagents[agent_name].plan.append(action)
        solutions.append(newagents)
        return
    if task.name in agents[agent_name].methods:
        decompos = agents[agent_name].methods[task.name]
        for i, decompo in enumerate(decompos):
            newagents = copy.deepcopy(agents)
            subtasks = decompo(newagents, newagents[agent_name].state, agent_name, *task.parameters)
            if subtasks != False:
                subtasks_obj = []
                for sub in subtasks:
                    if sub[0] in agents[agent_name].methods:
                        subtasks_obj.append(AbstractTask(sub[0], sub[1:], agent_name, task, i, [], len(agents[agent_name].methods[sub[0]])))
                    elif sub[0] in agents[agent_name].operators:
                        subtasks_obj.append(Operator(sub[0], sub[1:], agent_name, task, i, agents[agent_name].operators[sub[0]]))
                    else:
                        raise TypeError(
                            "Error: the decomposition function '{}' of task '{}' "
                            "returned a subtask '{}' which is neither in the methods nor in the operators "
                            "of agent '{}'".format(decompo.__name__, task.name, sub[0], agent_name)
                        )
                newagents[agent_name].tasks = subtasks_obj + newagents[agent_name].tasks[1:]
                get_all_applicable_actions(newagents, agent_name, solutions, previous_action)
        return
    print("looking for:", task.name, "not a task nor an action of agent", agent_name)
    return False


def get_first_applicable_action(agents, agent_name, solutions):
    raise NotImplementedError("Not implemented yet.")

