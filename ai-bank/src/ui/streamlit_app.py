import streamlit as st
import uuid
import sys
import os
import re
from dotenv import load_dotenv
load_dotenv()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from src.core.orchestrator import app_graph
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="Banco Ágil", page_icon="🏦")
st.title("Banco Ágil - Atendimento IA")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())

def limpar_texto(texto):
    """
    Remove tags de sistema como [Role Change...], [SISTEMA], etc.
    e remove quebras de linha excessivas no início.
    """
    if not texto: return ""
    texto_limpo = re.sub(r'\[.*?\]', '', texto)
    return texto_limpo.strip()

def process_input(user_input):

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    state_input = {"messages": [HumanMessage(content=user_input)]}
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.chat_message("assistant"):
        with st.spinner("Processando..."):
            # Stream events
            events = app_graph.stream(state_input, config=config)
            
            final_response = ""
            
            for event in events:
                for agent_name, payload in event.items():
                    if isinstance(payload, dict) and "messages" in payload:
                        for msg in payload["messages"]:
                            
                            if not isinstance(msg, AIMessage) or not msg.content:
                                continue
                                
                            texto_tratado = limpar_texto(msg.content)
                            
                            if texto_tratado:
                                final_response = texto_tratado
            
            if final_response:
                st.markdown(final_response)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_response
                })

if len(st.session_state.messages) > 0:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

if prompt := st.chat_input("Digite aqui..."):
    process_input(prompt)