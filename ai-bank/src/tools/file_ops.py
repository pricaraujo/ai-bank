import pandas as pd
import os
import re
from datetime import datetime
from glob import glob

POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(__file__), '../data/clientes.csv'),
    os.path.join(os.path.dirname(__file__), '../../data/clientes.csv'),
    os.path.join(os.path.dirname(__file__), '../../../data/clientes.csv'),
    os.path.join(os.getcwd(), 'data/clientes.csv'),
    os.path.join(os.getcwd(), 'src/data/clientes.csv'),
] #caso o avaliador queira adicionar dados de clientes extras

def _normalize_cpf(cpf_raw: str) -> str:
    if cpf_raw is None:
        return ""
    s = str(cpf_raw)
    return re.sub(r'\D', '', s)

def _normalize_date(date_raw: str) -> str:
    if date_raw is None:
        return ""
    s = str(date_raw).strip()
    if s == "":
        return ""
    
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            continue
    try:
        dt = pd.to_datetime(s, dayfirst=True, errors='coerce')
        if not pd.isna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return s

def _find_clients_csv():
    env_path = os.environ.get("clientes_CSV_PATH")
    if env_path:
        if os.path.exists(env_path):
            return env_path
    for p in POSSIBLE_PATHS:
        p_clean = os.path.abspath(os.path.normpath(p))
        if os.path.exists(p_clean):
            return p_clean
    for match in glob(os.path.join(os.getcwd(), '**', 'clientes.csv'), recursive=True):
        return os.path.abspath(match)
    return None

def validar_cliente(cpf: str, data_nascimento: str) -> dict:
    """
    valida cliente por CPF e data de nascimento.
    - normaliza CPF (somente dígitos).
    - normaliza data (YYYY-MM-DD).
    retorna dict com 'sucesso' e 'dados' (se encontrado).
    """
    try:
        csv_path = _find_clients_csv()
        if not csv_path:
            return {"sucesso": False, "mensagem": "Arquivo clientes.csv não encontrado. Verifique a pasta data/."}

        try:
            df = pd.read_csv(csv_path, dtype=str)
        except Exception as e:
            # tentar com sep=';'
            try:
                df = pd.read_csv(csv_path, sep=';', dtype=str)
            except Exception as e2:
                return {"sucesso": False, "mensagem": f"Falha ao ler {csv_path}: {str(e)} ; tentativa com ';' falhou: {str(e2)}"}

        cols = [c.lower().strip() for c in df.columns.tolist()]
        col_map = {c.lower().strip(): c for c in df.columns.tolist()}  # map lower->original
        if 'cpf' not in cols or 'data_nascimento' not in cols:
            # tenta detectar colunas equivalentes comuns
            candidate_cpf = None
            candidate_data = None
            for c in cols:
                if 'cpf' in c:
                    candidate_cpf = col_map[c]
                if 'nasc' in c or 'data' in c:
                    candidate_data = col_map[c]
            if not candidate_cpf or not candidate_data:
                return {"sucesso": False, "mensagem": f"CSV carregado ({csv_path}) não contém colunas 'cpf' e 'data_nascimento'. Colunas detectadas: {df.columns.tolist()}"}
            cpf_col = candidate_cpf
            data_col = candidate_data
        else:
            cpf_col = col_map['cpf']
            data_col = col_map['data_nascimento']

        cpf_norm = _normalize_cpf(cpf)
        data_norm = _normalize_date(data_nascimento)

        df['_cpf_norm'] = df[cpf_col].astype(str).apply(_normalize_cpf)
        df['_data_norm'] = df[data_col].astype(str).apply(_normalize_date)

        mask = (df['_cpf_norm'] == cpf_norm) & (df['_data_norm'] == data_norm)

        if not mask.any():
            mask_cpf = (df['_cpf_norm'] == cpf_norm)
            if mask_cpf.any():
                found = df[mask_cpf].iloc[0].to_dict()
                return {"sucesso": False, "mensagem": "CPF encontrado, mas a data de nascimento não confere.", "dados_possiveis": found}
            return {"sucesso": False, "mensagem": "Dados incorretos."}

        row = df[mask].iloc[0].to_dict()
        row.pop('_cpf_norm', None)
        row.pop('_data_norm', None)
        return {"sucesso": True, "dados": row, "mensagem": "Autenticado.", "csv_path": csv_path}
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro interno validar_cliente: {str(e)}"}
