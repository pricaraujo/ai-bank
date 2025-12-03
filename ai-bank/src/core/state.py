from typing import TypedDict, Annotated, List, Optional
import operator

# função aux pra garantir que o valor novo sobrescreva o antigo
def overwrite(old, new):
    return new

class AgentState(TypedDict):
    # histórico
    messages: Annotated[List[dict], operator.add]
    
    cpf: Optional[str]
    nome: Optional[str]
    user_data: Optional[dict]
    
    auth_attempts: int
    authenticated: bool
    
    next_agent: Optional[str]