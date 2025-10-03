# knowledge/validators/mapa_riscos_semantic_validator.py
from __future__ import annotations
from typing import List, Dict, Tuple

def semantic_validate_mapa_riscos(doc_text: str, client=None) -> Tuple[float, List[Dict]]:
    """
    Validador semântico para Mapa de Riscos.
    Retorna (score, results), onde:
      - score: média das notas de adequação
      - results: lista com campos: id, descricao, presente, adequacao_nota, justificativa
    """
    results = [
        {
            "id": "identificacao",
            "descricao": "Mapa contém identificação clara dos riscos e responsáveis",
            "presente": "risco" in doc_text.lower(),
            "adequacao_nota": 100 if "risco" in doc_text.lower() else 0,
            "justificativa": "Placeholder – checagem semântica ainda não detalhada."
        },
        {
            "id": "tratamento",
            "descricao": "Indicação de medidas de mitigação ou tratamento",
            "presente": "mitigação" in doc_text.lower() or "tratamento" in doc_text.lower(),
            "adequacao_nota": 100 if ("mitigação" in doc_text.lower() or "tratamento" in doc_text.lower()) else 0,
            "justificativa": "Placeholder – checagem semântica ainda não detalhada."
        }
    ]

    # cálculo do score médio
    notas = [r["adequacao_nota"] for r in results]
    score = round(sum(notas) / len(notas), 1) if notas else 0.0

    return score, results
