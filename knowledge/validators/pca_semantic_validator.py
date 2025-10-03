import pandas as pd

def validate_semantic(document: str) -> pd.DataFrame:
    results = [
        {
            "id": "identificacao",
            "descricao": "Identificação do PCA e da unidade responsável",
            "presente": "pca" in document.lower() or "unidade" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        },
        {
            "id": "metas",
            "descricao": "Clareza das metas e objetivos vinculados ao planejamento",
            "presente": "meta" in document.lower() or "objetivo" in document.lower(),
            "adequacao_nota": 100,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        }
    ]
    return pd.DataFrame(results)
