# knowledge/validators/mapa_riscos_validator.py
# Validador RÍGIDO para MAPA DE RISCOS
# - Lê o checklist em YAML
# - Para cada item:
#     * se houver campo "padrao", usa regex (mais robusto)
#     * senão, usa uma âncora simples (1ª palavra da descrição)

from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import re
import yaml

CHECKLIST_PATH = Path("knowledge/mapa_riscos_checklist.yml")

def load_checklist() -> List[Dict]:
    data = yaml.safe_load(CHECKLIST_PATH.read_text(encoding="utf-8"))
    return data.get("itens", [])

def _is_present(item: Dict, doc_lower: str) -> bool:
    padrao = item.get("padrao")
    if padrao:
        try:
            rx = re.compile(padrao, flags=re.IGNORECASE | re.DOTALL)
            return bool(rx.search(doc_lower))
        except re.error:
            # Se a regex estiver inválida, cai no fallback por âncora
            pass
    # Fallback simples por âncora (primeira palavra da descrição)
    anchor = item.get("descricao", "").split()[0].lower() if item.get("descricao") else ""
    return bool(anchor) and (anchor in doc_lower)

def rigid_validate_mapa_riscos(doc_text: str) -> Dict:
    itens = load_checklist()
    if not itens:
        return {"score": 0.0, "results": []}

    doc_lower = (doc_text or "").lower()
    results: List[Dict] = []
    obrigatorios = [i for i in itens if i.get("obrigatorio", True)]
    atendidos = 0

    for it in itens:
        presente = _is_present(it, doc_lower)
        if it.get("obrigatorio", True) and presente:
            atendidos += 1

        results.append({
            "id": it.get("id"),
            "descricao": it.get("descricao", ""),
            "obrigatorio": bool(it.get("obrigatorio", True)),
            "presente": presente,
        })

    score = round((atendidos / len(obrigatorios)) * 100, 1) if obrigatorios else 0.0
    return {"score": score, "results": results}
