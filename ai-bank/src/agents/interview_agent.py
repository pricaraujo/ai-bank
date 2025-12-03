from langchain_core.messages import SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.score_calculator import calcular_atualizar_score
from src.core.state import AgentState
from dotenv import load_dotenv

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0, max_retries=0)

PROMPT = """
Você é o Agente de Entrevista. Colete 5 dados: Renda, Emprego, Despesas, Dependentes, Dívidas.
CPF: {cpf}.
Pergunte UM por vez. Só chame a tool no final.
"""

def interview_node(state: AgentState):
    cpf = state.get('cpf')
    messages = state['messages']
    
    llm_tools = llm.bind_tools([calcular_atualizar_score])
    response = llm_tools.invoke([SystemMessage(content=PROMPT.format(cpf=cpf))] + messages)
    
    if response.tool_calls:
        args = response.tool_calls[0]['args']
        # Validação simples
        if len(args) < 5: 
             return {
                "messages": [AIMessage(content="Ainda preciso de mais dados. Continue respondendo...")],
                "next_agent": "interview_wait"
            }
            
        args['cpf'] = cpf
        res = calcular_atualizar_score(**args)
        
        if res['sucesso']:
            user_data = state.get('user_data', {})
            user_data['score'] = res['novo_score']
            return {
                "messages": [AIMessage(content=f"Entrevista finalizada! Novo Score: {res['novo_score']}.")],
                "user_data": user_data,
                "next_agent": "credit"
            }

    return {"messages": [response], "next_agent": "interview_wait"}