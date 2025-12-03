from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.file_ops import validar_cliente
from src.core.state import AgentState
from dotenv import load_dotenv
import os

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    max_retries=0
)

SYSTEM_PROMPT = """
Você é a Triagem do Banco Ágil.
REGRAS:
1. Responda APENAS o que foi perguntado.
2. Seja breve e profissional.
3. Peça CPF e Data de Nascimento para autenticar.
"""

def triage_node(state: AgentState):
    """
    fluxo do nó
    divisão em 2
    1. roteamento: se já ta logado 
    ---> se a ultima menagem for do sistema, o agente espera a resposta do usuario
    ---> pega por palavra chave
    ---> se não entendeu pergunta de novo 
    2. autenticação
    ----> pega os dados
    ----> chama a llm para verificar
    """
    messages = state["messages"]
    attempts = state.get("auth_attempts", 0)
    authenticated = state.get("authenticated", False)

    if authenticated:
        last_msg = messages[-1]
        
        if isinstance(last_msg, AIMessage):
            return {"next_agent": "end"}

        user_content = last_msg.content.lower()

        if "crédito" in user_content or "credito" in user_content or "limite" in user_content:
            return {
                "messages": [AIMessage(content="Um momento, transferindo para o Crédito.")], 
                "next_agent": "credit"
            }
            
        elif "cotação" in user_content or "cotacao" in user_content or "cambio" in user_content or "dólar" in user_content:
            return {
                "messages": [AIMessage(content="Um momento, chamando o especialista de Câmbio.")], 
                "next_agent": "exchange"
            }
            
        elif "atualização" in user_content or "atualizacao" in user_content or "dados" in user_content or "entrevista" in user_content:
            return {
                "messages": [AIMessage(content="Certo, vamos para a Atualização Cadastral.")], 
                "next_agent": "interview"
            }
            
        else:
            return {
                "messages": [AIMessage(content="Entendido. Você deseja falar sobre **Crédito**, **Câmbio** ou **Atualização Cadastral**?")], 
                "next_agent": "end" 
            }

    if attempts >= 3 and not authenticated:
         return {
            "messages": [AIMessage(content="Número máximo de tentativas excedido. Atendimento encerrado.")], 
            "next_agent": "end"
        }

    llm_tools = llm.bind_tools([validar_cliente])
    response = llm_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + messages)

    if response.tool_calls:
        args = response.tool_calls[0]["args"]
        result = validar_cliente(**args)

        if result["sucesso"]:
            nome = result["dados"]["nome"]
            # SUCESSO!
            return {
                "messages": [AIMessage(content=f"Olá {nome}, autenticado com sucesso! Como posso ajudar hoje? (Crédito, Câmbio ou Atualização)")],
                
                "authenticated": True,
                "cpf": result["dados"]["cpf"],
                "nome": nome,
                "user_data": result["dados"],
                "auth_attempts": 0,
                
                "next_agent": "end" 
            }
        else:
            return {
                "messages": [AIMessage(content="Dados incorretos. Verifique CPF e Data.")],
                "auth_attempts": attempts + 1,
                "next_agent": "end"
            }

    return {"messages": [response], "next_agent": "end"}