from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.core.state import AgentState

from src.agents.triage_agent import triage_node
from src.agents.credit_agent import credit_node
from src.agents.interview_agent import interview_node
from src.agents.exchange_agent import exchange_node

def initial_router(state: AgentState):
    route = state.get("next_agent")
    
    if route == "credit_wait": return "credit_agent"
    if route == "exchange_wait": return "exchange_agent"
    if route == "interview_wait": return "interview_agent"
    
    if route == "credit": return "credit_agent"
    if route == "exchange": return "exchange_agent"
    if route == "interview": return "interview_agent"
    
    return "triage_agent"

def router(state: AgentState):
    next_agent = state.get("next_agent")
    
    if "wait" in str(next_agent):
        return END
    
    mapping = {
        "credit": "credit_agent",
        "exchange": "exchange_agent",
        "interview": "interview_agent",
        "triage": "triage_agent",
        "end": END
    }
    return mapping.get(next_agent, END)

# grafo
workflow = StateGraph(AgentState)

workflow.add_node("triage_agent", triage_node)
workflow.add_node("credit_agent", credit_node)
workflow.add_node("exchange_agent", exchange_node)
workflow.add_node("interview_agent", interview_node)

workflow.set_conditional_entry_point(
    initial_router,
    {
        "triage_agent": "triage_agent",
        "credit_agent": "credit_agent",
        "exchange_agent": "exchange_agent",
        "interview_agent": "interview_agent"
    }
)

# arestas
workflow.add_conditional_edges(
    "triage_agent", router, 
    {"credit_agent": "credit_agent", "exchange_agent": "exchange_agent", "interview_agent": "interview_agent", "triage_agent": "triage_agent", END: END}
)

workflow.add_conditional_edges(
    "credit_agent", router,
    {"interview_agent": "interview_agent", "credit_agent": "credit_agent", END: END}
)

workflow.add_conditional_edges(
    "exchange_agent", router,
    {"exchange_agent": "exchange_agent", END: END}
)

workflow.add_conditional_edges(
    "interview_agent", router,
    {"credit_agent": "credit_agent", END: END}
)

memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)