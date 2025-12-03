import pandas as pd
import os
from datetime import datetime
import re

# Caminhos
SCORE_RULES = os.path.join(os.path.dirname(__file__), '../data/score_limit.csv')
LOG_PATH = os.path.join(os.path.dirname(__file__), '../data/limit_increase_request.csv')

def _limpar_valor(valor) -> float:
    """Extrai número float de string ou dict"""
    if isinstance(valor, (int, float)): return float(valor)
    if isinstance(valor, dict): # Caso o Gemini mande {'valor': 5000}
        return _limpar_valor(list(valor.values())[0])
    # Regex para pegar números
    nums = re.findall(r"[\d\.]+", str(valor).replace(',', '.'))
    return float(nums[0]) if nums else 0.0

def processar_solicitacao_aumento(cpf: str, limite_atual: any, novo_limite: any, score_atual: any) -> dict:
    try:
        # 1. Prepara dados numéricos
        score_val = int(_limpar_valor(score_atual))
        novo_limite_val = float(_limpar_valor(novo_limite))
        limite_atual_val = float(_limpar_valor(limite_atual))
        
        # 2. Carrega tabela de regras (Score vs Limite Máximo)
        df_regras = pd.read_csv(SCORE_RULES)
        
        # Filtra qual faixa de score o cliente se encaixa
        # Ex: Se score 450. Regras <= 450: [0, 300]. Pegamos a maior (300).
        regra = df_regras[df_regras['min_score'] <= score_val].sort_values('min_score', ascending=False)
        
        status = 'rejeitado'
        max_permitido = 0.0
        
        if not regra.empty:
            max_permitido = float(regra.iloc[0]['max_limit'])
            
            # A REGRA DE OURO: O pedido deve ser menor ou igual ao teto da faixa
            if novo_limite_val <= max_permitido:
                status = 'aprovado'
        
        # 3. Log de Auditoria (Obrigatório em sistemas bancários)
        nova_solicitacao = {
            'cpf_cliente': str(cpf),
            'data_hora_solicitacao': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'limite_atual': limite_atual_val,
            'novo_limite_solicitado': novo_limite_val,
            'score_no_momento': score_val,
            'status_pedido': status
        }
        
        df_log = pd.DataFrame([nova_solicitacao])
        
        # Escreve no CSV (Cria se não existir, Anexa se existir)
        header = not os.path.exists(LOG_PATH) or os.stat(LOG_PATH).st_size == 0
        df_log.to_csv(LOG_PATH, mode='a', header=header, index=False)
        
        # 4. Retorno para o Agente
        return {
            "sucesso": True, 
            "status": status, 
            "max_permitido": max_permitido,
            "mensagem_tecnica": f"Score {score_val} permite máx {max_permitido}. Solicitado: {novo_limite_val}"
        }

    except Exception as e:
        return {"sucesso": False, "status": "erro", "mensagem": str(e)}