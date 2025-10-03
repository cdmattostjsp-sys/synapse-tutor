# knowledge/validators/fiscalizacao_semantic_validator.py
from __future__ import annotations
from typing import List, Dict, Tuple
import pandas as pd

def semantic_validate_fiscalizacao(doc_text: str, client=None) -> Tuple[float, List[Dict]]:
    """
    Validador semântico para Fiscalização.
    Retorna (score, results), onde:
      - score: média das notas de adequação
      - results: lista com campos: id, descricao, presente, adequacao_nota, justificativa
    """
    results = [
        {
            "id": "identificacao",
            "descricao": "Clareza na identificação da unidade e data de início da fiscalização",
            "presente": "unidade" in doc_text.lower() or "responsável" in doc_text.lower(),
            "adequacao_nota": 100 if ("unidade" in doc_text.lower() or "responsável" in doc_text.lower()) else 0,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        },
        {
            "id": "descricao",
            "descricao": "Clareza dos objetivos e critérios da fiscalização",
            "presente": "objetivo" in doc_text.lower() or "critério" in doc_text.lower(),
            "adequacao_nota": 100 if ("objetivo" in doc_text.lower() or "critério" in doc_text.lower()) else 0,
            "justificativa": "Placeholder – verificação semântica ainda não detalhada."
        }
    ]

    # cálculo do score médio
    notas = [r["adequacao_nota"] for r in results]
    score = round(sum(notas) / len(notas), 1) if notas else 0.0

    return score, results
