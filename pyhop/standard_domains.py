import xml.etree.ElementTree as ET
from . import agents
import inspect
import re

task_name = re.compile("\"([^\"]+)\"")
re_args_list = re.compile("\(([^)]+)\)")
re_args_type = re.compile("@ontology_type(?:\s)+(\w+)(?:\s)*:(?:\s)*(\w+)")

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def get_return_lists(func):
    tasks_lists = []
    for l in inspect.getsource(func).split("\n"):
        if l.strip().startswith("return"):
            decompo = []
            for t in task_name.findall(l):
                decompo.append(t)
            if len(decompo) > 0:
                tasks_lists.append(decompo)
    return tasks_lists

def get_ontology_types(doc):
    if doc is None:
        return {}
    types = {}
    for l in doc.split("\n"):
        d = re_args_type.findall(l)
        if len(d) == 1:
            types[d[0][0]] = d[0][1]
    return types

def get_func_arguments(func):
    args_types = get_ontology_types(func.__doc__)
    first_line = inspect.getsource(func).split("\n")[0].strip()
    args_list = re_args_list.findall(first_line)[0]
    args = []
    print(args_types)
    for arg in args_list.split(",")[3:]:
        arg = arg.strip()
        if arg not in args_types:
            print("Warning: argument", arg, "of function", func.__name__, "does not have any ontology type")
            args.append((arg, None))
        else:
            args.append((arg, args_types[arg]))
    return args

def add_agent_arg(parameters_node):
    n = ET.Element("param")
    n.text = "agent"
    n.set("type", "Agent")
    parameters_node.append(n)



def generate_standard_domain(output_file):
    root = ET.Element("domains")
    tree = ET.ElementTree(root)
    for agent_name, agent in agents.items():
        for task in agent.methods:
            task_node = ET.Element("task")
            task_node.set("name", task)
            print("methods of", task)
            decompos_node = ET.Element("decompositions")
            for i, method in enumerate(agent.methods[task]):
                sub_methods = get_return_lists(method)
                args = get_func_arguments(method)
                args_node = ET.Element("parameters")
                add_agent_arg(args_node)
                for arg in args:
                    n = ET.Element("param")
                    n.text = arg[0]
                    if arg[1] is not None:
                        n.set("type", arg[1])
                    args_node.append(n)
                for j, m in enumerate(sub_methods):
                    method_node = ET.Element("decomposition")
                    method_node.set("id", str(i))
                    method_node.append(args_node)
                    for t in m:
                        ref_task_node = ET.Element("task_ref")
                        ref_task_node.set("name", t)
                        method_node.append(ref_task_node)
                    decompos_node.append(method_node)
            task_node.append(decompos_node)
            root.append(task_node)
        for action in agent.operators:
            action_node = ET.Element("action")
            action_node.set("name", action)
            args = get_func_arguments(agent.operators[action])
            args_node = ET.Element("parameters")
            add_agent_arg(args_node)
            for arg in args:
                n = ET.Element("param")
                n.text = arg[0]
                if arg[1] is not None:
                    n.set("type", arg[1])
                args_node.append(n)

            action_node.append(args_node)
            root.append(action_node)



    indent(root)
    tree.write(output_file)



