import pandas as pd

def validate_semantic(document: str) -> pd.DataFrame:
    results = [
        {
            "id": "identificacao",
            "descricao": "Clareza na identificação da unidade e data de início da fiscalização",
            "presente": "unidade" in document.lower() or "responsável" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        },
        {
            "id": "descricao",
            "descricao": "Clareza dos objetivos e critérios da fiscalização",
            "presente": "objetivo" in document.lower() or "critério" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        }
    ]
    return pd.DataFrame(results)
