from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send

class SubState(TypedDict):
    val: str
    result: str
    proposals: Annotated[list, operator.add]

def sub_1(state): return {"result": state["val"] + "_1"}
def sub_2(state): return {"result": state["result"] + "_2"}
def sub_3(state): return {"proposals": [state["result"] + "_3"]}

sub = StateGraph(SubState)
sub.add_node("s1", sub_1)
sub.add_node("s2", sub_2)
sub.add_node("s3", sub_3)
sub.add_edge(START, "s1")
sub.add_edge("s1", "s2")
sub.add_edge("s2", "s3")
sub.add_edge("s3", END)
sub_compiled = sub.compile()

class ParentState(TypedDict):
    items: list
    proposals: Annotated[list, operator.add]

def fan_out(state):
    return [Send("sub", {"val": i}) for i in state["items"]]

parent = StateGraph(ParentState)
parent.add_node("sub", sub_compiled)
parent.add_conditional_edges(START, fan_out, ["sub"])
parent.add_edge("sub", END)
app = parent.compile()

for chunk in app.stream({"items": ["a", "b"]}, stream_mode="updates", subgraphs=True):
    print(chunk)
