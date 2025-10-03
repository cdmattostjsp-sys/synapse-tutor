import pandas as pd

def validate_semantic(document: str) -> pd.DataFrame:
    results = [
        {
            "id": "identificacao",
            "descricao": "Clareza na identificação da unidade e responsável pela pesquisa",
            "presente": "pesquisa" in document.lower() or "responsável" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        },
        {
            "id": "fornecedores",
            "descricao": "Apresentação de cotações de fornecedores distintos",
            "presente": "fornecedor" in document.lower() or "cotação" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        }
    ]
    return pd.DataFrame(results)
