from graphviz import Digraph

def show_plan(agentss, controlable_agent, uncontrolable_agent):
    dot = Digraph(comment='Plan')
    plotted_edge = set()

    for agents in agentss:
        action = agents[uncontrolable_agent].plan[-1]
        while action is not None:
            color = "#AAAAFF" if action.agent == controlable_agent else "#FFFFAA"
            color_darker = "#5555CC" if action.agent == controlable_agent else "#CCCC55"
            shape = "octagon" if action.name == "IDLE" else "ellipse"
            dot.node(str(action.id), action.name + "\n(" + ",".join(map(lambda x: str(x), action.parameters)) + ")", style="filled", fillcolor=color, shape=shape)
            why = action.why
            how = action
            while why is not None:
                if (why.id, how.id) not in plotted_edge:
                    dot.node(str(why.id), why.name, shape="rectangle", style="filled", fillcolor=color_darker)
                    dot.edge(str(why.id), str(how.id), color="#999999", label=str(how.decompo_number),
                             fontcolor="#999999")
                    plotted_edge.add((why.id, how.id))
                how = why
                why = why.why

            if action.previous is not None:
                if (action.id, action.previous.id) not in plotted_edge:
                    plotted_edge.add((action.id, action.previous.id))
                    dot.edge(str(action.previous.id), str(action.id), color="#FF5555")
            action = action.previous
    dot.render("/home/gbuisan/test", view=True)