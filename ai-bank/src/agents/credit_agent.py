from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools.credit_ops import processar_solicitacao_aumento
from src.core.state import AgentState
from dotenv import load_dotenv
import re

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    max_retries=0
)

PROMPT = """
Você é o Agente de Crédito.
Cliente: {nome}, Score: {score}, Limite: {limite}.
NUNCA use tags como [Role Change].

OBJETIVOS:
1. Se o cliente atualizou o cadastro recentemente, parabenize e sugira tentar o aumento de novo.
2. Aumentar limite (use ferramenta).
3. Consultar limite.
"""

def credit_node(state: AgentState):
    """
    fluxo no nó:
    verifica  aultima mensagem (pode ser do usuário também)
    procura a última mensagem da IA pra saber o contexto da pergunta
    análisa as variáveis de intenção
    entra o agente + dá boas vindas
    só vai para entrevista se NÃO tem número e NÃO é um pedido explícito de aumento
    se tem numero, aumenta limite
    pode vir como retorno da entrevista (análise de novos dados cadastrados)
    atualiza limite
    """
    user_data = state.get('user_data', {})
    messages = state['messages']
    
    last_msg = messages[-1]
    
    last_ai_content = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            last_ai_content = msg.content
            break

    last_human_content = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_content = msg.content.lower()
            break

    disse_sim = "sim" in last_human_content or "quero" in last_human_content or "pode ser" in last_human_content
    tem_numero = bool(re.search(r'\d', last_human_content))
    quer_aumento = "aumentar" in last_human_content or "limite" in last_human_content

    # --- 2. BOAS VINDAS (Vindo da Triagem) ---
    if isinstance(last_msg, AIMessage) and ("um momento" in str(last_msg.content) or "Redirecionando" in str(last_msg.content)):
        limite = user_data.get('limite_credito', 0)
        return {
            "messages": [AIMessage(content=f"Olá! Sou do Crédito. Seu limite atual é R$ {limite}. Gostaria de solicitar um aumento ou apenas consultar?")],
            "next_agent": "credit_wait"
        }
    
    if isinstance(last_msg, AIMessage) and "Entrevista finalizada" in str(last_msg.content):
         return {
            "messages": [AIMessage(content=f"Recebi seus novos dados! Seu score foi atualizado. Qual valor você gostaria de solicitar agora?")],
            "next_agent": "credit_wait"
        }


    if disse_sim and ("novos dados" in last_ai_content or "score foi atualizado" in last_ai_content):
        return {
            "messages": [AIMessage(content="Perfeito! Por favor, digite novamente o **valor** que você deseja (ex: 2000).")],
            "next_agent": "credit_wait"
        }

    if disse_sim and not tem_numero and not quer_aumento:
        return {
            "messages": [AIMessage(content="Certo. Transferindo você para a atualização cadastral...")],
            "next_agent": "interview"
        }

    sys_msg = PROMPT.format(nome=state.get('nome'), score=user_data.get('score', 0), limite=user_data.get('limite_credito', 0))
    llm_tools = llm.bind_tools([processar_solicitacao_aumento])
    response = llm_tools.invoke([SystemMessage(content=sys_msg)] + messages)
    
    if response.tool_calls:
        args = response.tool_calls[0]['args']
        res = processar_solicitacao_aumento(**args)
        
        if res['status'] == 'rejeitado':
            max_val = res.get('max_permitido', 0)
            msg_final = (
                f" **Solicitação Negada.**\n\n"
                f"Com seu Score atual, o limite máximo é **R$ {max_val}**.\n"
                f"O valor pedido é maior que o permitido.\n\n"
                f"💡 **Sugestão:** Podemos tentar aumentar seu Score atualizando seu cadastro. Deseja fazer isso?"
            )
        else:
            msg_final = (
                f"**Aprovado!**\n\n"
                f"Seu novo limite foi confirmado. Teto atual: R$ {res.get('max_permitido', 0)}.\n"
                f"Algo mais?"
            )

        return {
            "messages": [AIMessage(content=msg_final)], 
            "next_agent": "credit_wait"
        }

    return {"messages": [response], "next_agent": "credit_wait"}