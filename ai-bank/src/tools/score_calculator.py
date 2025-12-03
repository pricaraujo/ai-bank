import pandas as pd
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), '../data/clients.csv')

def _limpar_numero(valor) -> float:
    """
    Remove R$, pontos de milhar e converte vírgula decimal para ponto.
    Ex: "R$ 2.500,00" -> 2500.0
    """
    if isinstance(valor, (int, float)):
        return float(valor)
    
    texto = str(valor).lower().replace('r$', '').strip()
    
    if ',' in texto:
        texto = texto.replace('.', '')
        texto = texto.replace(',', '.')

    numeros = re.findall(r"[\d\.]+", texto)
    if numeros:
        try:
            return float(numeros[0])
        except:
            return 0.0
    return 0.0

def calcular_atualizar_score(cpf: str, renda_mensal: any, tipo_emprego: str, despesas: any, dependentes: any, tem_dividas: str) -> dict:
    """
    regras do score pra aumento dependendo dos dados
    """
    try:
        renda_clean = _limpar_numero(renda_mensal)
        despesas_clean = _limpar_numero(despesas)
        
        dep_str = str(dependentes)
        nums = re.findall(r'\d+', dep_str)
        dep_clean = int(nums[0]) if nums else 0

        emp_norm = tipo_emprego.lower().strip()
        div_norm = "sim" if "sim" in str(tem_dividas).lower() else "não"

        PESO_RENDA = 30
        
        PESO_EMPREGO = {
            "formal": 300,
            "clt": 300,
            "autônomo": 200,
            "autonomo": 200,
            "desempregado": 0
        }
        

        if dep_clean == 0: pts_dep = 100
        elif dep_clean == 1: pts_dep = 80
        elif dep_clean == 2: pts_dep = 60
        else: pts_dep = 30 # 3 ou mais
        
        pts_div = -100 if div_norm == "sim" else 100

        # validação de Emprego (se não achar, assume autônomo pra não quebrar, ou retorna erro)
        pts_emp = PESO_EMPREGO.get(emp_norm, 0) 

        fator_financeiro = (renda_clean / (despesas_clean + 1)) * PESO_RENDA
        
        score_bruto = fator_financeiro + pts_emp + pts_dep + pts_div
        
        novo_score = int(max(0, min(1000, score_bruto)))

        df = pd.read_csv(DATA_PATH, dtype={'cpf': str})
        
        cpf_limpo = str(cpf).replace('.', '').replace('-', '').strip()
        mask = df['cpf'] == cpf_limpo
        
        if mask.any():
            df.loc[mask, 'renda_mensal'] = renda_clean
            df.loc[mask, 'tipo_emprego'] = emp_norm
            df.loc[mask, 'despesas'] = despesas_clean
            df.loc[mask, 'dependentes'] = dep_clean
            df.loc[mask, 'tem_dividas'] = div_norm
            df.loc[mask, 'score'] = novo_score
            
            df.to_csv(DATA_PATH, index=False)
            
            return {
                "sucesso": True, 
                "novo_score": novo_score,
                "detalhes": f"Renda:{renda_clean}, Emp:{pts_emp}, Dep:{pts_dep}, Div:{pts_div}"
            }
        
        return {"sucesso": False, "mensagem": "CPF não encontrado na base para atualização."}

    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro de cálculo: {str(e)}"}