import requests

def consultar_cotacao_real(moeda_origem: str, moeda_destino: str = 'BRL') -> dict:
    moeda_origem = moeda_origem.upper()
    moeda_destino = moeda_destino.upper()
    par = f"{moeda_origem}-{moeda_destino}"
    try:
        url = f"https://economia.awesomeapi.com.br/last/{par}"
        response = requests.get(url, timeout=5)
        if response.status_code != 200: return {"sucesso": False, "mensagem": "API indisponível."}
        
        dados = response.json()
        chave = f"{moeda_origem}{moeda_destino}"
        if chave in dados:
            return {"sucesso": True, "valor": dados[chave]['bid'], "moeda": dados[chave]['name']}
        return {"sucesso": False, "mensagem": "Moeda não encontrada."}
    except Exception as e:
        return {"sucesso": False, "mensagem": str(e)}