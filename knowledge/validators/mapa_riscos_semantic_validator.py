import pandas as pd

def validate_semantic(document: str) -> pd.DataFrame:
    results = [
        {
            "id": "identificacao",
            "descricao": "Clareza na identificação do processo e responsável",
            "presente": "mapa" in document.lower() or "processo" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        },
        {
            "id": "riscos",
            "descricao": "Listagem de riscos e medidas de mitigação",
            "presente": "risco" in document.lower() or "mitigação" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        }
    ]
    return pd.DataFrame(results)
