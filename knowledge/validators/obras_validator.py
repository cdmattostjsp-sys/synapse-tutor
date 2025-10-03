# knowledge/validators/obras_validator.py
# Validador rígido para OBRAS

from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import yaml

CHECKLIST_PATH = Path("knowledge/obras_checklist.yml")

def load_checklist() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def rigid_validate_obras(doc_text: str) -> Dict:
    itens = load_checklist()
    if not itens:
        return {"score": 0.0, "results": []}

    doc_lower = doc_text.lower() if doc_text else ""
    results: List[Dict] = []
    obrigatorios = [i for i in itens if i.get("obrigatorio", True)]
    atendidos = 0

    for i in itens:
        termo = i["descricao"].split()[0].lower()
        presente = termo in doc_lower
        if i.get("obrigatorio", True) and presente:
            atendidos += 1

        results.append({
            "id": i["id"],
            "descricao": i["descricao"],
            "obrigatorio": bool(i.get("obrigatorio", True)),
            "presente": presente,
        })

    score = round((atendidos / len(obrigatorios)) * 100, 1) if obrigatorios else 0.0
    return {"score": score, "results": results}
