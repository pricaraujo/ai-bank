from langchain_core.messages import SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.currency_ops import consultar_cotacao_real
from src.core.state import AgentState
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    max_retries=0
)

PROMPT = "Você é o Agente de Câmbio. Identifique a moeda que o usuário quer e use a ferramenta `consultar_cotacao_real`."

def exchange_node(state: AgentState):
    messages = state['messages']
    
    llm_tools = llm.bind_tools([consultar_cotacao_real])
    response = llm_tools.invoke([SystemMessage(content=PROMPT)] + messages)
    
    if response.tool_calls:
        args = response.tool_calls[0]['args']
        res = consultar_cotacao_real(**args)
        
        if res['sucesso']:
            moeda = res.get('moeda', 'Moeda')
            valor_raw = float(res.get('valor', 0))
            
            valor_fmt = f"{valor_raw:.4f}".replace('.', ',')
            
            content = (
                f"**Cotação Atual**\n\n"
                f"Moeda: **{moeda}**\n"
                f"Valor Comercial: **R$ {valor_fmt}**"
            )
        else:
            content = f"Não foi possível realizar a cotação. Motivo: {res.get('mensagem')}"
            
        return {
            "messages": [AIMessage(content=content)],
            "next_agent": "exchange_wait"
        }
    
    return {
        "messages": [response],
        "next_agent": "exchange_wait"
    }