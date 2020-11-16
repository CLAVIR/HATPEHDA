import rospy
import json

from planner_msgs.msg import PlanRequest, Plan, AgentTasksRequest, Task

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

    def on_new_request(self, msg: PlanRequest):
        agents_task = {}
        for ag in msg.agent_tasks:
            agents_task[ag.agent_name] = []
            for task in ag.tasks:
                arguments = []
                for ar in task.parameters:
                    try:
                        arguments.append(json.loads(ar))
                    except json.JSONDecodeError:
                        arguments.append(ar) # We assume that if it is not JSON, it is a simple string
                agents_task[ag.agent_name].append((task.name, arguments))
        if self.user_callback is not None:
            self.user_callback(agents_task)

    def wait_for_request(self):
        rospy.spin()

    def send_plan(self, agentss):
        existing_edges = set()
        existing_tasks = {}
        msg = Plan()
        msg.tasks = []
        for agents in agentss:
            reconstituted_plan = [None] * (2 * len(agents["robot"].plan))
            reconstituted_plan[::2] = agents["robot"].plan
            reconstituted_plan[1::2] = agents["human"].plan  # TODO: change it...
            for i, a in enumerate(reconstituted_plan):
                if a.id not in existing_tasks:
                    task = Task()
                    task.id = a.id
                    task.name = a.name
                    task.parameters = a.parameters
                    task.agent = "robot" if i % 2 == 0 else "human"  # TODO: change it...
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
