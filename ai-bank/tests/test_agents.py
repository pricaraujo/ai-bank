import unittest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.triage_agent import triage_node
from src.agents.credit_agent import credit_node

class TestAgentFlow(unittest.TestCase):

    # TESTE 1: TRIAGEM
    def test_triage_routing_credito(self):
        state = {
            "messages": [HumanMessage(content="Quero falar sobre crédito")],
            "authenticated": True,
            "auth_attempts": 0
        }

        result = triage_node(state)

        self.assertEqual(result["next_agent"], "credit")

    # TESTE 2: CRÉDITO
    @patch('src.agents.credit_agent.llm')
    @patch('src.agents.credit_agent.processar_solicitacao_aumento')
    def test_credit_direct_command(self, mock_tool, mock_llm):
        # Cenário: Usuário diz "Quero aumentar para 2000"
        # O código deve ignorar o "Quero" (que levaria pra entrevista) e chamar a tool
        
        state = {
            "messages": [HumanMessage(content="Quero aumentar para 2000")],
            "user_data": {"score": 500, "limite_credito": 1000},
            "nome": "Tester"
        }

        mock_tool.return_value = {"status": "aprovado", "max_permitido": 5000}
        
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Resposta simulada"
        
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        result = credit_node(state)

        self.assertNotEqual(result.get("next_agent"), "interview")

    # TESTE 3: CRÉDITO ---> ENTREVISTA
    def test_credit_go_to_interview(self):
        # Cenário: Usuário diz apenas "Sim, quero" (sem números)
        state = {
            "messages": [HumanMessage(content="Sim, quero fazer a entrevista")],
            "user_data": {},
            "nome": "Tester"
        }

        result = credit_node(state)

        self.assertEqual(result["next_agent"], "interview")
        self.assertIn("Transferindo", str(result["messages"][0].content))

if __name__ == '__main__':
    unittest.main()