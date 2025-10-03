# knowledge/validators/edital_semantic_validator.py
# Validador semântico para EDITAL (placeholder)

from __future__ import annotations
from typing import List, Dict, Tuple
import json
import re
import yaml
from pathlib import Path

CHECKLIST_PATH = Path("knowledge/edital_checklist.yml")

def load_checklist_items() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def semantic_validate_edital(doc_text: str, client) -> Tuple[float, List[Dict]]:
    itens = load_checklist_items()
    if not itens:
        return 0.0, []

    # Por ora, placeholder → devolve todos como ausentes
    results: List[Dict] = []
    for i in itens:
        results.append({
            "id": i["id"],
            "descricao": i["descricao"],
            "presente": False,
            "adequacao_nota": 0,
            "justificativa": "Validação semântica para EDITAL ainda não implementada.",
            "faltantes": []
        })

    return 0.0, results
