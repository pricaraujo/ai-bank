from langchain_core.messages import SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.currency_ops import consultar_cotacao_real
from src.core.state import AgentState
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0, max_retries=0)

PROMPT = "Você é o Agente de Câmbio. Identifique a moeda e use `consultar_cotacao_real`."

def exchange_node(state: AgentState):
    messages = state['messages']
    
    llm_tools = llm.bind_tools([consultar_cotacao_real])
    response = llm_tools.invoke([SystemMessage(content=PROMPT)] + messages)
    
    if response.tool_calls:
        args = response.tool_calls[0]['args']
        res = consultar_cotacao_real(**args)
        content = f"Cotação {res.get('moeda')}: R$ {res.get('valor')}." if res['sucesso'] else res['mensagem']
        return {
            "messages": [AIMessage(content=content)],
            "next_agent": "exchange_wait"
        }
    
    return {
        "messages": [response],
        "next_agent": "exchange_wait"
    }