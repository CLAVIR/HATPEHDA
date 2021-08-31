from graphviz import Digraph

def show_plan(actions, controlable_agent, uncontrolable_agent, with_abstract=True):
    dot = Digraph(comment='Plan', format="png")
    dot.attr(fontsize="20")
    plotted_edge = set()

    for action in actions:
        while action is not None:
            color = "#AAAAFF" if action.agent == controlable_agent else "#FFFFAA"
            color_darker = "#5555CC" if action.agent == controlable_agent else "#CCCC55"
            shape = "octagon" if action.name == "IDLE" else "ellipse"
            dot.node(str(action.id), action.name + "\n(" + ",".join(map(lambda x: str(x), action.parameters)) + ")", style="filled", fillcolor=color, shape=shape)
            why = action.why
            how = action
            if with_abstract:
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
    dot.render("graph_gui_hatpehda", view=True)
