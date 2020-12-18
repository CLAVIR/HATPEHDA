import rospy
import json

from planner_msgs.msg import PlanRequest, Plan, AgentTasksRequest, Task

from . import Goal

class RosNode:
    def __init__(self, name, on_new_request_cb):
        self.name = name
        self.user_callback = on_new_request_cb
        rospy.init_node(name)
        self.request_sub = rospy.Subscriber("~request_new_plan", PlanRequest, self.on_new_request)
        self.plan_pub = rospy.Publisher("~plan_answer", Plan, queue_size=10)
    @staticmethod
    def start_ros_node(node_name="planner", on_new_request=None):
        return RosNode(node_name, on_new_request)

    def retrieve_agents_task(self, agents_task_msg, agents_task):
        for ag in agents_task_msg:
            agents_task[ag.agent_name] = []
            for task in ag.tasks:
                arguments = []
                for ar in task.parameters:
                    try:
                        print("goal", ar)
                        j = json.loads(ar)
                        print(j)
                        goal = Goal("goal")
                        for p, indivs in j.items():
                            if not hasattr(goal, p):
                                goal.__setattr__(p, {})
                            for s, objs in indivs.items():
                                goal.__getattribute__(p)[s] = objs
                        arguments.append(goal)
                    except json.JSONDecodeError as e:
                        print(e)
                        arguments.append(ar) # We assume that if it is not JSON, it is a simple string
                agents_task[ag.agent_name].append((task.name, arguments))

    def on_new_request(self, msg: PlanRequest):
        ctrl_agents_task = {}
        unctrl_agents_task = {}
        self.retrieve_agents_task(msg.controllable_agent_tasks, ctrl_agents_task)
        self.retrieve_agents_task(msg.uncontrollable_agent_tasks, unctrl_agents_task)

        if self.user_callback is not None:
            self.user_callback(ctrl_agents_task, unctrl_agents_task)

    def wait_for_request(self):
        rospy.spin()

    def send_plan(self, agentss, ctrlable_name, unctrlable_name):
        print(ctrlable_name)
        print(unctrlable_name)
        existing_edges = set()
        existing_tasks = {}
        msg = Plan()
        msg.tasks = []
        for agents in agentss:
            reconstituted_plan = [None] * (2 * len(agents[ctrlable_name].plan))
            reconstituted_plan[::2] = agents[ctrlable_name].plan
            reconstituted_plan[1::2] = agents[unctrlable_name].plan  # TODO: change it...
            for i, a in enumerate(reconstituted_plan):
                if a.id not in existing_tasks:
                    task = Task()
                    task.id = a.id
                    task.type = task.PRIMITIVE_TASK
                    task.name = a.name
                    task.parameters = a.parameters
                    task.agent = a.agent
                    task.successors = []
                    existing_tasks[a.id] = task
                    msg.tasks.append(task)
                task = existing_tasks[a.id]
                if i < len(reconstituted_plan) - 1:
                    task.successors.append(reconstituted_plan[i+1].id)
                if i > 0:
                    task.predecessors.append(reconstituted_plan[i-1].id)
                why = a.why
                how = a
                while why is not None:
                    if (why.id, how.id) not in existing_edges:
                        if why.id not in existing_tasks:
                            task = Task()
                            task.id = why.id
                            task.name = why.name
                            task.parameters = why.parameters
                            task.agent = how.agent  # TODO: change it...
                            task.successors = []
                            existing_tasks[why.id] = task
                            msg.tasks.append(task)
                        why_task = existing_tasks[why.id]
                        how_task = existing_tasks[how.id]  # this one should exist
                        why_task.decomposed_into.append(how.id)
                        how_task.decomposition_of = why.id
                        how_task.decomposition_number = how.decompo_number
                        existing_edges.append(why.id, how.id)
                        how = why
                        why = why.why
        self.plan_pub.publish(msg)





def start_ros_node(node_name="planner"):
    rospy.init_node("planner")
