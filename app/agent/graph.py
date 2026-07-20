from langgraph.graph import StateGraph, START, END
from app.agent.state import AgentState
from app.agent.nodes import classify_node, enrich_node, assess_node

def build_triage_graph():
    builder = StateGraph(AgentState)
    builder.add_node("enrich", enrich_node)
    builder.add_node("classify", classify_node)
    builder.add_node("assess", assess_node)  # optionnel, mais montré

    builder.add_edge(START, "enrich")
    builder.add_edge("enrich", "classify")
    builder.add_edge("classify", "assess")
    builder.add_edge("assess", END)
    return builder.compile()