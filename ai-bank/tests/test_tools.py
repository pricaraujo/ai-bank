import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.score_calculator import calcular_atualizar_score
from src.tools.credit_ops import processar_solicitacao_aumento

class TestBusinessLogic(unittest.TestCase):

    # TESTE 1: CÁLCULO DE SCORE
    @patch('src.tools.score_calculator.pd.read_csv')
    @patch('src.tools.score_calculator.pd.DataFrame.to_csv')
    def test_calculo_score_exato(self, mock_to_csv, mock_read_csv):
        mock_df = pd.DataFrame([{
            'cpf': '12345678900', 'score': 0, 'renda_mensal': 0
        }])
        mock_read_csv.return_value = mock_df

        # Cenário: Renda 15k, Despesas 5k, CLT, 0 Dependentes, Sem Dívidas
        # Fórmula esperada: (15000 / 5001) * 30 = ~90
        # + CLT (300) + 0 Dep (100) + Sem Dívida (100) = ~590
        resultado = calcular_atualizar_score(
            cpf="12345678900",
            renda_mensal=15000,
            tipo_emprego="clt",
            despesas=5000,
            dependentes=0,
            tem_dividas="não"
        )

        self.assertTrue(resultado['sucesso'])
        # Verifica se o score ficou dentro de uma margem aceitável
        self.assertTrue(580 <= resultado['novo_score'] <= 600, f"Score calculado: {resultado['novo_score']}")

    # TESTE 2: REGRA DE CRÉDITO
    @patch('src.tools.credit_ops.pd.read_csv')
    @patch('src.tools.credit_ops.os.path.exists', return_value=True)
    def test_recusa_por_limite(self, mock_exists, mock_read_csv):
        data = {
            'min_score': [0, 300, 500],
            'max_limit': [500, 1000, 3000]
        }
        mock_read_csv.return_value = pd.DataFrame(data)

        # Cenário: Score 200 tenta pedir 1000 (Regra diz que max é 500)
        resultado = processar_solicitacao_aumento(
            cpf="123", 
            limite_atual=100, 
            novo_limite=1000, 
            score_atual=200
        )

        self.assertEqual(resultado['status'], 'rejeitado')
        self.assertEqual(resultado['max_permitido'], 500.0)

    #TESTE 3: REGRA DE CRÉDITO (Aprovação)
    @patch('src.tools.credit_ops.pd.read_csv')
    @patch('src.tools.credit_ops.os.path.exists', return_value=True)
    def test_aprovacao_credito(self, mock_exists, mock_read_csv):
        data = {
            'min_score': [0, 500],
            'max_limit': [500, 5000]
        }
        mock_read_csv.return_value = pd.DataFrame(data)

        # Cenário: Score 600 tenta pedir 4000 (Regra diz que max é 5000)
        resultado = processar_solicitacao_aumento(
            cpf="123", 
            limite_atual=1000, 
            novo_limite=4000, 
            score_atual=600
        )

        self.assertEqual(resultado['status'], 'aprovado')

if __name__ == '__main__':
    unittest.main()